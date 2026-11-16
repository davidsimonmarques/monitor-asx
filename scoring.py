import re
from typing import Dict, Any, Tuple

# Dicionários de nomes comuns brasileiros para inferência de gênero do vendedor particular
MALE_NAMES = {
    "carlos", "joao", "joão", "pedro", "lucas", "marcelo", "paulo", "marcos", "mateus", "matheus",
    "gabriel", "felipe", "rodrigo", "andre", "andré", "guilherme", "bruno", "gustavo", "victor", "vitor",
    "leonardo", "diego", "rafael", "thiago", "tiago", "fernando", "eduardo", "alexandre", "caio", "daniel",
    "renato", "ricardo", "sergio", "sérgio", "fabio", "fábio", "marcio", "márcio", "luiz", "luís",
    "antonio", "antônio", "jose", "josé", "francisco", "vinicius", "vinícius", "danilo", "igor", "roberto",
    "leandro", "juliano", "adriano", "alan", "allan", "arthur", "artur", "bernardo", "breno", "claudio",
    "cláudio", "davi", "david", "elias", "erico", "érico", "everton", "flavio", "flávio", "gilberto",
    "heitor", "helio", "hélio", "henrique", "hugo", "jorge", "julio", "júlio", "luciano", "mauro",
    "murilo", "nelson", "otavio", "otávio", "raul", "reginaldo", "renan", "rogerio", "rogério", "ronaldo",
    "samuel", "valter", "wagner", "wallace", "william", "wilson", "yuri", "alberto", "alex", "cleber"
}

FEMALE_NAMES = {
    "maria", "ana", "juliana", "camila", "mariana", "patricia", "patrícia", "aline", "amanda", "bruna",
    "carolina", "caroline", "fernanda", "gabriela", "larissa", "leticia", "letícia", "luana", "marina", "natalia",
    "natália", "renata", "vanessa", "bianca", "beatriz", "jessica", "jéssica", "daniela", "debora", "débora",
    "claudia", "cláudia", "cristina", "elaine", "flavia", "flávia", "isabela", "isabella", "jaqueline", "laura",
    "luciana", "monica", "mônica", "paula", "priscila", "raquel", "sabrina", "silvia", "sílvia", "tatiana",
    "thais", "thaís", "valeria", "valéria", "viviane", "adriana", "alessandra", "andreia", "andréia", "barbara",
    "bárbara", "carla", "danielle", "eduarda", "elizabeth", "fatima", "fátima", "giovana", "helena", "ingrid",
    "joana", "karina", "kelly", "livia", "lívia", "lorena", "luiza", "luísa", "marcela", "marta",
    "mayara", "milena", "mirella", "nayara", "paloma", "poliana", "rafaela", "regina", "rosana", "rose",
    "samanta", "sandra", "sheila", "simone", "sueli", "suelen", "talita", "tereza", "vitoria", "vitória"
}

STORE_KEYWORDS = [
    r"\bveículos\b", r"\bveiculos\b", r"\bmotors\b", r"\bauto\b", r"\bautos\b",
    r"\bcar\b", r"\bcars\b", r"\bmultimarcas\b", r"\bltda\b", r"\bconcessionária\b",
    r"\bconcessionaria\b", r"\bcomércio\b", r"\bcomercio\b", r"\bautomóveis\b",
    r"\bautomoveis\b", r"\bseminovos\b", r"\bgarage\b", r"\blocadora\b",
    r"\brepasse\b", r"\bplano profissional\b", r"\bloja\b", r"\brevenda\b",
    r"\bshopping\b"
]


def identify_vendor(vendor_name: str, seller_type_hint: str = "", text_context: str = "") -> Dict[str, str]:
    """
    Identifica se o vendedor é Loja ou Particular.
    Se Particular, infere o gênero (Homem / Mulher / Não identificado).
    """
    cleaned_name = (vendor_name or "").strip()
    full_context = f"{cleaned_name} {seller_type_hint} {text_context}".lower()

    # Checar se é loja usando regex de palavras inteiras
    is_store = False
    if seller_type_hint.lower() in ["dealership", "loja", "revenda", "profissional"]:
        is_store = True
    else:
        for pattern in STORE_KEYWORDS:
            if re.search(pattern, full_context):
                is_store = True
                break

    if is_store:
        return {
            "type": "Loja",
            "name": cleaned_name or "Loja parceira",
            "gender": "N/A",
            "label": f"Loja ({cleaned_name or 'Concessionária/Revenda'})"
        }

    # Se particular, tentar inferir nome e gênero
    first_name = ""
    if cleaned_name:
        parts = re.split(r'[\s\-_/]+', cleaned_name.strip())
        if parts:
            first_name = parts[0].lower()

    gender = "Não identificado"
    if first_name in MALE_NAMES:
        gender = "Homem"
    elif first_name in FEMALE_NAMES:
        gender = "Mulher"
    elif first_name.endswith("o") and len(first_name) > 3 and not first_name.endswith("cao"):
        gender = "Homem"
    elif first_name.endswith("a") and len(first_name) > 3:
        gender = "Mulher"

    label = f"Particular ({gender}{f' - {cleaned_name}' if cleaned_name else ''})"
    return {
        "type": "Particular",
        "name": cleaned_name or "Vendedor particular",
        "gender": gender,
        "label": label
    }


