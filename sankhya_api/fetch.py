import logging
from typing import Optional, Dict

def sankhya_buscar_estoque(codprod: int, codemp: int, local:int, client) -> Optional[int]:
    """
    Consulta o estoque de um produto específico via API Sankhya.

    - Se total de resultados for 0, retorna estoque = 0
    - Se houver resultado, retorna o valor real de 'ESTOQUE' (campo f1)

    Args:
        codprod (int): Código do produto.
        client (SankhyaClient): Instância autenticada da API.

    Returns:
        dict | None: {"CODPROD": ..., "ESTOQUE": ...} ou None em caso de erro.
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

    try:
        response = client.post(payload)
        body = response.get("responseBody", {}).get("entities", {})

        total = int(body.get("total", "0"))

        if total == 0:
            logging.info(f"📦 Produto {codprod} → Estoque: 0 no Sankhya")
            return 0

        entity = body.get("entity", {})
        estoque = entity.get("f1", {}).get("$", "0")

        logging.info(f"📦 Estoque Sankhya: Codprod: {codprod} | Estoque: {estoque}")
        estoque_formatado = int(float(estoque))
        return estoque_formatado

    except Exception as e:
        logging.error(f"❌ Erro ao consultar estoque do produto {codprod}: {e}")
        return None
