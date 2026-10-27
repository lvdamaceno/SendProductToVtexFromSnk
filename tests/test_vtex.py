from unittest import mock

import pytest
import requests

import vtex_api.client as client
import vtex_api.fetch as fetch
import vtex_api.processamentos as proc


def resposta(status, json_data=None, text="x"):
    resp = mock.Mock(status_code=status, text=text, content=b"x")
    resp.json.return_value = json_data or {}
    if status >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(str(status))
    return resp


# --- vtex_fetch_preco_venda_sku -----------------------------------------------

def test_preco_vtex_existente():
    with mock.patch.object(client.requests, "request", return_value=resposta(200, {"basePrice": 1899})):
        assert fetch.vtex_fetch_preco_venda_sku(687) == "1899"


def test_preco_vtex_404_significa_sem_preco():
    with mock.patch.object(client.requests, "request", return_value=resposta(404, text="Price not found")):
        assert fetch.vtex_fetch_preco_venda_sku(687) == "0"


def test_preco_vtex_erro_retorna_none():
    with mock.patch.object(client.requests, "request", return_value=resposta(500)):
        assert fetch.vtex_fetch_preco_venda_sku(687) is None


def test_404_continua_sendo_erro_fora_da_consulta_de_preco():
    with mock.patch.object(client.requests, "request", return_value=resposta(404)):
        assert client.vtex_get("catalog/pvt/product/1") is None


# --- vtex_atualiza_estoque ----------------------------------------------------

@pytest.fixture
def estoque_vtex():
    with mock.patch.object(proc, "vtex_fetch_estoque_sku", return_value={"Estoque": 2, "Doca": 0}) as f:
        yield f


def test_estoque_sem_sku_nao_chama_apis(estoque_vtex):
    with mock.patch.object(proc, "vtex_fetch_id_info") as id_info:
        assert proc.vtex_atualiza_estoque(700, [], None) == (proc.SEM_SKU, None)
    id_info.assert_not_called()
    estoque_vtex.assert_not_called()


def test_estoque_usa_lote_sem_consultar_sankhya(estoque_vtex):
    with mock.patch.object(proc, "sankhya_fetch_estoque") as por_produto:
        assert proc.vtex_atualiza_estoque(1, [10], None, "123", {123: 2}) == (proc.OK, None)
    por_produto.assert_not_called()


def test_estoque_ausente_do_lote_vale_zero(estoque_vtex):
    with mock.patch.object(proc, "vtex_send_update_estoque", return_value=True) as envia:
        status, _ = proc.vtex_atualiza_estoque(1, [10], None, "123", {})
    assert status == proc.ATUALIZADO
    envia.assert_called_once_with("123", 10, 0, 2)


def test_estoque_sem_lote_consulta_por_produto(estoque_vtex):
    with mock.patch.object(proc, "sankhya_fetch_estoque", return_value=2) as por_produto:
        assert proc.vtex_atualiza_estoque(1, [10], None, "123") == (proc.OK, None)
    por_produto.assert_called_once_with("123", proc.CODEMP_ESTOQUE, proc.CODLOCAL_ESTOQUE, None)


def test_estoque_sankhya_indisponivel_nao_envia(estoque_vtex):
    with mock.patch.object(proc, "sankhya_fetch_estoque", return_value=None), \
            mock.patch.object(proc, "vtex_send_update_estoque") as envia:
        status, _ = proc.vtex_atualiza_estoque(1, [10], None, "123")
    assert status == proc.FALHA
    envia.assert_not_called()


def test_estoque_falha_no_envio(estoque_vtex):
    with mock.patch.object(proc, "vtex_send_update_estoque", return_value=False):
        status, _ = proc.vtex_atualiza_estoque(1, [10], None, "123", {123: 5})
    assert status == proc.FALHA


# --- vtex_atualiza_preco_venda ------------------------------------------------

@pytest.fixture
def sem_preco_fixo():
    with mock.patch.object(proc, "vtex_create_fixed_price") as f:
        yield f


def test_preco_sankhya_indisponivel(sem_preco_fixo):
    with mock.patch.object(proc, "sankhya_fetch_preco_venda", return_value=None):
        status, _ = proc.vtex_atualiza_preco_venda(1, [10], None, "123")
    assert status == proc.FALHA


def test_preco_vtex_indisponivel_nao_envia(sem_preco_fixo):
    with mock.patch.object(proc, "sankhya_fetch_preco_venda", return_value=("12.0", "0.00")), \
            mock.patch.object(proc, "vtex_fetch_preco_venda_sku", return_value=None), \
            mock.patch.object(proc, "vtex_send_update_preco_venda") as envia:
        status, _ = proc.vtex_atualiza_preco_venda(1, [10], None, "123")
    assert status == proc.FALHA
    envia.assert_not_called()


def test_preco_diferente_e_atualizado(sem_preco_fixo):
    with mock.patch.object(proc, "sankhya_fetch_preco_venda", return_value=("12.0", "0.00")), \
            mock.patch.object(proc, "vtex_fetch_preco_venda_sku", return_value="10"), \
            mock.patch.object(proc, "vtex_send_update_preco_venda", return_value=True) as envia:
        status, detalhe = proc.vtex_atualiza_preco_venda(1, [10], None, "123")
    assert status == proc.ATUALIZADO
    assert "10 → 12.0" in detalhe
    envia.assert_called_once_with("123", 10, "12.0", "10")
    sem_preco_fixo.assert_not_called()


def test_preco_igual_com_promo_cria_preco_fixo(sem_preco_fixo):
    with mock.patch.object(proc, "sankhya_fetch_preco_venda", return_value=("1.0", "0.80")), \
            mock.patch.object(proc, "vtex_fetch_preco_venda_sku", return_value="1"), \
            mock.patch.object(proc, "vtex_send_update_preco_venda") as envia:
        assert proc.vtex_atualiza_preco_venda(1, [10], None, "123") == (proc.OK, None)
    envia.assert_not_called()
    sem_preco_fixo.assert_called_once_with(10, "1.0", "0.80")
