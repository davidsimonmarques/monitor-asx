import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
from config import MIN_YEAR, COUNTEROFFER_MAX_PRICE

logger = logging.getLogger(__name__)


class MercadoLivreScraper(BaseScraper):
    name = "Mercado Livre"

    def search(self) -> List[Dict[str, Any]]:
        """
        Busca Mitsubishi ASX no Mercado Livre para Belo Horizonte e Minas Gerais.
        """
        logger.info(f"[{self.name}] Iniciando busca de anúncios...")
        search_urls = [
            "https://lista.mercadolivre.com.br/veiculos/carros-caminhonetes/mitsubishi/asx/belo-horizonte-minas-gerais/desde-2014_PriceRange_45000-80000",
            "https://lista.mercadolivre.com.br/veiculos/carros-caminhonetes/mitsubishi/asx/minas-gerais/desde-2014_PriceRange_45000-80000",
            "https://lista.mercadolivre.com.br/mitsubishi-asx-minas-gerais",
        ]

        found_ads: List[Dict[str, Any]] = []
        seen_urls = set()

        for search_url in search_urls:
            resp = self.get(search_url)
            if not resp or resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Links para anúncios no Mercado Livre
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if ("carro.mercadolivre.com.br/MLB" in href or "veiculo.mercadolivre.com.br/MLB" in href or "/MLB-" in href) and "click1" not in href:
                    clean_url = href.split("?")[0].split("#")[0]
                    if clean_url in seen_urls:
                        continue
                    seen_urls.add(clean_url)

                    card_text = a_tag.get_text(separator=" ", strip=True)
                    price_match = re.search(r'R\$\s*([0-9]{2,3}(?:\.[0-9]{3})*)', card_text)
                    price = None
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(".", ""))
                        except ValueError:
                            pass

                    year_match = re.search(r'\b(201[4-9]|202[0-6])\b', card_text + " " + clean_url)
                    year = int(year_match.group(1)) if year_match else None

                    mlb_id_match = re.search(r'MLB-?(\d+)', clean_url)
                    ad_id = mlb_id_match.group(1) if mlb_id_match else clean_url

                    found_ads.append({
                        "id": f"ml_{ad_id}",
                        "url": clean_url,
                        "title": f"Mitsubishi ASX {year or ''}",
                        "price": price,
                        "year": year,
                        "source": "Mercado Livre",
                        "location": "Belo Horizonte / MG",
                        "card_snippet": card_text,
                    })

            if found_ads:
                break

        logger.info(f"[{self.name}] Encontrados {len(found_ads)} anúncios brutos para validação.")
        return found_ads
