import logging
from typing import List, Dict, Any
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DRY_RUN, MAX_PRICE

logger = logging.getLogger(__name__)


def send_telegram_message(message: str, parse_mode: str = "HTML") -> bool:
    """Envia uma mensagem para o chat do Telegram usando a Telegram Bot API."""
    if DRY_RUN or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.info(f"[DRY-RUN / TELEGRAM SIMULADO]\n{message}\n")
        print("\n" + "=" * 50 + " TELEGRAM MESSAGE " + "=" * 50)
        print(message)
        print("=" * 118 + "\n")
        return True

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Mensagem enviada com sucesso ao Telegram.")
            return True
        else:
            logger.error(f"Erro Telegram ({response.status_code}): {response.text}")
            # Tentar enviar sem parse_mode em caso de erro de formatação HTML
            payload.pop("parse_mode", None)
            retry_resp = requests.post(url, json=payload, timeout=10)
            return retry_resp.status_code == 200
    except Exception as e:
        logger.error(f"Falha de conexão com Telegram: {e}")
        return False


def format_ad_message(ad: Dict[str, Any], is_counteroffer: bool = False) -> str:
    """
    Formata um anúncio individual com todas as exigências:
    - Nota Ponderada (0-10)
    - Preço, Km, Ano, Versão, Cor, Bairro
    - Opcionais checados com rigor (Teto solar, Multimídia, Câmera, Sensor, Ar)
    - Vendedor (Loja / Particular [Homem/Mulher])
    - Laudo Cautelar e Histórico de Leilão/Sinistro
    - Link direto individual validado ao vivo
    """
    opts = ad.get("optionals", {})
    sunroof_str = "☀️ <b>Teto Solar Elétrico/Panorâmico:</b> SIM ✅" if opts.get("sunroof") else "▫️ Teto Solar: Não informado / Ausente"
    camera_str = "📷 <b>Câmera de Ré:</b> SIM ✅" if opts.get("rear_camera") else "▫️ Câmera de Ré: Não informada"
    sensor_str = "📡 <b>Sensor de Ré:</b> SIM ✅" if opts.get("parking_sensor") else "▫️ Sensor de Ré: Não informado"
    multimedia_str = "📺 <b>Multimídia:</b> SIM ✅" if opts.get("multimedia") else "▫️ Multimídia: Não informada"
    ac_str = "❄️ <b>Ar-condicionado:</b> SIM ✅" if opts.get("ac") else "▫️ Ar-condicionado: Não informado"
    awd_str = "⛰️ <b>Tração 4x4 AWD:</b> SIM ✅" if opts.get("awd") else ""

    vendor = ad.get("vendor", {})
    vendor_label = vendor.get("label", "Não identificado")

    header_icon = "🎯 <b>[CONTRAPROPOSTA]</b>" if is_counteroffer else "🔥 <b>[NOVA ASX ELEGÍVEL]</b>"

    lines = [
        f"{header_icon} <b>Mitsubishi ASX {ad.get('year')}</b>",
        f"⭐ <b>Nota Ponderada: {ad.get('score', 0):.1f} / 10.0</b>",
        f"<i>{ad.get('score_justification', '')}</i>",
        "",
        f"💰 <b>Preço:</b> R$ {ad.get('price', 0):,.2f}",
        f"🛣️ <b>Quilometragem:</b> {ad.get('km', 0):,} km",
        f"🏷️ <b>Versão:</b> {ad.get('version', '2.0 16V Flex CVT')}",
        f"🎨 <b>Cor:</b> {ad.get('cor', 'Não informada')}",
        f"📍 <b>Localização:</b> {ad.get('bairro', 'BH/Região')} ({ad.get('location', 'MG')})",
        f"⚙️ <b>Câmbio:</b> Automático (CVT) ✅",
        f"💺 <b>Bancos:</b> Couro ✅",
        "",
        "<b>Opcionais Verificados:</b>",
        sunroof_str,
        camera_str,
        sensor_str,
        multimedia_str,
        ac_str,
    ]

    if awd_str:
        lines.append(awd_str)

    lines.extend([
        "",
        f"👤 <b>Vendedor:</b> {vendor_label}",
        f"📋 <b>Laudo Cautelar:</b> {ad.get('laudo_cautelar', 'Não informado no anúncio')}",
        f"🛡️ <b>Histórico:</b> {ad.get('history_status', 'Não informado no anúncio')}",
        f"🏪 <b>Origem:</b> {ad.get('source', 'Portal')}",
        "",
        f"🔗 <b>Link Direto (Validado ao vivo):</b>",
        f"{ad.get('url')}",
    ])

    return "\n".join(lines)


def notify_results(
    new_eligible_ads: List[Dict[str, Any]],
    counteroffer_ads: List[Dict[str, Any]]
) -> None:
    """
    Envia as notificações ao Telegram seguindo as instruções:
    1. Se houver novos elegíveis (<= 70k), envia cada um em destaque.
    2. Se NÃO houver novos elegíveis até 70k, declara isso claramente e lista
       as opções ativas entre 70k e 80k para contraproposta.
    """
    if new_eligible_ads:
        # Enviar cada anúncio novo elegível
        intro = f"🚨 <b>MONITOR MITSUBISHI ASX - BH E REGIÃO</b> 🚨\nForam encontradas <b>{len(new_eligible_ads)}</b> nova(s) unidade(s) elegível(is) abaixo do teto de R$ {MAX_PRICE:,.2f}!\n"
        send_telegram_message(intro)

        for ad in new_eligible_ads:
            msg = format_ad_message(ad, is_counteroffer=False)
            send_telegram_message(msg)

    else:
        # Instrução estrita: "Se não houver novas entradas elegíveis até R$ 70k, declarar isso claramente e mapear unidades ativas entre R$ 70k e R$ 80k para contraproposta."
        msg_lines = [
            "📢 <b>MONITOR MITSUBISHI ASX - BH E REGIÃO</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"ℹ️ <b>Nenhuma nova entrada elegível até R$ {MAX_PRICE:,.2f} encontrada nesta varredura.</b>",
            "Todos os anúncios abaixo desse valor foram desqualificados por filtros eliminatórios (sem couro, câmbio manual, histórico negativo ou já notificados).",
            "",
            "🎯 <b>OPORTUNIDADES PARA CONTRAPROPOSTA (R$ 70k a R$ 80k):</b>",
            "<i>Unidades ativas e validadas ao vivo recomendadas para negociação:</i>",
            "",
        ]

        if not counteroffer_ads:
            msg_lines.append("<i>Nenhuma unidade ativa entre R$ 70k e R$ 80k atendeu a todos os critérios eliminatórios no momento.</i>")
            send_telegram_message("\n".join(msg_lines))
        else:
            # Ordenar contrapropostas pela melhor nota
            sorted_counters = sorted(counteroffer_ads, key=lambda x: x.get("score", 0), reverse=True)
            send_telegram_message("\n".join(msg_lines))

            # Enviar as melhores opções de contraproposta (top 5 para não sobrecarregar)
            for idx, ad in enumerate(sorted_counters[:5], 1):
                msg = f"<b>Opção #{idx} para Contraproposta:</b>\n" + format_ad_message(ad, is_counteroffer=True)
                send_telegram_message(msg)
