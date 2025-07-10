import json
import logging
from vtex_api.client import vtex_get, vtex_delete, vtex_post
from datetime import datetime, timezone, timedelta

def agora_iso8601() -> str:
    tz = timezone(timedelta(hours=-3))
    return datetime.now(tz).isoformat(timespec="seconds")

def amanha_iso8601() -> str:
    tz = timezone(timedelta(hours=-3))
    return (datetime.now(tz) + timedelta(days=1)).isoformat(timespec="seconds")

def get_fixed_prices(id_sku: int) -> list:
    """
    Retorna a lista de preços fixos existentes para o SKU,
    ou lista vazia caso não haja nenhum.
    """
    try:
        endpoint = f"pricing/prices/{id_sku}/fixed"
        # GET retorna uma lista de objetos, cada um com campo "id"
        return vtex_get(endpoint, "🔢 Buscando preços fixos existentes") or []
    except Exception as e:
        logging.error(f"❌ Erro ao buscar preços fixos do SKU {id_sku}: {e}")
        return []

def delete_fixed_prices(edit_sku: int):
    """
    Deleta todos os preços fixos encontrados para o SKU.
    """
    fixed_prices = get_fixed_prices(edit_sku)
    if fixed_prices:
        endpoint = f"pricing/prices/{edit_sku}/fixed/1"
        try:
            vtex_delete(endpoint, f"🔢 Deletando preço fixo id do SKU {edit_sku}")
            logging.info(f"✅ Preço fixo deletado com sucesso.")
        except Exception as e:
            logging.error(f"❌ Falha ao deletar preço fixo : {e}")

def vtex_create_fixed_price(edit_sku: int, preco_promo: float):
    """
    Remove preços fixos existentes e cria um novo preço fixo para o SKU
    no intervalo de hoje até amanhã.
    """
    # 1) Excluir tudo que já existe
    delete_fixed_prices(edit_sku)

    # 2) Payload do novo preço fixo
    payload = [
        {
            "value": float(preco_promo),
            "listPrice": float(preco_promo),
            "minQuantity": 1,
            "dateRange": {
                "from": agora_iso8601(),
                "to": amanha_iso8601()
            }
        }
    ]
    logging.info(f"💵 Criando novo preço fixo: {json.dumps(payload, ensure_ascii=False)}")
    try:
        # Observação: o endpoint de criação/edit não precisa de um ID fixo no path
        endpoint = f"pricing/prices/{edit_sku}/fixed/1"
        vtex_post(endpoint, payload, f"🔢 Criando preço fixo para SKU {edit_sku}")
        logging.info(f"✅ Novo preço fixo criado com sucesso para o SKU {edit_sku}.")
    except Exception as e:
        logging.error(f"❌ Falha ao criar preço fixo do SKU {edit_sku}: {e}")
