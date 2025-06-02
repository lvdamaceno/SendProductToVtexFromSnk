import logging
import time
from dotenv import load_dotenv
from notifications.telegram import enviar_notificacao_telegram
from sankhya_api.auth import SankhyaClient
from vtex_api.processamentos import vtex_atualiza_estoque, vtex_atualiza_preco_venda
from utils.configure_logging import configure_logging  # ✅ correto para pacote

# Carrega .env e configura logging com o nome do projeto
load_dotenv()
configure_logging(project="SendProductToVtexFromSnk")

if __name__ == '__main__':
    inicio = time.time()
    client = SankhyaClient()

    enviar_notificacao_telegram("=" * 40)
    enviar_notificacao_telegram("🚀 Iniciando integração de estoques/preços para o Vtex")

    logging.info("🚀 Iniciando envio de estoques para o Vtex")
    vtex_atualiza_estoque(client)

    logging.info("🚀 Iniciando envio de preços de venda para o Vtex")
    vtex_atualiza_preco_venda(client)

    fim = time.time()
    duracao_min = (fim - inicio) / 60
    logging.info(f"⏱️ Tempo total de execução: {duracao_min:.2f} minutos")
    enviar_notificacao_telegram(f"⏱️ Tempo total de execução: {duracao_min:.2f} minutos")
