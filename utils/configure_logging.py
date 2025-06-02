import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from utils.pg_log_handler import PostgresLogHandler  # ✅ Importa o handler customizado


def _get_log_directory() -> str:
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def _get_log_filename(log_dir: str) -> str:
    today_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(log_dir, f"app-{today_str}.log")


def _build_formatter(env: str) -> logging.Formatter:
    if env == "1":
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
    else:
        log_format = "%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"
    return logging.Formatter(log_format)


def configure_logging(project: str = "default"):
    """
    Configura o sistema de logging com:
    - terminal
    - arquivo rotativo com data
    - envio ao PostgreSQL com nome do projeto
    """
    env = os.getenv("APP_ENV", "0")
    log_dir = _get_log_directory()
    log_file = _get_log_filename(log_dir)
    formatter = _build_formatter(env)
    log_level = logging.INFO if env == "1" else logging.DEBUG

    # Handler de terminal
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Handler de arquivo
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5_000_000, backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Handler de PostgreSQL
    pg_handler = PostgresLogHandler(project)
    pg_handler.setFormatter(formatter)

    # Aplica todos os handlers
    logging.basicConfig(
        level=log_level,
        handlers=[stream_handler, file_handler, pg_handler],
        force=True
    )

    logging.debug(f"📄 Logs salvos em: {log_file}")
    logging.debug(f"📡 Logs também enviados para PostgreSQL com project='{project}'")
    logging.debug(f"🔧 Ambiente de execução: APP_ENV={env}")
