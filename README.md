
# 📦 SendProductToVtexFromSnk

Este projeto realiza a **integração de produtos da API Sankhya para a VTEX**, permitindo sincronização de dados como estoque e identificação de SKUs entre os dois sistemas.

---

## 🚀 Funcionalidades

- Consulta de produtos e estoques via API Sankhya
- Atualização de estoques diretamente na VTEX via API Logistics
- Autenticação automática em ambos os sistemas
- Registro de logs e notificações via Telegram

---

## 🛠️ Requisitos

- Python 3.9+
- Conta ativa na VTEX com AppKey e AppToken
- Acesso à API Gateway da Sankhya
- Biblioteca `requests`, `python-dotenv`, `logging`, entre outras

---

## 📦 Instalação

1. Clone este repositório:

```bash
git clone https://github.com/seu-usuario/SendProductToVtexFromSnk.git
cd SendProductToVtexFromSnk
```

2. Crie e ative um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate  # no Windows: .venv\Scripts\activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## 🔐 Configuração

Crie um arquivo `.env` na raiz com as seguintes variáveis:

```env
# VTEX
VTEXAPPKEY=seu_app_key_vtex
VTEXAPPTOKEN=seu_app_token_vtex
VTEX_BASE_URL=https://<sualoja>.vtexcommercestable.com.br/api/

# Sankhya
SANKHYA_TOKEN=seu_token
SANKHYA_APPKEY=sua_appkey
SANKHYA_USERNAME=usuario
SANKHYA_PASSWORD=senha

# Ambiente 0 para debug e 1 para produção
APP_ENV=1
```

---

## ▶️ Execução

Para iniciar a integração e atualizar os estoques:

```bash
python main.py
```

---

## 🔔 Notificações

Este projeto envia notificações de status via Telegram.
Configure seu bot em `notifications/telegram.py` com seu token e chat_id.

---

## 🧪 Estrutura do projeto

```
SendProductToVtexFromSnk/
│
├── api_vtex/
│   ├── client.py
│   ├── fetch.py
│   └── processamentos.py
│
├── sankhya_api/
│   └── auth.py
│
├── notifications/
│   └── telegram.py
│
├── utils.py
├── main.py
├── .env.example
└── README.md
```

---

## 📄 Licença

Este projeto é livre para uso interno. Para uso comercial, consulte o autor.
