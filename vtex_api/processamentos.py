import logging
import time

from sankhya_api.fetch import sankhya_fetch_estoque, sankhya_fetch_preco_venda
from vtex_api.create import vtex_create_fixed_price, delete_fixed_prices
from vtex_api.fetch import vtex_fetch_total_id_sku_list, vtex_fetch_id_sku_list, vtex_fetch_id_info, \
    vtex_fetch_estoque_sku, vtex_fetch_preco_venda_sku
from vtex_api.sender import vtex_send_update_estoque, vtex_send_update_preco_venda
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


# Status retornados pelas rotinas de atualização (contabilizados no resumo do main)
OK = "ok"
ATUALIZADO = "atualizado"
SEM_SKU = "sem_sku"
SEM_REFID = "sem_refid"
SEM_PRECO = "sem_preco"
FALHA = "falha"

# Empresa e local do Sankhya cujo estoque é publicado no depósito "Estoque" da VTEX
CODEMP_ESTOQUE = 7
CODLOCAL_ESTOQUE = 188


def normaliza_sku(id_sku, sku):
    """Retorna o primeiro SKU da lista, ou None se o produto não tiver SKU."""
    edit_sku = sku[0] if isinstance(sku, list) and sku else sku
    if edit_sku is None or edit_sku == []:
        logging.warning(f"⚠️ Produto id {id_sku} sem SKU na VTEX, ignorando")
        return None
    return edit_sku


def vtex_atualiza_estoque(id_sku, sku, client, refid=None, estoques_snk=None):
    """
    Sincroniza o estoque do SKU com o Sankhya.

    estoques_snk: dict {codprod: estoque} pré-carregado em lote; se None, consulta o produto no Sankhya.

    Returns:
        tuple: (status, detalhe) — detalhe descreve a alteração ou a falha, ou None.
    """
    edit_sku = normaliza_sku(id_sku, sku)
    if edit_sku is None:
        return SEM_SKU, None

    inicio = time.time()
    try:
        logging.debug(f"🟢 Buscando dados de estoque do id {id_sku} - sku {edit_sku}")

        if refid is None:
            refid = vtex_fetch_id_info(id_sku)
        if not refid:
            logging.warning(f"⚠️ Sem RefId para id {id_sku}, ignorando estoque")
            return SEM_REFID, None

        estoque = vtex_fetch_estoque_sku(edit_sku)
        if 'Estoque' not in estoque:
            return FALHA, f"estoque VTEX indisponível para Codprod {refid} (SKU {edit_sku})"

        estoque_vtex = estoque['Estoque']
        if estoques_snk is not None:
            estoque_snk = estoques_snk.get(int(refid), 0)
        else:
            estoque_snk = sankhya_fetch_estoque(refid, CODEMP_ESTOQUE, CODLOCAL_ESTOQUE, client)
        if estoque_snk is None:
            return FALHA, f"estoque Sankhya indisponível para Codprod {refid}"

        if estoque_snk == estoque_vtex:
            return OK, None

        logging.info(f'🚨 Estoque do produto {refid} sku {edit_sku} precisa ser atualizado')
        logging.info(f'🚨 Estoque Snk: {estoque_snk} | Estoque Vtex: {estoque_vtex}')
        if vtex_send_update_estoque(refid, edit_sku, estoque_snk, estoque_vtex):
            return ATUALIZADO, f"Codprod {refid}: estoque {estoque_vtex} → {estoque_snk}"
        return FALHA, f"falha ao enviar estoque do Codprod {refid} (SKU {edit_sku})"

    except Exception as e:
        logging.error(f"❌ Falha ao processar estoque para id {id_sku}, sku {sku}: {e}")
        return FALHA, f"erro no estoque do id {id_sku}: {e}"

    finally:
        logging.debug(f"⏱️ Estoque do id {id_sku} processado em {time.time() - inicio:.1f}s")


