from unittest import mock

import pytest
import requests

import sankhya_api.auth as auth
import sankhya_api.fetch as fetch

PAYLOAD = {"serviceName": "ConsultaProdutosSP.consultaProdutos"}


def resposta(status, body="{}", json_data=None):
    resp = mock.Mock(status_code=status, text=body)
    resp.json.return_value = json_data if json_data is not None else {"ok": 1}
    if status >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(str(status))
    return resp


@pytest.fixture
def sem_espera():
    with mock.patch.object(auth.time, "sleep") as sleep:
        yield sleep


# --- SankhyaClient.post -------------------------------------------------------

def test_post_recupera_apos_500(sankhya_client, sem_espera):
    with mock.patch.object(auth.requests, "post", side_effect=[resposta(500), resposta(200)]):
        assert sankhya_client.post(PAYLOAD) == {"ok": 1}
    assert [c.args[0] for c in sem_espera.call_args_list] == [2]


def test_post_desiste_apos_4_tentativas_com_backoff(sankhya_client, sem_espera):
    with mock.patch.object(auth.requests, "post", side_effect=[resposta(500)] * 4) as post:
        assert sankhya_client.post(PAYLOAD) is None
    assert post.call_count == 4
    assert [c.args[0] for c in sem_espera.call_args_list] == [2, 4, 8]


def test_post_nao_repete_erro_4xx(sankhya_client, sem_espera):
    with mock.patch.object(auth.requests, "post", side_effect=[resposta(400)]) as post:
        assert sankhya_client.post(PAYLOAD) is None
    assert post.call_count == 1


def test_post_recupera_apos_timeout(sankhya_client, sem_espera):
    with mock.patch.object(auth.requests, "post", side_effect=[requests.Timeout("t"), resposta(200)]):
        assert sankhya_client.post(PAYLOAD) == {"ok": 1}


def test_post_renova_token_em_401(sankhya_client, sem_espera):
    with mock.patch.object(auth.requests, "post", side_effect=[resposta(401), resposta(200)]), \
            mock.patch.object(sankhya_client, "_authenticate") as autentica:
        assert sankhya_client.post(PAYLOAD) == {"ok": 1}
    autentica.assert_called_once()


# --- sankhya_fetch_estoques ---------------------------------------------------

def test_estoques_em_lote_soma_por_produto():
    rows = [[410664, 4.0], [438486, 9.0], [438486, 1.0]]
    with mock.patch.object(fetch, "execute_query", return_value=rows) as query:
        assert fetch.sankhya_fetch_estoques(7, 188, None) == {410664: 4, 438486: 10}
    assert "CODEMP = 7 AND CODLOCAL = 188" in query.call_args.args[0]


def test_estoques_em_lote_retorna_none_em_erro():
    with mock.patch.object(fetch, "execute_query", return_value={"error": "boom"}):
        assert fetch.sankhya_fetch_estoques(7, 188, None) is None


# --- sankhya_fetch_preco_venda ------------------------------------------------

def test_preco_venda_extrai_preco_e_promo():
    client = mock.Mock()
    client.post.return_value = {"responseBody": {"produtos": {"produto": {
        "PRECOBASE": {"$": "799.0"}, "Preço_PROMO_1": {"$": "0.00"}}}}}
    assert fetch.sankhya_fetch_preco_venda(417643, client) == ("799.0", "0.00")


def test_preco_venda_nao_repete_quando_post_desiste():
    client = mock.Mock()
    client.post.return_value = None
    assert fetch.sankhya_fetch_preco_venda(417643, client) is None
    assert client.post.call_count == 1
