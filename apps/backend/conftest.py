import os
from pathlib import Path

from dotenv import load_dotenv

# Charge le .env à la racine du monorepo si présent
ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# Option: valeurs par défaut utiles aux tests
os.environ.setdefault("NC_SUMMARY_LANGUAGE", "fr")
