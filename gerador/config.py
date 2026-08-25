# -*- coding: utf-8 -*-
"""
Configuração centralizada — credenciais via variáveis de ambiente.

Suporta dois provedores de IA:
  - Google Gemini  → defina GEMINI_API_KEY no .env
  - Anthropic Claude → defina ANTHROPIC_API_KEY e AI_PROVIDER=claude no .env

Se ambas as chaves estiverem definidas, a variável AI_PROVIDER decide qual usar.
Padrão: gemini
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GERADOR_DIR  = PROJECT_ROOT / "gerador"
DADOS_DIR    = GERADOR_DIR  / "dados"
OUTPUT_DIR   = GERADOR_DIR  / "output"
DB_PATH      = GERADOR_DIR  / "produtos_db.json"


# ---------------------------------------------------------------------------
# Carrega .env automaticamente (sem dependência externa)
# ---------------------------------------------------------------------------

def _load_dotenv():
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key   = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


# ---------------------------------------------------------------------------
# WordPress / WooCommerce
# ---------------------------------------------------------------------------

def get_wp_credentials():
    """Retorna (username, password, base_url) ou None se não configurado."""
    user     = os.environ.get("WP_USERNAME", "")
    password = os.environ.get("WP_APP_PASSWORD", "")
    base_url = os.environ.get("WP_BASE_URL", "https://seu-site.com/wp-json/wc/v3")
    if user and password:
        return user, password, base_url.rstrip("/")
    return None


def get_wp_auth_headers():
    creds = get_wp_credentials()
    if not creds:
        return None
    import base64
    user, password, _ = creds
    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {
        "Authorization": f"Basic {auth}",
        "Content-Type":  "application/json",
    }


# ---------------------------------------------------------------------------
# IA — Gemini ou Claude
# ---------------------------------------------------------------------------

def get_ai_provider() -> str:
    """
    Retorna o provedor de IA ativo: 'gemini' ou 'claude'.
    Lógica de decisão:
      1. Se AI_PROVIDER estiver definido no .env, usa esse valor.
      2. Se só ANTHROPIC_API_KEY estiver definida, usa 'claude'.
      3. Padrão: 'gemini'.
    """
    explicit = os.environ.get("AI_PROVIDER", "").strip().lower()
    if explicit in ("gemini", "claude"):
        return explicit

    has_gemini = bool(os.environ.get("GEMINI_API_KEY", ""))
    has_claude = bool(os.environ.get("ANTHROPIC_API_KEY", ""))

    if has_claude and not has_gemini:
        return "claude"
    return "gemini"


def get_gemini_api_key() -> str:
    return os.environ.get("GEMINI_API_KEY", "")


def get_claude_api_key() -> str:
    return os.environ.get("ANTHROPIC_API_KEY", "")


def get_ai_client():
    """
    Retorna um cliente de IA pronto para uso.

    Para Gemini:  retorna o módulo `google.generativeai` já configurado.
    Para Claude:  retorna o cliente `anthropic.Anthropic`.

    Exemplo de uso:
        provider, client = get_ai_client()
        if provider == "gemini":
            model = client.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content("Seu prompt aqui")
            text = response.text
        elif provider == "claude":
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": "Seu prompt aqui"}]
            )
            text = response.content[0].text
    """
    provider = get_ai_provider()

    if provider == "claude":
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "Biblioteca 'anthropic' não encontrada.\n"
                "Instale com: pip install anthropic"
            )
        api_key = get_claude_api_key()
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY não definida no .env.\n"
                "Adicione: ANTHROPIC_API_KEY=sua_chave_aqui"
            )
        return "claude", anthropic.Anthropic(api_key=api_key)

    else:  # gemini (padrão)
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "Biblioteca 'google-generativeai' não encontrada.\n"
                "Instale com: pip install google-generativeai"
            )
        api_key = get_gemini_api_key()
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY não definida no .env.\n"
                "Adicione: GEMINI_API_KEY=sua_chave_aqui"
            )
        genai.configure(api_key=api_key)
        return "gemini", genai
