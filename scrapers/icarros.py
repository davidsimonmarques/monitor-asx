import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper

logger = logging.getLogger(__name__)


class IcarrosScraper(BaseScraper):
    name = "iCarros"

    def search(self) -> List[Dict[str, Any]]:
        """
        Busca Mitsubishi ASX no portal iCarros para Belo Horizonte e MG.
        """
        logger.info(f"[{self.name}] Iniciando busca de anúncios...")
        search_urls = [
            "https://www.icarros.com.br/ache/listaanuncios.jsp?pag=1&ord=1&marca=24&modelo=1883&cidade=Belo%20Horizonte&estado=MG&ano=2014-2026&preco=40000-80000",
            "https://www.icarros.com.br/ache/listaanuncios.jsp?pag=1&ord=1&marca=24&modelo=1883&estado=MG",
            "https://www.icarros.com.br/comprar/belo-horizonte-mg/mitsubishi/asx",
        ]

        found_ads: List[Dict[str, Any]] = []
        seen_urls = set()

        for search_url in search_urls:
            resp = self.get(search_url)
            if not resp or resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if ("/ache/detalhes.jsp" in href or "/comprar/mitsubishi/asx" in href) and "listaanuncios" not in href:
                    full_url = href if href.startswith("http") else f"https://www.icarros.com.br{href}"
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    card_text = a_tag.get_text(separator=" ", strip=True)
                    price_match = re.search(r'R\$\s*([0-9]{2,3}(?:\.[0-9]{3})*)', card_text)
                    price = float(price_match.group(1).replace(".", "")) if price_match else None

                    year_match = re.search(r'\b(201[4-9]|202[0-6])\b', card_text + " " + href)
                    year = int(year_match.group(1)) if year_match else None

                    id_match = re.search(r'id=(\d+)', href)
                    ad_id = id_match.group(1) if id_match else href.split("/")[-1].split("?")[0]

                    found_ads.append({
                        "id": f"icarros_{ad_id}",
                        "url": full_url,
                        "title": f"Mitsubishi ASX {year or ''}",
                        "price": price,
                        "year": year,
                        "source": "iCarros",
                        "location": "Belo Horizonte / MG",
                        "card_snippet": card_text,
                    })

            if found_ads:
                break

        logger.info(f"[{self.name}] Encontrados {len(found_ads)} anúncios brutos para validação.")
        return found_ads
