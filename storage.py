import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from config import SEEN_ADS_FILE

logger = logging.getLogger(__name__)


def load_seen_ads() -> Dict[str, Any]:
    """Carrega os anúncios previamente registrados do arquivo JSON."""
    if not SEEN_ADS_FILE.exists():
        return {}
    try:
        with open(SEEN_ADS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao ler {SEEN_ADS_FILE}: {e}")
        return {}


def is_ad_seen(ad_id_or_url: str) -> bool:
    """Verifica se o anúncio já foi visto e registrado."""
    seen = load_seen_ads()
    return ad_id_or_url in seen


def record_ad(ad: Dict[str, Any]) -> None:
    """Registra um anúncio como visto com timestamp e metadados."""
    seen = load_seen_ads()
    ad_key = ad.get("id") or ad.get("url")
    if not ad_key:
        return

    seen[ad_key] = {
        "id": ad_key,
        "url": ad.get("url"),
        "title": ad.get("title"),
        "price": ad.get("price"),
        "year": ad.get("year"),
        "km": ad.get("km"),
        "score": ad.get("score"),
        "is_eligible": ad.get("is_eligible", False),
        "source": ad.get("source"),
        "first_seen_at": seen.get(ad_key, {}).get("first_seen_at", datetime.now().isoformat()),
        "last_seen_at": datetime.now().isoformat(),
    }

    try:
        with open(SEEN_ADS_FILE, "w", encoding="utf-8") as f:
            json.dump(seen, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar {SEEN_ADS_FILE}: {e}")


def filter_new_ads(ads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtra apenas os anúncios que ainda não foram registrados anteriormente."""
    seen = load_seen_ads()
    new_ads = []
    for ad in ads:
        ad_key = ad.get("id") or ad.get("url")
        if ad_key and ad_key not in seen:
            new_ads.append(ad)
    return new_ads
