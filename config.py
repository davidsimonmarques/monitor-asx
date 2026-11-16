import os
from pathlib import Path

# Carregar variáveis de ambiente do .env se existir
BASE_DIR = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# Telegram Secrets
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
DRY_RUN = os.getenv("DRY_RUN", "False").lower() in ("true", "1", "yes")

# Filtros do Veículo
TARGET_MAKE = "Mitsubishi"
TARGET_MODEL = "ASX"
MIN_YEAR = int(os.getenv("MIN_YEAR", 2014))
MAX_PRICE = float(os.getenv("MAX_PRICE", 70000.0))
COUNTEROFFER_MAX_PRICE = float(os.getenv("COUNTEROFFER_MAX_PRICE", 80000.0))

# Termos obrigatórios e eliminatórios
REQUIRED_TRANSMISSION = ["automat", "aut.", "cvt", "aut"]
REQUIRED_LEATHER = ["couro", "banco de couro", "bancos de couro", "bancos em couro", "revestimento em couro"]

ELIMINATORY_KEYWORDS = [
    "leilão",
    "leilao",
    "sinistro",
    "sinistrado",
    "recuperado",
    "recuperada",
    "consta recuperado",
    "passagem por leilão",
    "passagem por leilao",
    "perda total",
    "pt",
    "batido",
    "salvado",
    "remarcado",
]

# Regiões / Cidades Aceitas (Belo Horizonte e Região Metropolitana)
ACCEPTED_LOCATIONS = [
    "belo horizonte",
    "bh",
    "contagem",
    "betim",
    "nova lima",
    "sabará",
    "sabara",
    "santa luzia",
    "ibirité",
    "ibirite",
    "ribeirão das neves",
    "ribeirao das neves",
    "vespasiano",
    "lagoa santa",
    "sete lagoas",
    "brumadinho",
    "sarzedo",
    "mário campos",
    "mario campos",
    "esmeraldas",
    "grande belo horizonte",
    "região metropolitana de belo horizonte",
    "congonhas",
    "ouro preto",
    "itavirito",
    "itaguara",
    "igarape",
    "igarapé",
]

# Lojas Locais Mapeadas
LOCAL_STORES = [
    {"name": "Lokamig Seminovos", "url": "https://www.seminovoslokamig.com.br/"},
    {"name": "Rota 66 BH", "url": "https://www.rota66bh.com.br/"},
    {"name": "Kavak Seminovos", "url": "https://www.kavak.com/br/seminovos"},
    {"name": "Compra e Venda Seu Carro", "url": "https://www.compraevendaseucarro.com.br/Veiculos"},
    {"name": "Carbig Seminovos", "url": "https://carbig.com/seminovos"},
    {"name": "Reicar BH", "url": "https://reicarbh.com.br/Veiculos"},
    {"name": "Tutti Veículos", "url": "https://www.tuttiveiculos.com.br/veiculos"},
    {"name": "Grande BH Veículos", "url": "https://grandebhveiculos.com.br/BuscarVeiculo"},
    {"name": "Portal Auto Shopping", "url": "https://www.portalautoshopping.com.br/buscar?tipoFiltro=1"},
    {"name": "WCar Veículos BH", "url": "https://wcarveiculosbh.com.br/BuscarVeiculo"},
    {"name": "Galaxy Motors MG", "url": "https://galaxymotorsmg.com.br/"},
]

# Armazenamento de anúncios vistos
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
SEEN_ADS_FILE = DATA_DIR / "seen_ads.json"
