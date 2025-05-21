import logging

import requests
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

logging.basicConfig(
    level=logging.INFO,  # ou DEBUG se quiser mais detalhes
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# Função para enviar notificação para o Telegram
def enviar_notificacao_telegram(mensagem):
    token = os.getenv('BOTTOKEN')  # Seu Token do Bot
    chat_id = os.getenv('CHATID')  # O chat_id do destinatário
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Dados a serem enviados
    payload = {
        'chat_id': chat_id,
        'text': mensagem,
        'parse_mode': 'Markdown'
    }

    # Enviar a requisição para o Telegram
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            logging.info("Notificação enviada com sucesso!")
        else:
            logging.warning(f"Falha ao enviar notificação: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ocorreu um erro: {e}")


