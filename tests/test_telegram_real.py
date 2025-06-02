import sys
import os

# Garante que a raiz do projeto esteja no path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from notifications.telegram import enviar_notificacao_telegram

def test_envio_telegram_simples():
    mensagem = "🔔 Teste de notificação do projeto SendProductToVtexFromSnk"
    sucesso = enviar_notificacao_telegram(mensagem)
    assert sucesso, "❌ A notificação não foi enviada com sucesso"
