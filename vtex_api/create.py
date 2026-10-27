import json
import logging

from notifications.telegram import enviar_notificacao_telegram
from vtex_api.client import vtex_get, vtex_delete, vtex_post
from datetime import datetime, timezone, timedelta

# Preço fixo vale 24h; só é recriado quando faltar menos que isso para vencer
RENOVA_PRECO_FIXO_ANTES = timedelta(hours=12)

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
    logging.debug(f"🟢 Buscando preços fixos para o id {id_sku}")
    try:
        endpoint = f"pricing/prices/{id_sku}/fixed"
        # GET retorna uma lista de objetos, cada um com campo "id"
        response = vtex_get(endpoint, ok_404=True) or []
        logging.debug(f"Response get_fixed_prices: {response}")
        return response
    except Exception as e:
        logging.error(f"❌ Erro ao buscar preços fixos do SKU {id_sku}: {e}")
        return []

def delete_fixed_prices(edit_sku: int, fixed_prices=None) -> bool:
    """
    Deleta todos os preços fixos encontrados para o SKU. Retorna False se a exclusão falhou.
    """
    logging.debug(f"🟢 Tentando deletar preços fixos existentes para o sku {edit_sku}")
    if fixed_prices is None:
        fixed_prices = get_fixed_prices(edit_sku)

    if not fixed_prices:
        return True

    endpoint = f"pricing/prices/{edit_sku}/fixed/1"
    if vtex_delete(endpoint, f"🔢 Deletando preço fixo id do SKU {edit_sku}") is None:
        logging.error(f"❌ Falha ao deletar preço fixo do SKU {edit_sku}")
        return False
    logging.debug(f"✅ Preço fixo do SKU {edit_sku} deletado com sucesso.")
    return True

def _preco_fixo_vigente(fixed_prices: list, preco, preco_promo) -> bool:
    """True se já existe um único preço fixo com os mesmos valores e longe de vencer."""
    if not isinstance(fixed_prices, list) or len(fixed_prices) != 1:
        return False
    atual = fixed_prices[0]
    try:
        if round(float(atual["value"]), 2) != round(float(preco_promo), 2) or \
                round(float(atual["listPrice"]), 2) != round(float(preco), 2):
            return False
        vence = datetime.fromisoformat(atual["dateRange"]["to"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError):
        return False
    return vence - datetime.now(timezone.utc) > RENOVA_PRECO_FIXO_ANTES

def vtex_create_fixed_price(edit_sku: int, preco: float, preco_promo: float) -> bool:
    """
    Garante um preço fixo para o SKU no intervalo de hoje até amanhã, recriando-o
    apenas se mudou ou está perto de vencer. Retorna False se a VTEX recusou.
    """
    existentes = get_fixed_prices(edit_sku)
    if _preco_fixo_vigente(existentes, preco, preco_promo):
        logging.debug(f"💵 Preço fixo do SKU {edit_sku} já vigente, nada a fazer")
        return True

    logging.info(f"🟢 Criando preço promocional para o sku {edit_sku}")

    # 1) Excluir tudo que já existe
    if not delete_fixed_prices(edit_sku, existentes):
        return False

    # 2) Payload do novo preço fixo
    payload = [
        {
            "value": float(preco_promo),
            "listPrice": float(preco),
            "minQuantity": 1,
            "dateRange": {
                "from": agora_iso8601(),
                "to": amanha_iso8601()
            }
        }
    ]
    logging.debug(f"💵 Criando novo preço fixo: {json.dumps(payload, ensure_ascii=False)}")
    endpoint = f"pricing/prices/{edit_sku}/fixed/1"
    if vtex_post(endpoint, payload, f"🔢 Criando preço fixo para SKU {edit_sku}") is None:
        logging.error(f"❌ Falha ao criar preço fixo do SKU {edit_sku}")
        return False
    logging.info(f"✅ Novo preço fixo criado com sucesso para o SKU {edit_sku}.")
    return True
