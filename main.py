import logging
import os
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from notifications.telegram import enviar_notificacao_telegram
from sankhya_api.auth import SankhyaClient
from sankhya_api.fetch import sankhya_fetch_estoques
from vtex_api.fetch import vtex_fetch_id_info
from vtex_api.processamentos import (vtex_atualiza_estoque, vtex_atualiza_preco_venda, vtex_merge_id_sku_dicts,
                                     ATUALIZADO, FALHA, SEM_SKU, SEM_REFID, CODEMP_ESTOQUE, CODLOCAL_ESTOQUE)
from utils.configure_logging import configure_logging

# Carrega .env e configura logging com o nome do projeto
load_dotenv()
configure_logging(project="SendProductToVtexFromSnk")

# Acima desse percentual de produtos com falha, o cron sai com erro para o Render alertar
LIMITE_FALHAS = 0.2
# Máximo de linhas de detalhe por seção no resumo do Telegram
MAX_DETALHES = 20
# Produtos processados em paralelo (chamadas VTEX + consulta de preço no Sankhya)
SYNC_WORKERS = int(os.getenv("SYNC_WORKERS", "4"))


def _secao(titulo, itens):
    if not itens:
        return []
    linhas = [f"\n{titulo} ({len(itens)}):"]
    # corta cada item para não estourar o limite de 4096 caracteres do Telegram
    linhas += [f"• {item[:150]}" for item in itens[:MAX_DETALHES]]
    if len(itens) > MAX_DETALHES:
        linhas.append(f"• ... e mais {len(itens) - MAX_DETALHES}")
    return linhas


def _monta_resumo(total, contagem, atualizados, falhas, duracao_min):
    linhas = [
        f"📊 Integração Sankhya → VTEX concluída em {duracao_min:.1f} min",
        f"Produtos: {total}",
        f"Estoque: {contagem['estoque', ATUALIZADO]} atualizados, {contagem['estoque', FALHA]} falhas",
        f"Preço: {contagem['preco', ATUALIZADO]} atualizados, {contagem['preco', FALHA]} falhas",
        f"Sem SKU: {contagem['estoque', SEM_SKU]} | Sem RefId: {contagem['estoque', SEM_REFID]}",
    ]
    linhas += _secao("✅ Atualizados", atualizados)
    linhas += _secao("❌ Falhas", falhas)
    return "\n".join(linhas)


def _processa_produto(id_sku, sku, client, estoques_snk):
    """Sincroniza estoque e preço de um produto. Retorna [(tipo, status, detalhe), ...]."""
    # RefId buscado uma vez e reaproveitado em estoque e preço
    refid = vtex_fetch_id_info(id_sku) if sku else None
    return [
        ("estoque", *vtex_atualiza_estoque(id_sku, sku, client, refid, estoques_snk)),
        ("preco", *vtex_atualiza_preco_venda(id_sku, sku, client, refid)),
    ]


def main(client):
    inicio = time.time()
    enviar_notificacao_telegram("🚀 Iniciando integração de estoques/preços para o Vtex")

    try:
        ids_skus = vtex_merge_id_sku_dicts()
    except Exception as e:
        logging.error(f"❌ Erro ao obter dicionário id_sku: {e}")
        enviar_notificacao_telegram(f"❌ Erro ao obter dicionário id_sku: {e}")
        raise SystemExit(1)

    # Uma query para todos os estoques; se falhar, cada produto consulta o seu
    estoques_snk = sankhya_fetch_estoques(CODEMP_ESTOQUE, CODLOCAL_ESTOQUE, client)
    if estoques_snk is None:
        logging.warning("⚠️ Estoque em lote indisponível, consultando o Sankhya produto a produto")

    contagem = Counter()
    atualizados, falhas = [], []
    produtos_com_falha = 0

    with ThreadPoolExecutor(max_workers=SYNC_WORKERS) as pool:
        futuros = {
            pool.submit(_processa_produto, id_sku, sku, client, estoques_snk): id_sku
            for id_sku, sku in ids_skus.items()
        }
        for futuro in as_completed(futuros):
            try:
                resultados = futuro.result()
            except Exception as e:
                logging.error(f"❌ Erro inesperado no id {futuros[futuro]}: {e}")
                falhas.append(f"erro inesperado no id {futuros[futuro]}: {e}")
                produtos_com_falha += 1
                continue

            teve_falha = False
            for tipo, status, detalhe in resultados:
                contagem[tipo, status] += 1
                if status == ATUALIZADO:
                    atualizados.append(detalhe)
                elif status == FALHA:
                    falhas.append(detalhe)
                    teve_falha = True
            produtos_com_falha += teve_falha

    duracao_min = (time.time() - inicio) / 60
    logging.info(f"⏱️ Tempo total de execução: {duracao_min:.2f} minutos")

    resumo = _monta_resumo(len(ids_skus), contagem, atualizados, falhas, duracao_min)
    logging.info(resumo)
    enviar_notificacao_telegram(resumo)

    if ids_skus and produtos_com_falha / len(ids_skus) > LIMITE_FALHAS:
        logging.error(f"❌ {produtos_com_falha}/{len(ids_skus)} produtos com falha, acima do limite de {LIMITE_FALHAS:.0%}")
        raise SystemExit(1)


if __name__ == '__main__':
    main(client = SankhyaClient())

    # client = SankhyaClient()
    # vtex_atualiza_preco_venda(541, 547, client)
