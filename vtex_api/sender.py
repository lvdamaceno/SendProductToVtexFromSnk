import logging
from notifications.telegram import enviar_notificacao_telegram
from vtex_api.client import vtex_put


def vtex_send_update_estoque(codprod, sku, estoque):
    """
    Envia uma atualização de estoque para um SKU específico no depósito fixo '1f82610'.

    Args:
        sku (int or str): ID do SKU na VTEX.
        estoque (int): Quantidade a ser atualizada.
    """
    endpoint = f"logistics/pvt/inventory/skus/{sku}/warehouses/1f82610"
    payload = {"quantity": estoque}
    mensagem = f"📦 Enviando atualização de estoque para o SKU {sku} → {estoque}"

    try:
        response = vtex_put(endpoint, data=payload, log_msg=mensagem)

        if response is not None:
            logging.info(f"✅ Estoque atualizado com sucesso para Codprod {codprod} | SKU {sku}")
            enviar_notificacao_telegram(f"✅ Estoque atualizado com sucesso para Codprod {codprod} | SKU {sku}")
        else:
            logging.warning(f"⚠️ Falha ao atualizar estoque para Codprod {codprod} | SKU {sku}")
            enviar_notificacao_telegram(f"⚠️ Falha ao atualizar estoque para Codprod {codprod} | SKU {sku}")

    except Exception as e:
        logging.error(f"❌ Erro ao atualizar estoque do Codprod {codprod} | SKU {sku}: {e}")
        enviar_notificacao_telegram(f"❌ Erro ao atualizar estoque do Codprod {codprod} | SKU {sku}: {e}")
