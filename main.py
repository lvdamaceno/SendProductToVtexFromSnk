import logging
import time
from dotenv import load_dotenv
from notifications.telegram import enviar_notificacao_telegram
from sankhya_api.auth import SankhyaClient
from vtex_api.processamentos import vtex_atualiza_estoque, vtex_atualiza_preco_venda, vtex_merge_id_sku_dicts
from utils.configure_logging import configure_logging

# Carrega .env e configura logging com o nome do projeto
load_dotenv()
configure_logging(project="SendProductToVtexFromSnk")

def main(client):
    inicio = time.time()
    enviar_notificacao_telegram("🚀 Iniciando integração de estoques/preços para o Vtex")

    try:
        ids_skus = vtex_merge_id_sku_dicts()
        for id_sku, sku in ids_skus.items():
            vtex_atualiza_estoque(id_sku, sku, client)
            vtex_atualiza_preco_venda(id_sku, sku, client)
    except Exception as e:
        logging.error(f"❌ Erro ao obter dicionário id_sku: {e}")
        enviar_notificacao_telegram(f"❌ Erro ao obter dicionário id_sku: {e}")
        raise SystemExit(1)

    fim = time.time()
    duracao_min = (fim - inicio) / 60
    logging.info(f"⏱️ Tempo total de execução: {duracao_min:.2f} minutos")


if __name__ == '__main__':
    main(client = SankhyaClient())

    # client = SankhyaClient()
    # vtex_atualiza_preco_venda(541, 547, client)

