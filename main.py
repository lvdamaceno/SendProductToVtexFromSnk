import logging
import time
from dotenv import load_dotenv
from notifications.telegram import enviar_notificacao_telegram
from sankhya_api.auth import SankhyaClient
from vtex_api.processamentos import vtex_atualiza_estoque, vtex_atualiza_preco_venda, vtex_merge_id_sku_dicts
from utils.configure_logging import configure_logging  # ✅ correto para pacote

# Carrega .env e configura logging com o nome do projeto
load_dotenv()
configure_logging(project="SendProductToVtexFromSnk")

def main(client):
    inicio = time.time()

    try:
        ids_skus = vtex_merge_id_sku_dicts()

        enviar_notificacao_telegram("🚀 Iniciando integração de estoques/preços para o Vtex")

        # logging.info("🚀 Iniciando envio de estoques para o Vtex")
        # vtex_atualiza_estoque(ids_skus, client)

        logging.info("🚀 Iniciando envio de preços de venda para o Vtex")
        vtex_atualiza_preco_venda(ids_skus, client)

    except Exception as e:
        logging.error(f"❌ Erro ao obter dicionário id_sku: {e}")
        enviar_notificacao_telegram(f"❌ Erro ao obter dicionário id_sku: {e}")
        raise SystemExit(1)

    fim = time.time()
    duracao_min = (fim - inicio) / 60
    logging.info(f"⏱️ Tempo total de execução: {duracao_min:.2f} minutos")


if __name__ == '__main__':
    main(client = SankhyaClient())