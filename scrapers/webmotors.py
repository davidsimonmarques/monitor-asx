import re
import json
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
from config import MIN_YEAR, COUNTEROFFER_MAX_PRICE

logger = logging.getLogger(__name__)


class WebmotorsScraper(BaseScraper):
    name = "Webmotors"

    def search(self) -> List[Dict[str, Any]]:
        """
        Busca Mitsubishi ASX no portal Webmotors para Belo Horizonte e MG.
        Utiliza cabeçalhos móveis para contornar proteções antibot com sucesso.
        """
        logger.info(f"[{self.name}] Iniciando busca de anúncios...")
        search_urls = [
            "https://www.webmotors.com.br/carros/estoque/mitsubishi/asx/de.2014/ate.2026?estadocidade=Minas%20Gerais&precoate=80000",
            "https://www.webmotors.com.br/carros/estoque/mitsubishi/asx/de.2014/ate.2026?cidade=Belo%20Horizonte&estadocidade=Minas%20Gerais",
            "https://www.webmotors.com.br/carros/estoque/mitsubishi/asx",
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9",
        }

        found_ads: List[Dict[str, Any]] = []
        seen_urls = set()

        for search_url in search_urls:
            resp = self.get(search_url, impersonate="safari17_0", headers=headers)
            if not resp or resp.status_code != 200:
                continue

            # Tentar extrair dados do JSON embutido na página (Next.js / Redux State)
            # Webmotors geralmente embute os dados do estoque em tags <script>
            try:
                soup = BeautifulSoup(resp.text, "html.parser")
                for s in soup.find_all("script"):
                    stext = s.string or ""
                    if "SearchResults" in stext or "Vehicles" in stext or "adList" in stext:
                        # Extrair URLs de anúncios com regex
                        matches = re.findall(r'(/comprar/mitsubishi/asx/[^"\',\s]+)', stext)
                        for m in matches:
                            clean_m = m.replace("\\", "")
                            full_url = f"https://www.webmotors.com.br{clean_m}"
                            if full_url in seen_urls:
                                continue
                            seen_urls.add(full_url)
                            found_ads.append({
                                "id": f"wm_{clean_m.split('/')[-1]}",
                                "url": full_url,
                                "title": "Mitsubishi ASX",
                                "price": None,
                                "year": None,
                                "source": "Webmotors",
                                "location": "Belo Horizonte e Região/MG",
                            })
            except Exception as e:
                logger.warning(f"[{self.name}] Falha ao analisar scripts: {e}")

            # Buscar links em tags <a>
            soup = BeautifulSoup(resp.text, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if "/comprar/mitsubishi/asx/" in href or "/detalhes/" in href:
                    full_url = href if href.startswith("http") else f"https://www.webmotors.com.br{href}"
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    card_text = a_tag.get_text(separator=" ", strip=True)
                    price_match = re.search(r'R\$\s*([0-9]{2,3}(?:\.[0-9]{3})*)', card_text)
                    price = float(price_match.group(1).replace(".", "")) if price_match else None

                    year_match = re.search(r'\b(201[4-9]|202[0-6])\b', card_text + " " + href)
                    year = int(year_match.group(1)) if year_match else None

                    found_ads.append({
                        "id": f"wm_{href.split('/')[-1].split('?')[0]}",
                        "url": full_url,
                        "title": f"Mitsubishi ASX {year or ''}",
                        "price": price,
                        "year": year,
                        "source": "Webmotors",
                        "location": "Belo Horizonte e Região/MG",
                        "card_snippet": card_text,
                    })

            if found_ads:
                break

        logger.info(f"[{self.name}] Encontrados {len(found_ads)} anúncios brutos para validação.")
        return found_ads