def vtex_atualiza_preco_venda(id_sku, sku, client, refid=None):
    """
    Sincroniza o preço base (e o preço fixo promocional) do SKU com o Sankhya.

    Returns:
        tuple: (status, detalhe) — detalhe descreve a alteração ou a falha, ou None.
    """
    edit_sku = normaliza_sku(id_sku, sku)
    if edit_sku is None:
        return SEM_SKU, None

    inicio = time.time()
    try:
        logging.debug(f"🟢 Buscando dados de preço de venda do id {id_sku} - sku {edit_sku}")

        # delete_fixed_prices(edit_sku)

        # 1) Busca no VTEX para obter o refid
        if refid is None:
            refid = vtex_fetch_id_info(id_sku)
        if not refid:
            logging.warning(f"⚠️ Sem RefId para id {id_sku}, ignorando preço")
            return SEM_REFID, None

        # 2) Chama o Sankhya
        resultado_snk = sankhya_fetch_preco_venda(refid, client)
        if resultado_snk is None:
            logging.error(f"⚠️ Não foi possível obter preço do Sankhya para produto {refid}, ignorando")
            return FALHA, f"preço Sankhya indisponível para Codprod {refid}"

        preco, preco_promo = resultado_snk
        if preco is None:
            # produto não retornado pela consulta de preço do Sankhya: não é falha da integração
            return SEM_PRECO, f"Codprod {refid} (SKU {edit_sku})"

        # 3) Busca no VTEX o preço do SKU
        preco_vtex = vtex_fetch_preco_venda_sku(edit_sku)
        if preco_vtex is None:
            return FALHA, f"preço VTEX indisponível para Codprod {refid} (SKU {edit_sku})"

        logging.debug(f"💵 Preço de venda codprod {refid} Sku {edit_sku} Sankhya: {preco} | Vtex: {preco_vtex}")

        # Normalização
        norm_preco_snk = preco.strip().replace(',', '.')
        norm_preco_vtex = preco_vtex.strip().replace(',', '.')
        logging.debug(f"🔢 Normalização preço Sankhya {norm_preco_snk}")
        logging.debug(f"🔢 Normalização preço Vtex {norm_preco_vtex}")

        dec_preco_sankhya = Decimal(norm_preco_snk)
        dec_preco_vtex = Decimal(norm_preco_vtex)

        status, detalhe = OK, None
        if dec_preco_sankhya != dec_preco_vtex:
            logging.info(f'🚨 Preço do produto {refid} sku {edit_sku} precisa ser atualizado')
            logging.info(f'🚨 Preço Snk: {dec_preco_sankhya} | Preço Vtex: {dec_preco_vtex}')
            logging.debug(f"⚠️ Enviando para atualização de preços: {refid}, {edit_sku}, {preco}, {preco_vtex}")
            if vtex_send_update_preco_venda(refid, edit_sku, preco, preco_vtex):
                status, detalhe = ATUALIZADO, f"Codprod {refid}: preço {dec_preco_vtex} → {dec_preco_sankhya}"
            else:
                status, detalhe = FALHA, f"falha ao enviar preço do Codprod {refid} (SKU {edit_sku})"
        else:
            logging.debug(f"✅ Preços iguais: {dec_preco_sankhya}")

        logging.debug(f"Preço promo {preco_promo}")
        if preco_promo and float(preco_promo) > 0:
            logging.debug('💵 Produto possui desconto, garantindo preço fixo no vtex')
            if not vtex_create_fixed_price(edit_sku, preco, preco_promo):
                falha_promo = f"falha ao criar preço promocional do Codprod {refid} (SKU {edit_sku})"
                return FALHA, f"{detalhe}; {falha_promo}" if detalhe else falha_promo
        else:
            logging.debug('💵 Produto não possui desconto')

        return status, detalhe

    except Exception as e:
        logging.error(f"❌ Falha ao processar id {id_sku}, sku {sku}: {e}")
        return FALHA, f"erro no preço do id {id_sku}: {e}"

    finally:
        logging.debug(f"⏱️ Preço do id {id_sku} processado em {time.time() - inicio:.1f}s")
