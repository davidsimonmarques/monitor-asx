import sys
import logging
from typing import List, Dict, Any
from config import MAX_PRICE, COUNTEROFFER_MAX_PRICE
from scrapers import (
    OlxScraper,
    SeminovosBhScraper,
    MercadoLivreScraper,
    WebmotorsScraper,
    IcarrosScraper,
    MobiautoScraper,
    LocalDealersScraper,
)
from validator import validate_ad_live
from storage import is_ad_seen, record_ad
from notifier import notify_results

# Configuração de Logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("MonitorASX")


def run_pipeline() -> None:
    logger.info("=" * 70)
    logger.info("INICIANDO MONITOR MITSUBISHI ASX - BELO HORIZONTE E REGIÃO")
    logger.info(f"Filtros: Ano >= 2014 | Preço Teto <= R$ {MAX_PRICE:,.2f} | Câmbio Automático | Bancos de Couro")
    logger.info(f"Janela de Contraproposta: R$ {MAX_PRICE:,.2f} a R$ {COUNTEROFFER_MAX_PRICE:,.2f}")
    logger.info("=" * 70)

    # 1. Instanciar scrapers dos Portais e Lojas Locais
    scrapers = [
        SeminovosBhScraper(),
        OlxScraper(),
        MercadoLivreScraper(),
        WebmotorsScraper(),
        IcarrosScraper(),
        MobiautoScraper(),
        LocalDealersScraper(),
    ]

    all_raw_ads: List[Dict[str, Any]] = []

    # 2. Coletar anúncios brutos de todas as fontes
    for scraper in scrapers:
        try:
            logger.info(f"--> Executando scraper: {scraper.name}")
            ads = scraper.search()
            all_raw_ads.extend(ads)
            logger.info(f"--> {scraper.name}: {len(ads)} anúncio(s) coletado(s).")
        except Exception as e:
            logger.error(f"Erro ao executar scraper {scraper.name}: {e}")

    logger.info(f"Total bruto de anúncios coletados: {len(all_raw_ads)}")

    # Deduplicar por URL antes da validação
    unique_candidates: Dict[str, Dict[str, Any]] = {}
    for ad in all_raw_ads:
        url = ad.get("url")
        if url and url not in unique_candidates:
            unique_candidates[url] = ad

    logger.info(f"Total de candidatos únicos para validação ao vivo: {len(unique_candidates)}")

    # 3. VALIDAÇÃO AO VIVO OBRIGATÓRIA (Abre individualmente cada página com concorrência segura)
    logger.info("Iniciando Validação Ao Vivo Obrigatória em cada anúncio...")
    validated_eligible_ads: List[Dict[str, Any]] = []
    validated_counteroffer_ads: List[Dict[str, Any]] = []

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _validate_worker(item):
        idx, (url, raw_ad) = item
        try:
            val = validate_ad_live(raw_ad)
            return idx, val
        except Exception as err:
            logger.warning(f"Erro ao validar {url}: {err}")
            return idx, None

    candidate_items = list(enumerate(unique_candidates.items(), 1))
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(_validate_worker, item): item for item in candidate_items}
        for future in as_completed(futures):
            idx, validated = future.result()
            if not validated:
                continue

            if validated["is_eligible"]:
                validated_eligible_ads.append(validated)
                logger.info(f" -> [{idx}/{len(unique_candidates)}] APROVADO ELEGÍVEL (<= R$ {MAX_PRICE:,.2f}): {validated['title']} - R$ {validated['price']:,.2f} (Nota: {validated['score']})")
            else:
                validated_counteroffer_ads.append(validated)
                logger.info(f" -> [{idx}/{len(unique_candidates)}] APROVADO CONTRAPROPOSTA (70k-80k): {validated['title']} - R$ {validated['price']:,.2f} (Nota: {validated['score']})")

    # 4. Filtrar novos anúncios elegíveis (que ainda não foram notificados)
    new_eligible_ads: List[Dict[str, Any]] = []
    for ad in validated_eligible_ads:
        ad_key = ad.get("id") or ad.get("url")
        if not is_ad_seen(ad_key):
            new_eligible_ads.append(ad)

    logger.info("=" * 70)
    logger.info(f"Novos anúncios elegíveis a notificar: {len(new_eligible_ads)}")
    logger.info(f"Unidades válidas para contraproposta (70k-80k): {len(validated_counteroffer_ads)}")
    logger.info("=" * 70)

    # 5. Enviar Notificações via Telegram
    notify_results(new_eligible_ads, validated_counteroffer_ads)

    # 6. Registrar anúncios como vistos para evitar notificações repetidas futuras
    for ad in validated_eligible_ads:
        record_ad(ad)
    for ad in validated_counteroffer_ads:
        record_ad(ad)

    logger.info("Processamento concluído com sucesso!")


if __name__ == "__main__":
    run_pipeline()
