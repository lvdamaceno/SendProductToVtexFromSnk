import contextvars
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Prefixo das linhas de log (ex.: "[id 656] "); cada thread do sync define o do produto que está processando
contexto_log: contextvars.ContextVar[str] = contextvars.ContextVar("contexto_log", default="")


class _ContextoFilter(logging.Filter):
    def filter(self, record):
        record.contexto = contexto_log.get()
        return True


def _get_log_directory() -> str:
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def _get_log_filename(log_dir: str) -> str:
    today_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(log_dir, f"app-{today_str}.log")


def _build_formatter(env: str) -> logging.Formatter:
    if env == "1":
        log_format = "%(asctime)s - %(levelname)s - %(contexto)s%(message)s"
    else:
        log_format = "%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(contexto)s%(message)s"
    return logging.Formatter(log_format)


def configure_logging(project: str = "default"):
    """
    Configura o sistema de logging com:
    - terminal
    - arquivo rotativo com data
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

    for handler in (stream_handler, file_handler):
        handler.addFilter(_ContextoFilter())

    # Aplica todos os handlers
    logging.basicConfig(
        level=log_level,
        handlers=[stream_handler, file_handler],
        force=True
    )

    logging.debug(f"📄 Logs salvos em: {log_file}")
    logging.debug(f"🔧 Ambiente de execução: APP_ENV={env}")
