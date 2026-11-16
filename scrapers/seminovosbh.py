import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
from config import MIN_YEAR, COUNTEROFFER_MAX_PRICE

logger = logging.getLogger(__name__)


class SeminovosBhScraper(BaseScraper):
    name = "Seminovos BH"

    def search(self) -> List[Dict[str, Any]]:
        """
        Busca Mitsubishi ASX no portal Seminovos BH (seminovos.com.br).
        """
        logger.info(f"[{self.name}] Iniciando busca de anúncios...")
        search_urls = [
            "https://seminovos.com.br/carros/mitsubishi/asx/ano-2014-2026/preco-40000-80000",
            "https://seminovos.com.br/carros/mitsubishi/asx",
        ]

        found_ads: List[Dict[str, Any]] = []
        seen_urls = set()

        for search_url in search_urls:
            resp = self.get(search_url)
            if not resp or resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Os links para os veículos no Seminovos seguem o padrão /mitsubishi-asx-ano-ano-ID
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if re.search(r'/mitsubishi-asx-\d{4}-\d{4}-\d{6,}', href) or re.search(r'/mitsubishi-asx-[^/]+-\d{6,}', href):
                    full_url = href if href.startswith("http") else f"https://seminovos.com.br{href}"
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    # Extrair ano do link (ex: mitsubishi-asx-2014-2015-4986044)
                    year = None
                    year_match = re.search(r'-(\d{4})-(\d{4})-', href)
                    if year_match:
                        year = int(year_match.group(2))
                    else:
                        single_year = re.search(r'-(\d{4})-', href)
                        if single_year:
                            year = int(single_year.group(1))

                    ad_id = href.split("-")[-1].split("?")[0]
                    card_text = a_tag.get_text(separator=" ", strip=True)

                    price_match = re.search(r'R\$\s*([0-9]{2,3}(?:\.[0-9]{3})*)', card_text)
                    price = None
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(".", ""))
                        except ValueError:
                            pass

                    found_ads.append({
                        "id": f"seminovos_{ad_id}",
                        "url": full_url,
                        "title": f"Mitsubishi ASX {year or ''}",
                        "price": price,
                        "year": year,
                        "source": "Seminovos BH",
                        "location": "Belo Horizonte e Região/MG",
                        "card_snippet": card_text,
                    })

            if found_ads:
                break

        logger.info(f"[{self.name}] Encontrados {len(found_ads)} anúncios brutos para validação.")
        return found_ads
