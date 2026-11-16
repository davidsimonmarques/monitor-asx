import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
from config import MIN_YEAR, COUNTEROFFER_MAX_PRICE

logger = logging.getLogger(__name__)


class OlxScraper(BaseScraper):
    name = "OLX"

    def search(self) -> List[Dict[str, Any]]:
        """
        Busca Mitsubishi ASX em Belo Horizonte e Região no portal OLX.
        URL com filtros de preço até R$ 80k e ano mínimo.
        """
        logger.info(f"[{self.name}] Iniciando busca de anúncios...")
        search_urls = [
            "https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios/mitsubishi/asx/estado-mg/belo-horizonte-e-regiao?rs=45000&re=80000",
            "https://mg.olx.com.br/belo-horizonte-e-regiao/autos-e-pecas/carros-vans-e-utilitarios/mitsubishi/asx?rs=45000&re=80000",
        ]

        found_ads: List[Dict[str, Any]] = []
        seen_urls = set()

        for search_url in search_urls:
            resp = self.get(search_url)
            if not resp or resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Buscar todos os links para anúncios individuais
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                # URL individual da OLX termina com o ID numérico do anúncio
                if ("/autos-e-pecas/carros-vans-e-utilitarios/" in href or "olx.com.br" in href) and re.search(r'-\d{7,}$', href):
                    full_url = href if href.startswith("http") else f"https://mg.olx.com.br{href}"
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    # Obter dados do card se disponível
                    card_text = a_tag.get_text(separator=" ", strip=True)

                    # Tentar extrair preço do card
                    price_match = re.search(r'R\$\s*([0-9]{2,3}(?:\.[0-9]{3})*)', card_text)
                    price = None
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(".", ""))
                        except ValueError:
                            pass

                    # Tentar extrair ano do card ou URL
                    year = None
                    year_match = re.search(r'\b(201[4-9]|202[0-6])\b', href + " " + card_text)
                    if year_match:
                        year = int(year_match.group(1))

                    # Extrair título ou versão
                    title = a_tag.get("title") or a_tag.get("aria-label") or ""
                    if not title:
                        h2 = a_tag.find(["h2", "h3"])
                        title = h2.get_text(strip=True) if h2 else "Mitsubishi ASX"

                    found_ads.append({
                        "id": href.split("-")[-1].split("?")[0],
                        "url": full_url,
                        "title": title,
                        "price": price,
                        "year": year,
                        "source": "OLX",
                        "location": "Belo Horizonte e Região/MG",
                        "card_snippet": card_text,
                    })

            if found_ads:
                break

        logger.info(f"[{self.name}] Encontrados {len(found_ads)} anúncios brutos para validação.")
        return found_ads
