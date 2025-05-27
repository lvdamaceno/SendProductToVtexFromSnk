import logging
from notifications.telegram import enviar_notificacao_telegram
from vtex_api.client import vtex_put


def vtex_send_update_estoque(codprod, sku, estoque_snk, estoque_vtex):
    endpoint = f"logistics/pvt/inventory/skus/{sku}/warehouses/1f82610"
    payload = {"quantity": estoque_snk}
    mensagem = f"📦 Enviando atualização de estoque para o SKU {sku} → {estoque_snk}"

    try:
        response = vtex_put(endpoint, data=payload, log_msg=mensagem)

        if response is not None:
            logging.info(f"✅ Estoque atualizado com sucesso para Codprod {codprod} | SKU {sku} | Estoque Snk {estoque_snk} | Estoque Vtex: {estoque_vtex}")
            enviar_notificacao_telegram(f"✅ Estoque atualizado com sucesso para Codprod {codprod} | SKU {sku} | Estoque Snk {estoque_snk} | Estoque Vtex: {estoque_vtex}")
        else:
            logging.warning(f"⚠️ Falha ao atualizar estoque para Codprod {codprod} | SKU {sku}")
            enviar_notificacao_telegram(f"⚠️ Falha ao atualizar estoque para Codprod {codprod} | SKU {sku}")

    except Exception as e:
        logging.error(f"❌ Erro ao atualizar estoque do Codprod {codprod} | SKU {sku}: {e}")
        enviar_notificacao_telegram(f"❌ Erro ao atualizar estoque do Codprod {codprod} | SKU {sku}: {e}")


def vtex_send_update_preco_venda(codprod, sku, preco_snk, preco_vtex):
    logging.debug(f"🔢 Codprod {codprod} | SKU {sku} | preco snk {preco_snk} | preco vtex {preco_vtex}")
    endpoint = f"pricing/prices/{sku}"
    try:
        preco_float = float(preco_snk)
    except ValueError:
        logging.error(f"❌ Valor inválido para preco_snk: {preco_snk}")
        return

    payload = {
        "markup": 0,
        "basePrice": preco_float
    }

    mensagem = f"📦 Enviando atualização de preço de venda para o SKU {sku} → {preco_float}"

    try:
        response = vtex_put(endpoint, data=payload, log_msg=mensagem)

        if response is not None:
            logging.info(
                f"✅ Preço de venda atualizado com sucesso para Codprod {codprod} | SKU {sku} | Preço Snk {preco_float} | Preço Vtex: {preco_vtex}")
            enviar_notificacao_telegram(
                f"✅ Preço de venda atualizado com sucesso para Codprod {codprod} | SKU {sku} | Preço Snk {preco_float} | Preço Vtex: {preco_vtex}")
        else:
            logging.warning(f"⚠️ Falha ao atualizar preço para Codprod {codprod} | SKU {sku}")
            enviar_notificacao_telegram(f"⚠️ Falha ao atualizar preço para Codprod {codprod} | SKU {sku}")

    except Exception as e:
        logging.error(f"❌ Erro ao atualizar preço do Codprod {codprod} | SKU {sku}: {e}")
        enviar_notificacao_telegram(f"❌ Erro ao atualizar preço do Codprod {codprod} | SKU {sku}: {e}")