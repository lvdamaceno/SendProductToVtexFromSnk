import logging

from vtex_api.client import vtex_get


def vtex_fetch_total_id_sku_list():
    """
    Consulta o total de produtos (SKUs) disponíveis na VTEX.

    Returns:
        int or None: total de SKUs ou None em caso de erro.
    """
    endpoint = "catalog_system/pvt/products/GetProductAndSkuIds"

    try:
        result = vtex_get(endpoint, "🔢 Buscando total de produtos")
        if not result:
            logging.warning("⚠️ Nenhum resultado retornado ao buscar total de produtos.")
            return None

        total = result.get('range', {}).get('total')
        if total is not None:
            logging.debug(f"🔢 Total de produtos: {total}")
            return total
        else:
            logging.warning("⚠️ Campo 'total' ausente na resposta da VTEX.")
            return None

    except Exception as e:
        logging.error(f"❌ Erro ao buscar total de produtos: {e}")
        return None


def vtex_fetch_id_sku_list(start, end):
    """
    Busca IDs e SKUs de produtos da VTEX no intervalo especificado.

    Args:
        start (int): índice inicial
        end (int): índice final

    Returns:
        list: lista de dicts com id/sku ou None em caso de falha
    """
    endpoint = f"catalog_system/pvt/products/GetProductAndSkuIds?_from={start}&_to={end}"

    try:
        result = vtex_get(endpoint, f"🟢 Buscando ids/skus {start} to {end}")
        if not result:
            logging.warning(f"⚠️ Nenhum resultado para intervalo {start}–{end}")
            return None

        data = result.get('data')
        if data:
            logging.debug(f"📄 Ids/Skus ({len(data)} itens): {data}")
        else:
            logging.warning(f"⚠️ Resposta sem dados para intervalo {start}–{end}")

        return data

    except Exception as e:
        logging.error(f"❌ Erro ao buscar ids/skus {start}–{end}: {e}")
        return None


def vtex_fetch_id_info(id_sku):
    """
    Consulta informações básicas do produto a partir de um SKU.

    Retorna o RefId (código de referência), ou None em caso de erro.
    """
    endpoint = f"catalog/pvt/product/{id_sku}"

    try:
        result = vtex_get(endpoint)
        if not result:
            logging.warning(f"⚠️ Nenhum resultado encontrado para SKU {id_sku}")
            return None

        ref_id = result.get("RefId")
        nome = result.get("Name")

        if ref_id and nome:
            logging.info(f"📄 Produto: {ref_id} - {nome}")
        elif ref_id:
            logging.info(f"📄 Produto: {ref_id}")
        else:
            logging.warning(f"⚠️ Produto sem RefId para SKU {id_sku}")

        return ref_id

    except Exception as e:
        logging.error(f"❌ Erro ao buscar informações do produto SKU {id_sku}: {e}")
        return None


def vtex_estoque_sku(id_sku):
    """
    Consulta o estoque de um SKU na VTEX e retorna um dicionário com os depósitos e suas quantidades.
    """
    endpoint = f"logistics/pvt/inventory/skus/{id_sku}"
    estoque = {}

    try:
        result = vtex_get(endpoint)
        if not result:
            logging.warning(f"⚠️ Nenhum resultado para o SKU {id_sku}")
            return estoque

        balance = result.get('balance', [])
        for item in balance:
            deposito = item.get('warehouseName')
            total = item.get('totalQuantity')
            if deposito is not None and total is not None:
                estoque[deposito] = total

        if estoque:
            log_str = ", ".join(f"{k} = {v}" for k, v in sorted(estoque.items()))
            logging.info(f"📦 Estoque VTEX: SKU {id_sku}: {log_str}")
        else:
            logging.warning(f"⚠️ SKU {id_sku} com dados de estoque vazios.")

    except Exception as e:
        logging.error(f"❌ Erro ao consultar estoque do SKU {id_sku}: {e}")

    return estoque
