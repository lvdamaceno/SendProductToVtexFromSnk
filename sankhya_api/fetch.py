import json
import logging
import time
from typing import Optional, Any

import requests

from notifications.telegram import enviar_notificacao_telegram


def sankhya_fetch_estoque(codprod: int, codemp: int, local: int, client, tentativas: int = 3) -> Optional[int]:
    """
    Consulta o estoque de um produto no Sankhya com tentativas de retry em caso de falha.
    """
    payload = {
        "serviceName": "CRUDServiceProvider.loadRecords",
        "requestBody": {
            "dataSet": {
                "rootEntity": "Estoque",
                "includePresentationFields": "S",
                "offsetPage": "0",
                "criteria": {
                    "expression": {
                        "$": f"this.CODPROD = {codprod} AND this.CODEMP = {codemp} AND this.CODLOCAL = {local}"
                    },
                    "parameter": [
                        {
                            "$": "24",
                            "type": "I"
                        }
                    ]
                },
                "entity": {
                    "fieldset": {
                        "list": "CODPROD, ESTOQUE"
                    }
                }
            }
        }
    }

    for tentativa in range(1, tentativas + 1):
        try:
            response = client.post(payload)
            body = response.get("responseBody", {}).get("entities", {})

            total = int(body.get("total", "0"))
            if total == 0:
                logging.info(f"📦 Produto {codprod} → Estoque: 0 no Sankhya")
                return 0

            entity = body.get("entity", {})
            estoque = entity.get("f1", {}).get("$", "0")

            estoque_formatado = int(float(estoque))
            logging.info(f"📦 Estoque Sankhya: Codprod: {codprod} | Estoque: {estoque_formatado}")
            return estoque_formatado

        except Exception as e:
            logging.warning(f"⚠️ Tentativa {tentativa}/{tentativas} falhou ao consultar estoque do produto {codprod}: {e}")

    logging.error(f"❌ Todas as tentativas falharam ao consultar estoque do produto {codprod}")
    enviar_notificacao_telegram(f"❌ Todas as tentativas falharam ao consultar estoque do produto {codprod}")
    return None


def sankhya_fetch_preco_venda(codprod: int, client) -> Optional[str]:
    payload = {
        "serviceName": "ConsultaProdutosSP.consultaProdutos",
        "requestBody": {
            "filtros": {
                "criterio": {
                    "resourceID": "br.com.sankhya.com.cons.consultaProdutos",
                    "PERCDESC": "0",
                    "CODPROD": {
                        "$": f"{codprod}"
                    }
                },
                "isPromocao": {
                    "$": "false"
                },
                "isLiquidacao": {
                    "$": "false"
                }
            }
        }
    }

    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            response = client.post(payload)
        except requests.exceptions.ReadTimeout:
            logging.warning(f"⏳ Timeout na tentativa {attempt}/{max_retries} para CODPROD {codprod}")
            continue
        except Exception as e:
            logging.error(f"❌ Erro inesperado na tentativa {attempt}/{max_retries} para CODPROD {codprod}: {e}")
            enviar_notificacao_telegram(f"❌ Erro inesperado na tentativa {attempt}/{max_retries} para CODPROD {codprod}: {e}")
            continue

        if not isinstance(response, dict):
            logging.error(f"🔴 Esperava JSON de dict, mas recebi: {response!r}")
            enviar_notificacao_telegram(f"🔴 Esperava JSON de dict, mas recebi: {response!r}")
            continue

        resp_body = response.get("responseBody")
        if not isinstance(resp_body, dict):
            logging.error(f"🔴 Sem 'responseBody' válido: {resp_body!r}")
            enviar_notificacao_telegram(f"🔴 Sem 'responseBody' válido: {resp_body!r}")
            continue

        produtos = resp_body.get("produtos")
        if not isinstance(produtos, dict):
            logging.error(f"🔴 Sem 'produtos' válido: {produtos!r}")
            enviar_notificacao_telegram(logging.error(f"🔴 Sem 'produtos' válido: {produtos!r}"))
            continue

        produto = produtos.get("produto")
        if not isinstance(produto, dict):
            logging.error(f"🔴 Sem 'produto' válido: {produto!r}")
            enviar_notificacao_telegram(f"🔴 Sem 'produto' válido: {produto!r}")
            continue

        preco_base = produto.get("PRECOBASE", {}).get("$")
        if preco_base is None:
            logging.error(f"⚠️ Campo 'PRECOBASE' ausente p/ CODPROD {codprod}")
            enviar_notificacao_telegram(f"⚠️ Campo 'PRECOBASE' ausente p/ CODPROD {codprod}")
            continue

        logging.debug(f"💵 Preço Sankhya: {preco_base}")
        return preco_base

    logging.error(f"❌ Não consegui obter preço de venda para {codprod} após {max_retries} tentativas")
    enviar_notificacao_telegram(f"❌ Não consegui obter preço de venda para {codprod} após {max_retries} tentativas")
    return None


def sankhya_fetch_grupo_informacoes_produto(codprod: int, client, tentativas: int = 3) -> Optional[list[Any]]:
    payload = {
        "serviceName": "CRUDServiceProvider.loadRecords",
        "requestBody": {
            "dataSet": {
                "rootEntity": "Produto",
                "includePresentationFields": "N",
                "offsetPage": "0",
                "criteria": {
                    "expression": {
                        "$": f"this.CODPROD = {codprod}"
                    }
                },
                "entity": {
                    "fieldset": {
                        "list": "AD_DESCLONGALV, AD_DESCTECNICALV, AD_URLIMGLV, AD_DIFERENCIAISLV, AD_URLDEMATERIAIS"
                    }
                }
            }
        }
    }

    for tentativa in range(1, tentativas + 1):
        try:
            response = client.post(payload)
            body = response.get("responseBody", {}).get("entities", {}).get("entity", {})
            logging.debug(f"📦 Payload: {json.dumps(body, indent=2)}")
            f0 = body.get("f0", {}).get("$")
            f1 = body.get("f1", {}).get("$")
            f2 = body.get("f2", {}).get("$")
            f3 = body.get("f3", {}).get("$")
            f4 = body.get("f4", {}).get("$")
            grupo_informacoes = [f0, f1, f2, f3, f4]
            logging.debug(f"Grupo de informações: {grupo_informacoes}")
            return grupo_informacoes

        except Exception as e:
            logging.warning(f"⚠️ Tentativa {tentativa}/{tentativas} falhou ao consultar grupo de informacoes do produto {codprod}: {e}")

    logging.error(f"❌ Todas as tentativas falharam ao consultar grupo de informacoes do produto {codprod}")
    enviar_notificacao_telegram(f"❌ Todas as tentativas falharam ao consultar grupo de informacoes do produto {codprod}")
    return None