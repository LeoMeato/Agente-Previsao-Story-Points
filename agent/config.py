import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega arquivo .env se existir na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "tawos.db"))
DEFAULT_PROJECT_KEY = os.getenv("DEFAULT_PROJECT_KEY", "MESOS")

# Parâmetros de inferência
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
