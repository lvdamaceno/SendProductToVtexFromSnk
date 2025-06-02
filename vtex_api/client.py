import logging
import os
import json
import requests
from dotenv import load_dotenv

from notifications.telegram import enviar_notificacao_telegram

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
    url, headers = build_vtex_request(endpoint)
    try:
        if log_msg:
            logging.info(log_msg)

        logging.debug(f"🔗 URL: {url}")
        logging.debug(f"📨 Método: {method.upper()}")
        logging.debug(f"📦 Payload: {json.dumps(data, indent=2)}")
        logging.debug(f"🧾 Headers: {headers}")

        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=data,
            timeout=30
        )
        logging.debug(f"📥 Status Code: {response.status_code}")
        logging.debug(f"📥 Response Text: {response.text}")

        response.raise_for_status()
        return response.json() if response.content else {}

    except requests.RequestException as e:
        logging.error(f"❌ Erro na requisição VTEX [{method.upper()} {endpoint}]: {e}")
        enviar_notificacao_telegram(f"❌ Erro na requisição VTEX [{method.upper()} {endpoint}]: {e}")
        logging.error(f"❌ Corpo da resposta com erro: {response.text if 'response' in locals() else 'sem resposta'}")
        return None


def vtex_get(endpoint, log_msg=None):
    return vtex_request("GET", endpoint, log_msg=log_msg)

def vtex_post(endpoint, data, log_msg=None):
    return vtex_request("POST", endpoint, data=data, log_msg=log_msg)

def vtex_put(endpoint, data, log_msg=None):
    return vtex_request("PUT", endpoint, data=data, log_msg=log_msg)

