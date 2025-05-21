import logging
import os
import time
from typing import Optional, Any

import requests
from dotenv import load_dotenv
from requests import RequestException, Timeout

from notifications.telegram import enviar_notificacao_telegram

load_dotenv()

TOKEN = os.getenv("SANKHYA_TOKEN")
APPKEY = os.getenv("SANKHYA_APPKEY")
USERNAME = os.getenv("SANKHYA_USERNAME")
PASSWORD = os.getenv("SANKHYA_PASSWORD")

# ------------------------------------------------------------------------------
# 🔧 Configurações iniciais
# ------------------------------------------------------------------------------


BASE_URL = "https://api.sankhya.com.br/gateway/v1/mge/service.sbr"
HEADERS_BASE = {
    "Content-Type": "application/json"
}


# ------------------------------------------------------------------------------
# 🔐 Cliente Sankhya com autenticação única
# ------------------------------------------------------------------------------

class SankhyaClient:
    def __init__(self):
        self.token = None
        self.headers = None
        self.timeout = 60
        self.base_mge = "https://api.sankhya.com.br/gateway/v1/mge/service.sbr"
        self.base_mgecom = "https://api.sankhya.com.br/gateway/v1/mgecom/service.sbr"
        self._autenticar()

    def _autenticar(self):
        login_url = "https://api.sankhya.com.br/login"
        headers = {
            "token": TOKEN,
            "appkey": APPKEY,
            "username": USERNAME,
            "password": PASSWORD
        }
        try:
            logging.info("🔐 Autenticando na API da Sankhya...")
            resp = requests.post(login_url, headers=headers)
            resp.raise_for_status()
            self.token = resp.json().get("bearerToken")
            if not self.token:
                raise ValueError("Bearer token não encontrado na resposta.")
            self.headers = {**HEADERS_BASE, "Authorization": f"Bearer {self.token}"}
        except requests.RequestException as e:
            logging.error(f"❌ Erro ao autenticar: {e}")
            enviar_notificacao_telegram(f"❌ Não foi possível autenticar na Api do Sankhya")
            raise

    def _build_url(self, service_name: str) -> str:
        if service_name.startswith(("CACSP.", "SelecaoDocumentoSP.")):
            return f"{self.base_mgecom}?serviceName={service_name}&outputType=json"
        else:
            return f"{self.base_mge}?serviceName={service_name}&outputType=json"

    def get(self, payload: dict) -> Optional[Any]:
        service_name = payload.get("serviceName")
        if not service_name:
            raise ValueError("Payload precisa conter 'serviceName'")

        url = self._build_url(service_name)
        logging.debug(f"🔗 GET Sankhya → {url} (timeout={self.timeout}s)")

        max_retries = 5
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )
                resp.raise_for_status()
                return resp.json()

            except Timeout:
                logging.warning(f"⏱️ Timeout na tentativa {attempt}/{max_retries} para {service_name}")
                if attempt == max_retries:
                    logging.error(f"❌ Timeout após {max_retries} tentativas.")
                    enviar_notificacao_telegram(f"❌ Timeout após {max_retries} tentativas.")
                    raise
                # backoff exponencial e continua o loop
                time.sleep(2 ** (attempt - 1))

            except RequestException as e:
                logging.error(f"🚨 Erro na requisição: {e}")
                raise

        # Se, por algum motivo, sair do loop sem retornar nem lançar, devolve None
        return None

    def post(self, payload: dict) -> dict:
        service_name = payload.get("serviceName")
        if not service_name:
            raise ValueError("Payload precisa conter 'serviceName'")
        url = self._build_url(service_name)
        logging.debug(f"🔗 POST Sankhya → {url}")
        resp = requests.post(url, headers=self.headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()
