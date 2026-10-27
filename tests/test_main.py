from unittest import mock

import pytest

import main
from vtex_api.processamentos import ATUALIZADO, FALHA, OK, SEM_SKU


@pytest.fixture
def integracao():
    """main() com VTEX/Sankhya simulados; cada teste define o retorno por produto."""
    with mock.patch.object(main, "vtex_merge_id_sku_dicts") as ids, \
            mock.patch.object(main, "sankhya_fetch_estoques", return_value={}) as estoques, \
            mock.patch.object(main, "vtex_fetch_id_info", side_effect=lambda i: f"ref{i}") as id_info, \
            mock.patch.object(main, "vtex_atualiza_estoque") as estoque, \
            mock.patch.object(main, "vtex_atualiza_preco_venda") as preco, \
            mock.patch.object(main, "enviar_notificacao_telegram") as telegram:
        yield mock.Mock(ids=ids, estoques=estoques, id_info=id_info, estoque=estoque, preco=preco,
                        telegram=telegram)


def _resumo(integracao):
    return integracao.telegram.call_args_list[-1].args[0]


def test_resumo_e_sucesso_abaixo_do_limite(integracao):
    integracao.ids.return_value = {i: [i] for i in range(1, 11)}
    integracao.estoque.side_effect = lambda id_sku, *a: (ATUALIZADO, "Codprod 1: estoque 0 → 5") if id_sku == 1 else (OK, None)
    integracao.preco.side_effect = lambda id_sku, *a: (FALHA, "preço Sankhya indisponível para Codprod 2") if id_sku == 2 else (OK, None)

    main.main(None)  # 1/10 com falha: não sai com erro

    resumo = _resumo(integracao)
    assert "Produtos: 10" in resumo
    assert "Codprod 1: estoque 0 → 5" in resumo
    assert "preço Sankhya indisponível para Codprod 2" in resumo
    assert integracao.id_info.call_count == 10  # RefId uma vez por produto


def test_sai_com_erro_acima_do_limite(integracao):
    integracao.ids.return_value = {1: [1], 2: [2], 3: [3]}
    integracao.estoque.return_value = (OK, None)
    integracao.preco.return_value = (FALHA, "falha")

    with pytest.raises(SystemExit) as erro:
        main.main(None)
    assert erro.value.code == 1


def test_estoque_em_lote_e_repassado(integracao):
    integracao.ids.return_value = {1: [1]}
    integracao.estoques.return_value = {111: 3}
    integracao.estoque.return_value = (OK, None)
    integracao.preco.return_value = (OK, None)

    main.main(None)

    integracao.estoque.assert_called_once_with(1, [1], None, "ref1", {111: 3})


def test_produto_sem_sku_nao_busca_refid(integracao):
    integracao.ids.return_value = {1: []}
    integracao.estoque.return_value = (SEM_SKU, None)
    integracao.preco.return_value = (SEM_SKU, None)

    main.main(None)

    integracao.id_info.assert_not_called()
    assert "Sem SKU: 1" in _resumo(integracao)


def test_excecao_inesperada_conta_como_falha(integracao):
    integracao.ids.return_value = {1: [1]}
    integracao.estoque.side_effect = RuntimeError("boom")

    with pytest.raises(SystemExit):
        main.main(None)
    assert "erro inesperado no id 1: boom" in _resumo(integracao)


def test_resumo_limita_detalhes():
    itens = [f"item {i}" for i in range(main.MAX_DETALHES + 5)]
    linhas = main._secao("Falhas", itens)
    assert linhas[-1] == "• ... e mais 5"
    assert len(linhas) == main.MAX_DETALHES + 2
