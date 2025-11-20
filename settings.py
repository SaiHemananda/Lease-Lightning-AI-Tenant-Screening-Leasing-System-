# backend/config/settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

APP_HOST = "0.0.0.0"
APP_PORT = 8000

ALLOWED_ORIGINS = [
    "http://localhost:8501",  # Streamlit
    "http://127.0.0.1:8501",
    "http://localhost:3000",
]