def extract_laudo_cautelar(text: str) -> str:
    """
    Identifica o status do Laudo Cautelar e Perícia.
    """
    txt = text.lower()
    if any(k in txt for k in ["laudo cautelar aprovado", "cautelar 100% aprovada", "cautelar aprovada", "perícia aprovada", "pericia aprovada", "laudo 100%"]):
        return "Aprovado 100% (Sem apontamentos)"
    elif any(k in txt for k in ["cautelar com apontamento", "laudo com apontamento", "apontamento no laudo"]):
        return "Aprovado com apontamento"
    elif any(k in txt for k in ["possui laudo", "tem laudo", "laudo cautelar"]):
        return "Mencionado no anúncio (Verificar relatório)"
    return "Não informado no anúncio"


def extract_history_status(text: str) -> Tuple[bool, str]:
    """
    Verifica se o veículo tem passagem por leilão, sinistro ou recuperação.
    Retorna: (is_disqualified, status_description)
    """
    txt = text.lower()
    
    # Detecção de negação explícita (ex: "Leilão Não", "Sem leilão", "Nunca foi de leilão")
    safe_patterns = [
        "sem leilão", "sem leilao", "não tem leilão", "nao tem leilao",
        "leilão não", "leilao nao", "nunca teve leilão", "nunca teve leilao",
        "sem sinistro", "não tem sinistro", "nao tem sinistro", "sinistros não",
        "sinistro não", "não é leilão", "nao e leilao", "livre de leilão"
    ]
    is_explicitly_clean = any(p in txt for p in safe_patterns)

    # Termos negativos
    bad_patterns = [
        "consta leilão", "consta leilao", "passagem por leilão", "passagem por leilao",
        "veículo de leilão", "veiculo de leilao", "adquirido em leilão", "adquirido em leilao",
        "proveniente de leilão", "proveniente de leilao", "sinistrado", "consta sinistro",
        "recuperado de sinistro", "recuperado no documento", "recuperada", "perda total",
        "pequena monta", "media monta", "média monta", "grande monta"
    ]

    for bad in bad_patterns:
        if bad in txt:
            return True, f"Descartado: Histórico negativo identificado ({bad})"

    if "leilão" in txt or "leilao" in txt:
        if not is_explicitly_clean:
            return True, "Descartado: Menção suspeita de leilão sem confirmação negativa explícita"

    if is_explicitly_clean:
        return False, "Certificado / Sem histórico de leilão ou sinistro"

    return False, "Não informado no anúncio"


import re
import unicodedata
from typing import Dict, Any, Tuple


def remove_accents(text: str) -> str:
    """Remove acentuação para busca resiliente."""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def evaluate_optionals(text: str) -> Dict[str, Any]:
    """
    Avalia a presença real de opcionais na descrição/especificações.
    Checa com rigor: teto solar elétrico/skyview, ar-condicionado, multimídia, câmera de ré e sensor de ré.
    """
    raw_lower = text.lower()
    norm_txt = remove_accents(raw_lower)

    # Teto solar (rigor: panorâmico, skyview ou elétrico)
    has_sunroof = any(k in norm_txt for k in [
        "teto solar", "teto panoramico", "skyview", "sky view", "sunroof"
    ])

    # Ar-condicionado
    has_ac = any(k in norm_txt for k in [
        "ar-condicionado", "ar condicionado", "ar digital", "ar automatico", "ar quente"
    ])

    # Multimídia
    has_multimedia = any(k in norm_txt for k in [
        "multimidia", "central multimidia", "tela touch", "apple carplay", "android auto", "gps", "navegador", "bluetooth"
    ])

    # Câmera de ré
    has_camera = any(k in norm_txt for k in [
        "camera de re", "camera de estacionamento", "camera traseira"
    ])

    # Sensor de estacionamento
    has_sensor = any(k in norm_txt for k in [
        "sensor de estacionamento", "sensor de re", "sensores de estacionamento", "park assist"
    ])

    # Outros opcionais desejáveis na ASX
    has_awd = any(k in norm_txt for k in ["4x4", "awd", "tracao integral", "tracao 4x4"])
    has_paddle = any(k in norm_txt for k in ["paddle shift", "borboleta no volante", "troca de marchas no volante"])
    has_cruise = any(k in norm_txt for k in ["piloto automatico", "cruise control"])
    has_start_stop = any(k in norm_txt for k in ["start stop", "start/stop", "chave presencial", "botao start"])

    return {
        "sunroof": has_sunroof,
        "ac": has_ac,
        "multimedia": has_multimedia,
        "rear_camera": has_camera,
        "parking_sensor": has_sensor,
        "awd": has_awd,
        "paddle_shift": has_paddle,
        "cruise_control": has_cruise,
        "keyless": has_start_stop
    }


