import configparser
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from urllib.parse import urlparse


def get_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    base_dir = Path(__file__).parent.parent
    config_path = os.path.join(base_dir, 'utils', 'config.ini')
    config.read(config_path, encoding='utf-8')

    return config

load_dotenv()


def parse_database_url() -> Optional[Dict[str, Any]]:
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        parsed = urlparse(database_url)
        return {
            "host": parsed.hostname,
            "port": parsed.port,
            "user": parsed.username,
            "password": parsed.password,
            "database": parsed.path[1:]
        }
    return None

db_config = parse_database_url()

if db_config:
    POSTGRES_HOST = db_config["host"]
    POSTGRES_PORT = db_config["port"]
    POSTGRES_USER = db_config["user"]
    POSTGRES_PASSWORD = db_config["password"]
    POSTGRES_DB = db_config["database"]
    POSTGRES_SSL = "require"
else:
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
    POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")
    POSTGRES_DB = os.environ.get("POSTGRES_DB", "discharge_summary_app")
    POSTGRES_SSL = os.environ.get("POSTGRES_SSL", None)

GOOGLE_CREDENTIALS_JSON: Optional[str] = os.environ.get("GOOGLE_CREDENTIALS_JSON")
GEMINI_MODEL: Optional[str] = os.environ.get("GEMINI_MODEL")
GEMINI_EVALUATION_MODEL: Optional[str] = os.environ.get("GEMINI_EVALUATION_MODEL")
GEMINI_THINKING_LEVEL: str = os.environ.get("GEMINI_THINKING_LEVEL", "HIGH").upper()
GOOGLE_PROJECT_ID: Optional[str] = os.environ.get("GOOGLE_PROJECT_ID")
GOOGLE_LOCATION: Optional[str] = os.environ.get("GOOGLE_LOCATION")

AWS_ACCESS_KEY_ID: Optional[str] = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY: Optional[str] = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION: Optional[str] = os.environ.get("AWS_REGION")
ANTHROPIC_MODEL: Optional[str] = os.environ.get("ANTHROPIC_MODEL")

CLAUDE_API_KEY: Optional[bool] = True if all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, ANTHROPIC_MODEL]) else None

SELECTED_AI_MODEL: str = os.environ.get("SELECTED_AI_MODEL", "claude")

MAX_INPUT_TOKENS: int = int(os.environ.get("MAX_INPUT_TOKENS", "300000"))
MIN_INPUT_TOKENS: int = int(os.environ.get("MIN_INPUT_TOKENS", "100"))
MAX_TOKEN_THRESHOLD: int = int(os.environ.get("MAX_TOKEN_THRESHOLD", "100000"))
PROMPT_MANAGEMENT: bool = os.environ.get("PROMPT_MANAGEMENT", "False").lower() == "true"

APP_TYPE: str = os.environ.get("APP_TYPE", "default")
