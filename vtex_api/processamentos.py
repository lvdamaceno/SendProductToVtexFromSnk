import logging
import time

from notifications.telegram import enviar_notificacao_telegram
from sankhya_api.fetch import sankhya_fetch_estoque, sankhya_fetch_preco_venda
from vtex_api.create import vtex_create_fixed_price, delete_fixed_prices
from vtex_api.fetch import vtex_fetch_total_id_sku_list, vtex_fetch_id_sku_list, vtex_fetch_id_info, \
    vtex_fetch_estoque_sku, vtex_fetch_preco_venda_sku
from vtex_api.sender import (vtex_send_update_estoque, vtex_send_update_preco_venda,
                             vtex_update_grupo_informacoes)
from decimal import Decimal

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


def vtex_atualiza_estoque(id_sku, sku, client):
    inicio = time.time()
    try:
        edit_sku = sku[0] if isinstance(sku, list) and sku else sku
        logging.info(f"🟢 Buscando dados de estoque do id {id_sku} - sku {edit_sku}")

        refid = vtex_fetch_id_info(id_sku)

        estoque = vtex_fetch_estoque_sku(edit_sku)
        for deposito, qtd in estoque.items():
            if deposito == 'Estoque':
                estoque_snk = sankhya_fetch_estoque(refid, 7, 188, client)
                estoque_vtex = qtd
                if estoque_snk != estoque_vtex:
                    logging.info(f'🚨 Estoque do produto {refid} sku {edit_sku} precisa ser atualizado')
                    enviar_notificacao_telegram(f'🚨 Estoque do produto {refid} sku {edit_sku} precisa ser atualizado')
                    logging.info(f'🚨 Estoque Snk: {estoque_snk} | Estoque Vtex: {estoque_vtex}')
                    enviar_notificacao_telegram(f'🚨 Estoque Snk: {estoque_snk} | Estoque Vtex: {estoque_vtex}')
                    vtex_send_update_estoque(refid, edit_sku, estoque_snk, estoque_vtex)

    except Exception as e:
        logging.error(f"❌ Falha ao processar estoque para id {id_sku}, sku {sku}: {e}")
        enviar_notificacao_telegram(f"❌ Falha ao processar estoque para id {id_sku}, sku {sku}: {e}")

    fim = time.time()
    duracao_min = (fim - inicio) / 60
    logging.info(f"⏱️ Tempo total de execução: {duracao_min:.2f} minutos")


def vtex_atualiza_preco_venda(id_sku, sku, client):
    inicio = time.time()
    try:
        edit_sku = sku[0] if isinstance(sku, list) and sku else sku

        delete_fixed_prices(edit_sku)
        print(40*'-')
        logging.info(f"🟢 Buscando dados de preço de venda do id {id_sku} - sku {edit_sku}")

        # 1) Busca no VTEX para obter o refid
        refid = vtex_fetch_id_info(id_sku)

        # 2) Chama o Sankhya
        preco, preco_promo = sankhya_fetch_preco_venda(refid, client)
        if preco is None:
            logging.error(f"⚠️ Preço Sankhya ausente para produto {refid}")
            enviar_notificacao_telegram(f"⚠️ Preço Sankhya ausente para produto {refid}")

        # 3) Busca no VTEX o preço do SKU
        preco_vtex = vtex_fetch_preco_venda_sku(edit_sku)

        logging.info(f"💵 Preço de venda codprod {refid} Sku {edit_sku} Sankhya: {preco} | Vtex: {preco_vtex}")

        # Normalização
        norm_preco_snk = preco.strip().replace(',', '.')
        norm_preco_vtex = preco_vtex.strip().replace(',', '.')
        logging.debug(f"🔢 Normalização preço Sankhya {norm_preco_snk}")
        logging.debug(f"🔢 Normalização preço Vtex {norm_preco_vtex}")

        dec_preco_sankhya = Decimal(norm_preco_snk)
        dec_preco_vtex = Decimal(norm_preco_vtex)

        if dec_preco_sankhya != dec_preco_vtex:
            logging.info(f'🚨 Preço do produto {refid} sku {edit_sku} precisa ser atualizado')
            enviar_notificacao_telegram(f'🚨 Preço do produto {refid} sku {edit_sku} precisa ser atualizado')
            logging.info(f'🚨 Preço Snk: {dec_preco_sankhya} | Preço Vtex: {dec_preco_vtex}')
            enviar_notificacao_telegram(f'🚨 Preço Snk: {dec_preco_sankhya} | Preço Vtex: {dec_preco_vtex}')
            logging.debug(f"⚠️ Enviando para atualização de preços: {refid}, {edit_sku}, {preco}, {preco_vtex}")
            vtex_send_update_preco_venda(refid, edit_sku, preco, preco_vtex)
        else:
            logging.info(f"✅ Preços iguais: {dec_preco_sankhya}")

        logging.info(f"Preço promo {preco_promo}")
        if float(preco_promo) > 0:
            logging.info('💵 Produto possui desconto, criando preço fixo no vtex')
            vtex_create_fixed_price(edit_sku, preco, preco_promo)
        else:
            logging.info('💵 Produto não possui desconto')


    except Exception as e:
        logging.error(f"❌ Falha ao processar id {id_sku}, sku {sku}: {e}")
        enviar_notificacao_telegram(f"❌ Falha ao processar id {id_sku}, sku {sku}: {e}")

    fim = time.time()
    duracao_min = (fim - inicio) / 60
    logging.info(f"⏱️ Tempo total de execução: {duracao_min:.2f} minutos")


def vtex_atualiza_cadastro_produto(id_vtex, snk_codprod, client):
    inicio = time.time()

    vtex_update_grupo_informacoes(id_vtex, snk_codprod, client)

    fim = time.time()
    duracao_min = (fim - inicio) / 60

    logging.info(f"⏱️ Tempo total de execução: {duracao_min:.2f} minutos")
