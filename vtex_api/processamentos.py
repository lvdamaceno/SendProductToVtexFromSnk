import logging

from sankhya_api.fetch import sankhya_buscar_estoque
from vtex_api.fetch import vtex_fetch_total_id_sku_list, vtex_fetch_id_sku_list, vtex_fetch_id_info, vtex_estoque_sku
from vtex_api.sender import vtex_send_update_estoque


def vtex_merge_id_sku_dicts():
    """
    Consulta todos os IDs e SKUs da VTEX e os combina em um único dicionário.

    Returns:
        dict: {id: sku}
    """
    id_sku_dict = {}

    try:
        total_produtos = vtex_fetch_total_id_sku_list()
        if not total_produtos:
            raise ValueError("❌ Não foi possível obter o total de produtos.")
    except Exception as e:
        logging.error(f"❌ Erro ao obter total de produtos: {e}")
        raise SystemExit(1)

    max_ids_to_fetch = 250

    for start in range(0, total_produtos, max_ids_to_fetch):
        end = min(start + max_ids_to_fetch - 1, total_produtos - 1)
        try:
            partial = vtex_fetch_id_sku_list(start, end)
            if isinstance(partial, dict):
                id_sku_dict.update(partial)
            else:
                logging.warning(f"⚠️ Dados inesperados no intervalo {start}-{end}: {partial}")
        except Exception as e:
            logging.error(f"❌ Erro ao buscar intervalo {start}-{end}: {e}")

    logging.debug(f"🔢 id_sku_dict: {len(id_sku_dict)} itens")
    return id_sku_dict


def vtex_atualiza_estoque(client):
    try:
        ids_skus = vtex_merge_id_sku_dicts()
    except Exception as e:
        logging.error(f"❌ Erro ao obter dicionário id_sku: {e}")
        raise SystemExit(1)

    for id_sku, sku in ids_skus.items():
        try:
            edit_sku = sku[0] if isinstance(sku, list) and sku else sku
            logging.info(f"🟢 Buscando dados do id {id_sku} - sku {edit_sku}")

            refid = vtex_fetch_id_info(id_sku)

            estoque = vtex_estoque_sku(edit_sku)
            for deposito, qtd in estoque.items():
                if deposito == 'Estoque':
                    estoque_snk = sankhya_buscar_estoque(refid, 7, 188, client)
                    estoque_vtex = qtd
                    if estoque_snk != estoque_vtex:
                        logging.info(f'🚨 Estoque do produto {refid} sku {edit_sku} precisa ser atualizado')
                        logging.info(f'🚨 Estoque Snk: {estoque_snk} | Estoque Vtex: {estoque_vtex}')
                        vtex_send_update_estoque(refid, edit_sku, estoque_snk, estoque_vtex)

        except Exception as e:
            logging.error(f"❌ Falha ao processar id {id_sku}, sku {sku}: {e}")