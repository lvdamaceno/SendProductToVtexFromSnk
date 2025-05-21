import json
import logging

from sankhya_api.auth import SankhyaClient

def execute_query(sql: str, client: SankhyaClient):
    payload = {
        "serviceName": "DbExplorerSP.executeQuery",
        "requestBody": {
            "sql": sql
        }
    }

    logging.debug("📄 Payload de executeQuery:\n" + json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        logging.debug(f"🔎 Executando SQL no Sankhya: {sql}")
        response = client.get(payload)
        rows = response['responseBody']['rows']
        logging.debug("🔍 Resposta completa da API Sankhya:\n" +
                      json.dumps(rows, indent=2, ensure_ascii=False))
        return rows
    except Exception as e:
        logging.error(f"🚨 Erro ao executar DbExplorerSP.executeQuery: {e}")
        return {"error": str(e)}