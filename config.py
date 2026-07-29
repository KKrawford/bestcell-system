from pathlib import Path

# ---------------- BASE PATH ----------------
BASE_DIR = Path(__file__).resolve().parent

# ---------------- DATABASE ----------------
DB_PATH = BASE_DIR / "bestsystem.db"

# ---------------- PLATFORM TOOLS ----------------
PLATFORM_TOOLS = r"C:\platform-tools"
LAUDOS_DIR = Path(PLATFORM_TOOLS) / "Laudos"
LAUDOS_DIR.mkdir(exist_ok=True)

# ---------------- MODULE PATHS ----------------
VENDAS_DIR = BASE_DIR / "vendas"
ORDEM_SERVICO_DIR = BASE_DIR / "ordem_servico"
ESTOQUE_DIR = BASE_DIR / "estoque"
CATALOGO_DIR = BASE_DIR / "catalogo"

# ---------------- ASSETS ----------------
VENDAS_ASSETS = VENDAS_DIR / "assets"
OS_ASSETS = ORDEM_SERVICO_DIR / "assets"
ESTOQUE_ASSETS = ESTOQUE_DIR / "assets"
CATALOGO_ASSETS = CATALOGO_DIR / "assets"
