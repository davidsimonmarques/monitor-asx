import logging
from typing import List, Dict, Any, Optional

try:
    from curl_cffi import requests
except ImportError:
    import requests

logger = logging.getLogger(__name__)


class BaseScraper:
    name: str = "Base"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def get(self, url: str, impersonate: str = "chrome124", headers: Optional[Dict[str, str]] = None) -> Optional[Any]:
        """Faz requisição GET protegida com impersonate de navegador real quando disponível."""
        default_headers = {
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }
        if headers:
            default_headers.update(headers)

        try:
            if hasattr(requests, "Session") and "curl_cffi" in requests.__name__:
                resp = requests.get(
                    url,
                    impersonate=impersonate,
                    headers=default_headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                )
            else:
                resp = requests.get(
                    url,
                    headers=default_headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                )
            return resp
        except Exception as e:
            logger.warning(f"[{self.name}] Falha ao requisitar {url}: {e}")
            try:
                if hasattr(requests, "Session") and "curl_cffi" in requests.__name__:
                    return requests.get(
                        url,
                        impersonate="safari17_0",
                        headers=default_headers,
                        timeout=self.timeout,
                        allow_redirects=True,
                    )
                else:
                    return requests.get(
                        url,
                        headers=default_headers,
                        timeout=self.timeout,
                        allow_redirects=True,
                    )
            except Exception as e2:
                logger.error(f"[{self.name}] Fallback também falhou para {url}: {e2}")
                return None

    def search(self) -> List[Dict[str, Any]]:
        """Método principal a ser implementado por cada scraper."""
        raise NotImplementedError
