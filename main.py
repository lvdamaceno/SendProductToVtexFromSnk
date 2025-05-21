import logging

from sankhya_api.auth import SankhyaClient
from vtex_api.processamentos import vtex_atualiza_estoque
from utils import configure_logging
import time


if __name__ == '__main__':
    configure_logging()
    inicio = time.time()

    client = SankhyaClient()
    vtex_atualiza_estoque(client)

    fim = time.time()
    duracao_min = (fim - inicio) / 60
    logging.info(f"⏱️ Tempo total de execução: {duracao_min:.2f} minutos")