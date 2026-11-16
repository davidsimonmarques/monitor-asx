import re
import logging
from typing import Optional, Dict, Any, Tuple

try:
    from curl_cffi import requests
except ImportError:
    import requests

from bs4 import BeautifulSoup
from config import (
    MIN_YEAR,
    MAX_PRICE,
    COUNTEROFFER_MAX_PRICE,
    REQUIRED_TRANSMISSION,
    REQUIRED_LEATHER,
    ACCEPTED_LOCATIONS,
)
from scoring import (
    identify_vendor,
    extract_laudo_cautelar,
    extract_history_status,
    evaluate_optionals,
    calculate_score,
)

logger = logging.getLogger(__name__)

INACTIVE_PATTERNS = [
    "anúncio finalizado",
    "anúncio desativado",
    "anúncio pausado",
    "este anúncio foi desativado",
    "este anúncio não está mais disponível",
    "veículo indisponível",
    "veículo vendido",
    "anúncio expirado",
    "página não encontrada",
    "ops! parece que este anúncio não existe",
    "não encontramos o anúncio",
]


def fetch_live_page(url: str, timeout: int = 15) -> Optional[Tuple[int, str, str]]:
    """
    Acessa a página individual ao vivo com headers de navegador real.
    Retorna (status_code, final_url, html_content) ou None se falhar.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
        "Referer": "https://www.google.com.br/",
    }

    try:
        # Se for curl_cffi, usar impersonate
        if hasattr(requests, "Session") and "curl_cffi" in requests.__name__:
            r = requests.get(
                url,
                impersonate="chrome124",
                timeout=timeout,
                headers=headers,
                allow_redirects=True,
            )
        else:
            r = requests.get(
                url,
                timeout=timeout,
                headers=headers,
                allow_redirects=True,
            )
        return r.status_code, str(r.url), r.text
    except Exception as e:
        logger.warning(f"Erro ao acessar {url}: {e}")
        try:
            if hasattr(requests, "Session") and "curl_cffi" in requests.__name__:
                r = requests.get(
                    url,
                    impersonate="safari17_0",
                    timeout=timeout,
                    headers={"Accept-Language": "pt-BR,pt;q=0.9"},
                    allow_redirects=True,
                )
            else:
                r = requests.get(
                    url,
                    timeout=timeout,
                    headers=headers,
                    allow_redirects=True,
                )
            return r.status_code, str(r.url), r.text
        except Exception as e2:
            logger.error(f"Fallback também falhou para {url}: {e2}")
            return None


def extract_price_from_text(text: str) -> Optional[float]:
    """
    Extrai o valor numérico em reais de textos como 'R$ 68.900,00' ou '68900'.
    """
    match = re.search(r'R\$\s*([0-9]{2,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)', text, re.IGNORECASE)
    if match:
        raw_val = match.group(1).replace(".", "").replace(",", ".")
        try:
            return float(raw_val)
        except ValueError:
            pass

    # Procurar formato direto 70000 ou 68.900
    match2 = re.search(r'\b([4-9][0-9]\.[0-9]{3})\b', text)
    if match2:
        try:
            return float(match2.group(1).replace(".", ""))
        except ValueError:
            pass
    return None


def extract_km_from_text(text: str) -> int:
    """
    Extrai a quilometragem de textos como '112.000 km' ou '98000'.
    """
    match = re.search(r'([0-9]{1,3}(?:\.[0-9]{3})+)\s*km', text, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1).replace(".", ""))
        except ValueError:
            pass

    match2 = re.search(r'\b([3-9][0-9]{4}|1[0-9]{5}|2[0-9]{5})\s*km\b', text, re.IGNORECASE)
    if match2:
        try:
            return int(match2.group(1))
        except ValueError:
            pass
    return 115000  # Km média estimada se não constar


def extract_year_from_text(text: str) -> Optional[int]:
    """
    Extrai o ano/modelo do veículo (ex: 2014, 2015/2015, 14/15).
    """
    match = re.search(r'\b(201[4-9]|202[0-6])\b', text)
    if match:
        return int(match.group(1))

    match2 = re.search(r'\b(1[4-9]|2[0-6])/(1[4-9]|2[0-6])\b', text)
    if match2:
        return 2000 + int(match2.group(2))
    return None


def validate_ad_live(ad: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Executa a validação individual ao vivo obrigatória do anúncio.
    Confirma:
    1. Anúncio ativo e acessível.
    2. Câmbio automático.
    3. Bancos de couro obrigatórios.
    4. Sem histórico de leilão/sinistro.
    5. Ano >= 2014.
    6. Preço dentro do teto (elegível <= 70k ou contraproposta <= 80k).
    7. Localização (Belo Horizonte e Região).
    """
    url = ad.get("url")
    if not url:
        return None

    fetch_res = fetch_live_page(url)
    if not fetch_res:
        logger.info(f"[DESCARTE - Conexão] Não foi possível carregar: {url}")
        return None

    status_code, final_url, html = fetch_res
    if status_code != 200:
        logger.info(f"[DESCARTE - Status {status_code}] Anúncio fora do ar: {url}")
        return None

    # Verificar redirecionamentos que indicam anúncio expirado
    if "busca" in final_url and "busca" not in url:
        logger.info(f"[DESCARTE - Redirecionamento] Redirecionou para página de busca: {url}")
        return None

    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(separator=" ", strip=True)
    lower_page = page_text.lower()

    # 1. Checagem de anúncio inativo/vendido
    for marker in INACTIVE_PATTERNS:
        if marker in lower_page:
            logger.info(f"[DESCARTE - Inativo] Marcador '{marker}' detectado em: {url}")
            return None

    # 2. Confirmação do Modelo ASX
    if "asx" not in lower_page and "asx" not in ad.get("title", "").lower():
        logger.info(f"[DESCARTE - Modelo] Não é ASX: {url}")
        return None

    # 3. Filtro de Câmbio: Automático Obrigatório
    has_auto = any(k in lower_page for k in REQUIRED_TRANSMISSION) or any(
        k in ad.get("transmission", "").lower() for k in REQUIRED_TRANSMISSION
    )
    is_manual = "manual" in ad.get("transmission", "").lower() or (
        "câmbio: manual" in lower_page or "cambio: manual" in lower_page
    )
    if not has_auto or is_manual:
        logger.info(f"[DESCARTE - Câmbio] Não é automático: {url}")
        return None

    # 4. Filtro de Bancos de Couro: Obrigatório
    has_leather = any(k in lower_page for k in REQUIRED_LEATHER) or any(
        k in ad.get("description", "").lower() for k in REQUIRED_LEATHER
    )
    if not has_leather:
        logger.info(f"[DESCARTE - Couro] Bancos de couro ausentes ou não informados: {url}")
        return None

    # 5. Filtro de Histórico: Descartar Leilão/Sinistro/Recuperado
    is_disqualified, hist_status = extract_history_status(page_text)
    if is_disqualified:
        logger.info(f"[DESCARTE - Histórico] {hist_status}: {url}")
        return None

    # 6. Ano >= 2014
    year = ad.get("year")
    if not year:
        year = extract_year_from_text(page_text) or extract_year_from_text(ad.get("title", ""))
    if not year or year < MIN_YEAR:
        logger.info(f"[DESCARTE - Ano] Ano ({year}) menor que {MIN_YEAR}: {url}")
        return None

    # 7. Preço (Extraído da página ao vivo se possível)
    price = ad.get("price")
    page_price = extract_price_from_text(page_text[:3000])  # Buscar no topo da página
    if page_price and 30000 < page_price < 200000:
        price = page_price
    if not price:
        price = extract_price_from_text(ad.get("title", ""))

    if not price or price > COUNTEROFFER_MAX_PRICE:
        logger.info(f"[DESCARTE - Preço] Preço R$ {price} acima de R$ {COUNTEROFFER_MAX_PRICE}: {url}")
        return None

    # 8. Localização: Belo Horizonte e Região
    loc_text = f"{ad.get('location', '')} {ad.get('bairro', '')} {page_text[:2500]}".lower()
    is_bh_region = any(c in loc_text for c in ACCEPTED_LOCATIONS)
    if not is_bh_region and "mg" not in loc_text:
        logger.info(f"[DESCARTE - Região] Fora da Grande BH: {url}")
        return None

    # Extrações detalhadas para enriquecer o anúncio
    km = ad.get("km")
    if not km:
        km = extract_km_from_text(page_text)

    # Identificação do Vendedor e Gênero
    seller_name = ad.get("seller_name", "")
    if not seller_name:
        seller_match = re.search(r'vendedor:?\s*([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)?)', page_text, re.IGNORECASE)
        if seller_match:
            seller_name = seller_match.group(1).strip()
    seller_type_hint = ad.get("seller_type", "")
    vendor_info = identify_vendor(seller_name, seller_type_hint, page_text[:2000])

    # Status do Laudo Cautelar
    laudo_status = extract_laudo_cautelar(page_text)

    # Opcionais reais
    optionals = evaluate_optionals(page_text)

    # Nota Ponderada (0 a 10)
    score, score_justification = calculate_score(
        price=price,
        km=km,
        year=year,
        optionals=optionals,
        laudo_status=laudo_status,
        vendor_info=vendor_info,
    )

    # Classificação: Elegível (<= 70k) ou Contraproposta (70k a 80k)
    is_eligible = price <= MAX_PRICE

    # Versão, cor e bairro
    version = ad.get("version") or "2.0 16V Flex CVT"
    cor = ad.get("cor") or "Não informada"
    bairro = ad.get("bairro") or "Grande BH"

    # Criar objeto validado
    validated_ad = {
        "id": ad.get("id") or url,
        "url": url,
        "title": ad.get("title", f"Mitsubishi ASX {year}"),
        "version": version,
        "year": year,
        "price": price,
        "km": km,
        "cor": cor,
        "bairro": bairro,
        "location": ad.get("location", "Belo Horizonte e Região/MG"),
        "source": ad.get("source", "Portal"),
        "transmission": "Automático (CVT)",
        "leather_seats": True,
        "history_status": hist_status,
        "laudo_cautelar": laudo_status,
        "vendor": vendor_info,
        "optionals": optionals,
        "score": score,
        "score_justification": score_justification,
        "is_eligible": is_eligible,
        "status": "VALIDADO_AO_VIVO",
    }

    return validated_ad
