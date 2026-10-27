import logging
from notifications.telegram import enviar_notificacao_telegram
from sankhya_api.fetch import sankhya_fetch_grupo_informacoes_produto
from vtex_api.client import vtex_put, vtex_post


def vtex_send_update_estoque(codprod, sku, estoque_snk, estoque_vtex) -> bool:
    endpoint = f"logistics/pvt/inventory/skus/{sku}/warehouses/1f82610"
    payload = {"quantity": estoque_snk}
    mensagem = f"📦 Enviando atualização de estoque para o SKU {sku} → {estoque_snk}"

    try:
        response = vtex_put(endpoint, data=payload, log_msg=mensagem)

        if response is not None:
            logging.info(f"✅ Estoque atualizado com sucesso para Codprod {codprod} | SKU {sku} | Estoque atualizado: {estoque_snk} | Estoque Anterior: {estoque_vtex}")
            return True

        logging.warning(f"⚠️ Falha ao atualizar estoque para Codprod {codprod} | SKU {sku}")
        return False

    except Exception as e:
        logging.error(f"❌ Erro ao atualizar estoque do Codprod {codprod} | SKU {sku}: {e}")
        return False


def vtex_send_update_preco_venda(codprod, sku, preco_snk, preco_vtex) -> bool:
    logging.info(f"🟢 Enviando para p Vtex atualização de preço de venda {codprod}")
    logging.debug(f"🔢 Codprod {codprod} | SKU {sku} | preco snk {preco_snk} | preco vtex {preco_vtex}")
    endpoint = f"pricing/prices/{sku}"
    try:
        preco_float = float(preco_snk)
    except ValueError:
        logging.error(f"❌ Valor inválido para preco_snk: {preco_snk}")
        return False

    payload = {"markup": 0, "basePrice": preco_float}
    mensagem = f"📦 Enviando atualização de preço de venda para o SKU {sku} → {preco_float}"

    try:
        response = vtex_put(endpoint, data=payload, log_msg=mensagem)

        if response is not None:
            logging.info(
                f"✅ Preço de venda atualizado com sucesso para Codprod {codprod} | SKU {sku} | Preço Atualizado: {preco_float} | Preço Anterior: {preco_vtex}")
            return True

        logging.warning(f"⚠️ Falha ao atualizar preço para Codprod {codprod} | SKU {sku}")
        return False

    except Exception as e:
        logging.error(f"❌ Erro ao atualizar preço do Codprod {codprod} | SKU {sku}: {e}")
        return False


def vtex_update_grupo_informacoes(id_vtex, snk_codprod, client):
    endpoint = f"catalog_system/pvt/products/{id_vtex}/specification"

    grupo_informacao = sankhya_fetch_grupo_informacoes_produto(snk_codprod, client)
    descricao, diferenciais, carateristicas, materiais, imagem = grupo_informacao

    payload = [
        {
            "Value": [
                f"{descricao}",
            ],
            "Id": 20,
            "Name": "Descrição"
        },
        {
            "Value": [
                f"{diferenciais}",
            ],
            "Id": 21,
            "Name": "Diferenciais"
        },
        {
            "Value": [
                f"{carateristicas}",
            ],
            "Id": 22,
            "Name": "Características"
        },
        {
            "Value": [
                f"{materiais}",
            ],
            "Id": 23,
            "Name": "Download  de materiais"
        },
        {
            "Value": [
                f"{imagem}",
            ],
            "Id": 24,
            "Name": "Imagem da descrição"
        }
    ]

    mensagem = f"📦 Enviando atualização de cadastro de produto para o ID {id_vtex}"

    try:
        response = vtex_post(endpoint, data=payload, log_msg=mensagem)

        if response is not None:
            logging.info(f"✅ Grupo de informações atualizado com sucesso para o id {id_vtex}")
            enviar_notificacao_telegram(f"✅ Grupo de informações atualizado com sucesso para o id {id_vtex}")
        else:
            logging.warning(f"⚠️ Falha ao atualizar grupo de informações para Id {id_vtex}")
            enviar_notificacao_telegram(f"⚠⚠️ Falha ao atualizar grupo de informações para Id {id_vtex}")

    except Exception as e:
        logging.error(f"❌ Erro ao atualizar grupo de informações do Id {id_vtex}")
        enviar_notificacao_telegram(f"❌ Erro ao atualizar grupo de informações do Id {id_vtex}")