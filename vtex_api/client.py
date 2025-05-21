import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

VTEX_APP_KEY = os.getenv("VTEXAPPKEY")
VTEX_APP_TOKEN = os.getenv("VTEXAPPTOKEN")
VTEX_BASE_URL = os.getenv("VTEX_BASE_URL", "https://casacontente.vtexcommercestable.com.br/api/")

if not VTEX_APP_KEY or not VTEX_APP_TOKEN:
    raise EnvironmentError("❌ VTEXAPPKEY e VTEXAPPTOKEN não foram definidos no .env")

def build_vtex_request(endpoint: str) -> tuple[str, dict]:
    """
    Constrói URL completa + headers de autenticação para chamadas VTEX.

    Args:
        endpoint (str): Caminho do endpoint da API.

    Returns:
        tuple: (URL completa, headers)
    """
    url = f"{VTEX_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-VTEX-API-AppKey": VTEX_APP_KEY,
        "X-VTEX-API-AppToken": VTEX_APP_TOKEN,
    }
    return url, headers


def vtex_request(method: str, endpoint: str, data=None, log_msg=None):
    """
    Realiza requisições HTTP genéricas para a API VTEX com autenticação.

    Args:
        method (str): Método HTTP (GET, POST, PUT, etc).
        endpoint (str): Caminho do endpoint da API.
        data (dict, optional): Payload a ser enviado no corpo da requisição.
        log_msg (str, optional): Mensagem de log.

    Returns:
        dict or None: Resposta em JSON ou None se falhar.
    """
    url, headers = build_vtex_request(endpoint)
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        if log_msg:
            logging.info(log_msg)
        return response.json() if response.content else {}
    except requests.RequestException as e:
        logging.error(f"❌ Erro na requisição VTEX [{method.upper()} {endpoint}]: {e}")
        return None


def vtex_get(endpoint, log_msg=None):
    return vtex_request("GET", endpoint, log_msg=log_msg)

def vtex_put(endpoint, data, log_msg=None):
    return vtex_request("PUT", endpoint, data=data, log_msg=log_msg)

