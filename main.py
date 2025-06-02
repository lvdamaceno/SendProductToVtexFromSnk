import logging
from notifications.telegram import enviar_notificacao_telegram
from sankhya_api.auth import SankhyaClient
from vtex_api.processamentos import vtex_atualiza_estoque, vtex_atualiza_preco_venda, vtex_atualiza_cadastro_produto
from utils import configure_logging
import time

configure_logging()


if __name__ == '__main__':
    inicio = time.time()
    client = SankhyaClient()

    enviar_notificacao_telegram(40*"=")
    enviar_notificacao_telegram("🚀 Iniciando integração de estoques/preços para o Vtex")

    logging.info("🚀 Iniciando envio de estoques o Vtex")
    vtex_atualiza_estoque(client)

    logging.info("🚀 Iniciando envio de preços de venda o Vtex")
    vtex_atualiza_preco_venda(client)

    fim = time.time()
    duracao_min = (fim - inicio) / 60
    logging.info(f"⏱️ Tempo total de execução p/ integração de produtos: {duracao_min:.2f} minutos")
    enviar_notificacao_telegram(f"⏱️ Tempo total de execução: {duracao_min:.2f} minutos")
    logging.info(f"⏱️ Tempo total de execução: {duracao_min:.2f} minutos")