def calculate_score(
    price: float,
    km: int,
    year: int,
    optionals: Dict[str, bool],
    laudo_status: str,
    vendor_info: Dict[str, str]
) -> Tuple[float, str]:
    """
    Calcula a Nota Ponderada (0.0 a 10.0) equilibrando Preço, Km, Ano e Opcionais Reais.
    Retorna (score, justificativa).
    """
    score = 0.0
    breakdown = []

    # 1. Preço (até 3.0 pontos)
    if price <= 55000:
        p_pts = 3.0
    elif price <= 60000:
        p_pts = 2.7
    elif price <= 65000:
        p_pts = 2.4
    elif price <= 70000:
        p_pts = 2.0
    elif price <= 75000:
        p_pts = 1.3
    elif price <= 80000:
        p_pts = 0.8
    else:
        p_pts = 0.0
    score += p_pts
    breakdown.append(f"Preço R$ {price:,.2f} (+{p_pts:.1f} pts)")

    # 2. Quilometragem (até 2.5 pontos)
    if km <= 80000:
        k_pts = 2.5
    elif km <= 100000:
        k_pts = 2.2
    elif km <= 120000:
        k_pts = 1.8
    elif km <= 140000:
        k_pts = 1.4
    elif km <= 165000:
        k_pts = 1.0
    else:
        k_pts = 0.5
    score += k_pts
    breakdown.append(f"Km {km:,} km (+{k_pts:.1f} pts)")

    # 3. Ano / Modelo (até 1.5 pontos)
    if year >= 2019:
        y_pts = 1.5
    elif year == 2018:
        y_pts = 1.3
    elif year == 2017:
        y_pts = 1.1
    elif year == 2016:
        y_pts = 0.9
    elif year == 2015:
        y_pts = 0.7
    elif year >= 2014:
        y_pts = 0.5
    else:
        y_pts = 0.2
    score += y_pts
    breakdown.append(f"Ano {year} (+{y_pts:.1f} pts)")

    # 4. Opcionais Reais (até 2.5 pontos)
    opt_pts = 0.0
    opt_details = []
    if optionals.get("sunroof"):
        opt_pts += 0.8  # Teto solar é diferencial de grande valor na ASX
        opt_details.append("Teto Solar (+0.8)")
    if optionals.get("rear_camera"):
        opt_pts += 0.4
        opt_details.append("Câmera Ré (+0.4)")
    if optionals.get("multimedia"):
        opt_pts += 0.4
        opt_details.append("Multimídia (+0.4)")
    if optionals.get("parking_sensor"):
        opt_pts += 0.3
        opt_details.append("Sensor Estac. (+0.3)")
    if optionals.get("ac"):
        opt_pts += 0.2
        opt_details.append("Ar-condicionado (+0.2)")
    if optionals.get("awd"):
        opt_pts += 0.3
        opt_details.append("Tração 4x4 AWD (+0.3)")
    if optionals.get("paddle_shift"):
        opt_pts += 0.1
    
    opt_pts = min(opt_pts, 2.5)
    score += opt_pts
    breakdown.append(f"Opcionais: {', '.join(opt_details) if opt_details else 'Básicos'} (+{opt_pts:.1f} pts)")

    # 5. Laudo Cautelar & Procedência (até 0.5 ponto bônus)
    if "100%" in laudo_status or "Aprovado" in laudo_status:
        score += 0.5
        breakdown.append("Laudo Cautelar Aprovado (+0.5 pt)")

    # Ajuste final
    final_score = round(min(max(score, 0.0), 10.0), 1)
    justification = " | ".join(breakdown)

    return final_score, justification
