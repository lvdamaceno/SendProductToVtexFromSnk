import logging
from notifications.telegram import enviar_notificacao_telegram
from sankhya_api.auth import SankhyaClient
from vtex_api.processamentos import vtex_atualiza_estoque, vtex_atualiza_preco_venda
from utils import configure_logging
import time

configure_logging()


if __name__ == '__main__':
    inicio = time.time()
    client = SankhyaClient()

    enviar_notificacao_telegram("🚀 Iniciando integração de produtos para o Vtex")
    enviar_notificacao_telegram("🚀 Iniciando envio de estoques o Vtex")
    vtex_atualiza_estoque(client)
    enviar_notificacao_telegram("🚀 Iniciando envio de preços de venda o Vtex")
    vtex_atualiza_preco_venda(client)

    fim = time.time()
    duracao_min = (fim - inicio) / 60
    enviar_notificacao_telegram(f"⏱️ Tempo total de execução p/ integração de produtos: {duracao_min:.2f} minutos")
    logging.info(f"⏱️ Tempo total de execução: {duracao_min:.2f} minutos")