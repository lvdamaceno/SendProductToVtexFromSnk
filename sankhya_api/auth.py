import logging
import os
import time
from typing import Optional, Any

import requests
from dotenv import load_dotenv
from requests import RequestException, Timeout
from json.decoder import JSONDecodeError
from notifications.telegram import enviar_notificacao_telegram

load_dotenv()

TOKEN = os.getenv("SANKHYA_TOKEN")
APPKEY = os.getenv("SANKHYA_APPKEY")
USERNAME = os.getenv("SANKHYA_USERNAME")
PASSWORD = os.getenv("SANKHYA_PASSWORD")

# ----------------------------------------------------------------------------
# 🔧 Configurações iniciais
# ----------------------------------------------------------------------------
BASE_MGE_URL     = "https://api.sankhya.com.br/gateway/v1/mge/service.sbr"
BASE_MGECOM_URL  = "https://api.sankhya.com.br/gateway/v1/mgecom/service.sbr"
HEADERS_BASE     = {"Content-Type": "application/json"}

# ----------------------------------------------------------------------------
# 🔐 Cliente Sankhya com autenticação automática e refresh
# ----------------------------------------------------------------------------
class SankhyaClient:
    def __init__(self):
        self.token: Optional[str] = None
        self.token_expiry: float    = 0.0
        self.headers: dict          = {}
        self.timeout: int           = 120

        # autentica pela primeira vez
        self._authenticate()

    def _authenticate(self):
        """Faz login e atualiza self.token, self.token_expiry e self.headers."""
        login_url = "https://api.sankhya.com.br/login"
        auth_headers = {
            "token":    TOKEN,
            "appkey":   APPKEY,
            "username": USERNAME,
            "password": PASSWORD,
        }

        try:
            logging.info("🔐 Autenticando na API da Sankhya...")
            resp = requests.post(login_url, headers=auth_headers, timeout=self.timeout)
            resp.raise_for_status()

            data = resp.json()
            bearer = data.get("bearerToken")
            if not bearer:
                raise ValueError("Bearer token não encontrado na resposta.")

            # atualiza token e cabeçalhos
            self.token   = bearer
            self.headers = {**HEADERS_BASE, "Authorization": f"Bearer {self.token}"}

            # expira em 15 minutos, com 10% de folga (i.e. 13.5 min)
            self.token_expiry = time.time() + (15 * 60) * 0.9
            logging.debug(f"✅ Token válido até {time.ctime(self.token_expiry)}")

        except Exception as e:
            logging.error(f"❌ Erro ao autenticar: {e}", exc_info=True)
            enviar_notificacao_telegram("❌ Não foi possível autenticar na API do Sankhya")
            raise

    def _ensure_token_valid(self):
        """Reloga se não tiver token ou se já tiver expirado."""
        if not self.token or time.time() >= self.token_expiry:
            logging.info("🔄 Token expirado ou ausente, realizando novo login...")
            self._authenticate()

    def _build_url(self, service_name: str) -> str:
        base = BASE_MGECOM_URL if service_name.startswith((
            "CACSP.", "SelecaoDocumentoSP.", "ConsultaProdutosSP."
        )) else BASE_MGE_URL
        return f"{base}?serviceName={service_name}&outputType=json"

    def get(self, payload: dict) -> Optional[Any]:
        """
        GET para os serviços Sankhya (mge e mgecom), com retry e refresh de token.
        Retorna dict ou None em caso de erro/formato inesperado.
        """
        service_name = payload.get("serviceName")
        if not service_name:
            raise ValueError("Payload precisa conter 'serviceName'.")

        url = self._build_url(service_name)
        max_retries = 5

        for attempt in range(1, max_retries + 1):
            # garante que o token ainda seja válido
            self._ensure_token_valid()

            try:
                resp = requests.get(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )
                logging.debug(f"🔎 {service_name} status {resp.status_code} tentativa {attempt}/{max_retries}")

                # se 401, renova token e repete
                if resp.status_code == 401:
                    logging.warning("⚠️ 401 Unauthorized, renovando token e repetindo...")
                    self._authenticate()
                    continue

                resp.raise_for_status()
                text = resp.text.strip()
                if not text.startswith(("{", "[")):
                    logging.error(f"🔴 Esperava JSON mas recebi:\n{text!r}")
                    enviar_notificacao_telegram(f"🔴 Esperava JSON mas recebi:\n{text!r}")
                    return None

                return resp.json()

            except Timeout:
                logging.warning(f"⏱️ Timeout {attempt}/{max_retries} para {service_name}")
                if attempt == max_retries:
                    logging.error(f"❌ Timeout após {max_retries} tentativas.")
                    enviar_notificacao_telegram(f"❌ Timeout ao chamar {service_name}")
                    raise
                # backoff exponencial
                time.sleep(2 ** (attempt - 1))

            except RequestException as e:
                logging.error(f"🚨 Erro na requisição de {service_name}: {e}", exc_info=True)
                if 'resp' in locals():
                    logging.error(f"🚨 Response body: {resp.text!r}")
                raise

        return None

    def post(self, payload: dict) -> Optional[Any]:
        """
        POST (sem retry automático, mas com refresh de token em 401).
        Retorna dict ou None em caso de JSON inválido ou erro HTTP.
        """
        service_name = payload.get("serviceName")
        if not service_name:
            raise ValueError("Payload precisa conter 'serviceName'.")

        url = self._build_url(service_name)
        # garante token fresh
        self._ensure_token_valid()

        resp = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
        if resp.status_code == 401:
            logging.warning("⚠️ 401 Unauthorized ao POST, renovando token e repetindo...")
            self._authenticate()
            resp = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)

        try:
            resp.raise_for_status()
            return resp.json()
        except JSONDecodeError:
            logging.error(f"❌ JSON inválido no POST {service_name}: {resp.text!r}")
            enviar_notificacao_telegram(f"❌ JSON inválido no POST {service_name}: {resp.text!r}")
            return None
        except RequestException as e:
            logging.error(f"🚨 Erro HTTP no POST {service_name}: {e}", exc_info=True)
            enviar_notificacao_telegram(f"🚨 Erro HTTP no POST {service_name}: {e}", exc_info=True)
            return None
