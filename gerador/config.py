# -*- coding: utf-8 -*-
"""Configuração centralizada — credenciais via variáveis de ambiente."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GERADOR_DIR = PROJECT_ROOT / "gerador"
DADOS_DIR = GERADOR_DIR / "dados"
OUTPUT_DIR = GERADOR_DIR / "output"
PRODUTOS_DIR = PROJECT_ROOT / "produtos"
DB_PATH = GERADOR_DIR / "produtos_db.json"


def _load_dotenv():
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


def get_wp_credentials():
    """Retorna (username, password, base_url) do WooCommerce ou None se não configurado."""
    user = os.environ.get("WP_USERNAME", "")
    password = os.environ.get("WP_APP_PASSWORD", "")
    base_url = os.environ.get("WP_BASE_URL", "https://DemoStore.com.br/wp-json/wc/v3")
    if user and password:
        return user, password, base_url.rstrip("/")
    return None


def get_gemini_api_key():
    return os.environ.get("GEMINI_API_KEY", "")


def get_wp_auth_headers():
    creds = get_wp_credentials()
    if not creds:
        return None
    import base64
    user, password, _ = creds
    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {
        "Authorization": f"Basic {auth}",
        "User-Agent": "DemoStore-LPP-Bot/1.0",
        "Content-Type": "application/json",
    }
