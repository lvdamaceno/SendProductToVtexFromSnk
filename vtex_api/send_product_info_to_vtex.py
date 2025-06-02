from sankhya_api.auth import SankhyaClient
from vtex_api.processamentos import vtex_atualiza_estoque, vtex_atualiza_preco_venda, vtex_atualiza_cadastro_produto
from utils import configure_logging
import time

configure_logging()


if __name__ == '__main__':
    inicio = time.time()
    client = SankhyaClient()

    id_vtex = 0
    snk_codprod = 0

    vtex_atualiza_cadastro_produto(id_vtex, snk_codprod, client)
