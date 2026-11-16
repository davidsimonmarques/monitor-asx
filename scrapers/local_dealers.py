import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
from config import LOCAL_STORES

logger = logging.getLogger(__name__)


class LocalDealersScraper(BaseScraper):
    name = "Lojas Locais BH"

    def __init__(self, timeout: int = 12):
        super().__init__(timeout=timeout)

    def search(self) -> List[Dict[str, Any]]:
        """
        Varre os estoques das 11 lojas e concessionárias locais de BH e região.
        Mapeia se há Mitsubishi ASX disponível em estoque.
        """
        logger.info(f"[{self.name}] Iniciando varredura nas 11 lojas locais de BH...")
        found_ads: List[Dict[str, Any]] = []

        # Padrões de busca específicos para cada loja
        store_queries = [
            {
                "name": "Lokamig Seminovos",
                "urls": [
                    "https://www.seminovoslokamig.com.br/estoque?busca=asx",
                    "https://www.seminovoslokamig.com.br/estoque?marca=mitsubishi",
                    "https://www.seminovoslokamig.com.br/",
                ],
                "base_url": "https://www.seminovoslokamig.com.br",
            },
            {
                "name": "Rota 66 BH",
                "urls": [
                    "https://www.rota66bh.com.br/veiculos?termo=asx",
                    "https://www.rota66bh.com.br/veiculos?marca=mitsubishi",
                    "https://www.rota66bh.com.br/",
                ],
                "base_url": "https://www.rota66bh.com.br",
            },
            {
                "name": "Kavak Seminovos",
                "urls": [
                    "https://www.kavak.com/br/seminovos/mitsubishi/asx",
                    "https://www.kavak.com/br/seminovos?search=asx",
                ],
                "base_url": "https://www.kavak.com",
            },
            {
                "name": "Compra e Venda Seu Carro",
                "urls": [
                    "https://www.compraevendaseucarro.com.br/Veiculos?termo=asx",
                    "https://www.compraevendaseucarro.com.br/Veiculos?marca=mitsubishi",
                    "https://www.compraevendaseucarro.com.br/Veiculos",
                ],
                "base_url": "https://www.compraevendaseucarro.com.br",
            },
            {
                "name": "Carbig Seminovos",
                "urls": [
                    "https://carbig.com/seminovos/mitsubishi/asx",
                    "https://carbig.com/seminovos?busca=asx",
                ],
                "base_url": "https://carbig.com",
            },
            {
                "name": "Reicar BH",
                "urls": [
                    "https://reicarbh.com.br/Veiculos?termo=asx",
                    "https://reicarbh.com.br/Veiculos?tipoveiculo=1&marca=mitsubishi",
                    "https://reicarbh.com.br/Veiculos",
                ],
                "base_url": "https://reicarbh.com.br",
            },
            {
                "name": "Tutti Veículos",
                "urls": [
                    "https://www.tuttiveiculos.com.br/veiculos?brand=Mitsubishi",
                    "https://www.tuttiveiculos.com.br/veiculos?termo=asx",
                    "https://www.tuttiveiculos.com.br/veiculos",
                ],
                "base_url": "https://www.tuttiveiculos.com.br",
            },
            {
                "name": "Grande BH Veículos",
                "urls": [
                    "https://grandebhveiculos.com.br/BuscarVeiculo?termo=asx",
                    "https://grandebhveiculos.com.br/BuscarVeiculo?marca=mitsubishi",
                    "https://grandebhveiculos.com.br/BuscarVeiculo",
                ],
                "base_url": "https://grandebhveiculos.com.br",
            },
            {
                "name": "Portal Auto Shopping",
                "urls": [
                    "https://www.portalautoshopping.com.br/buscar?busca=asx",
                    "https://www.portalautoshopping.com.br/buscar?marca=33&tipoFiltro=1",
                    "https://www.portalautoshopping.com.br/buscar?tipoFiltro=1",
                ],
                "base_url": "https://www.portalautoshopping.com.br",
            },
            {
                "name": "WCar Veículos BH",
                "urls": [
                    "https://wcarveiculosbh.com.br/BuscarVeiculo?termo=asx",
                    "https://wcarveiculosbh.com.br/BuscarVeiculo",
                ],
                "base_url": "https://wcarveiculosbh.com.br",
            },
            {
                "name": "Galaxy Motors MG",
                "urls": [
                    "https://galaxymotorsmg.com.br/?s=asx",
                    "https://galaxymotorsmg.com.br/estoque/?s=asx",
                    "https://galaxymotorsmg.com.br/",
                ],
                "base_url": "https://galaxymotorsmg.com.br",
            },
        ]

        seen_urls = set()

        for store in store_queries:
            store_name = store["name"]
            base_url = store["base_url"]
            store_found = 0

            for url in store["urls"]:
                resp = self.get(url)
                if not resp or resp.status_code != 200:
                    continue

                # Checar se a página sequer menciona ASX
                if "asx" not in resp.text.lower():
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")

                # Procurar links para veículos específicos
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    lower_href = href.lower()
                    card_text = a_tag.get_text(separator=" ", strip=True).lower()

                    if "asx" in lower_href or "asx" in card_text:
                        # Excluir links genéricos de busca
                        if any(k in lower_href for k in ["busca", "marca=", "brand=", "filtro", "page=", "?s="]):
                            continue

                        full_url = href if href.startswith("http") else f"{base_url}{href if href.startswith('/') else '/' + href}"
                        if full_url in seen_urls:
                            continue
                        seen_urls.add(full_url)

                        price_match = re.search(r'r\$\s*([0-9]{2,3}(?:\.[0-9]{3})*)', card_text)
                        price = float(price_match.group(1).replace(".", "")) if price_match else None

                        year_match = re.search(r'\b(201[4-9]|202[0-6])\b', card_text + " " + href)
                        year = int(year_match.group(1)) if year_match else None

                        found_ads.append({
                            "id": f"{store_name.lower().replace(' ', '_')}_{hash(full_url) % 10000000}",
                            "url": full_url,
                            "title": f"Mitsubishi ASX {year or ''} - {store_name}",
                            "price": price,
                            "year": year,
                            "source": store_name,
                            "location": "Belo Horizonte e Região/MG",
                            "seller_name": store_name,
                            "seller_type": "Loja",
                            "card_snippet": card_text,
                        })
                        store_found += 1

                if store_found > 0:
                    break

            logger.info(f"[{self.name}] {store_name}: {store_found} anúncio(s) localizado(s).")

        logger.info(f"[{self.name}] Total de {len(found_ads)} anúncios brutos encontrados nas lojas locais.")
        return found_ads
