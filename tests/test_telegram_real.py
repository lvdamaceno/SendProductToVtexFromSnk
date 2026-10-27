import pytest

from notifications.telegram import enviar_notificacao_telegram


@pytest.mark.real
def test_envio_telegram_simples():
    mensagem = "🔔 Teste de notificação do projeto SendProductToVtexFromSnk"
    sucesso = enviar_notificacao_telegram(mensagem)
    assert sucesso, "❌ A notificação não foi enviada com sucesso"
