from .base import BaseScraper
from .olx import OlxScraper
from .seminovosbh import SeminovosBhScraper
from .mercadolivre import MercadoLivreScraper
from .webmotors import WebmotorsScraper
from .icarros import IcarrosScraper
from .mobiauto import MobiautoScraper
from .local_dealers import LocalDealersScraper

__all__ = [
    "BaseScraper",
    "OlxScraper",
    "SeminovosBhScraper",
    "MercadoLivreScraper",
    "WebmotorsScraper",
    "IcarrosScraper",
    "MobiautoScraper",
    "LocalDealersScraper",
]
