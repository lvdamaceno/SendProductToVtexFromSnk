import os
import sys
import threading
from unittest import mock

import pytest

# Garante que a raiz do projeto esteja no path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# vtex_api.client exige as credenciais já no import
os.environ.setdefault("VTEXAPPKEY", "test-key")
os.environ.setdefault("VTEXAPPTOKEN", "test-token")


@pytest.fixture
def sankhya_client():
    """SankhyaClient sem login real, com token válido."""
    from sankhya_api.auth import SankhyaClient

    client = object.__new__(SankhyaClient)
    client.token = "token"
    client.token_expiry = float("inf")
    client.headers = {}
    client.timeout = 1
    client._lock = threading.Lock()
    return client


def pytest_configure(config):
    config.addinivalue_line("markers", "real: chama APIs reais (só roda com RUN_REAL_TESTS=1)")


def pytest_collection_modifyitems(config, items):
    if os.getenv("RUN_REAL_TESTS") == "1":
        return
    pular = pytest.mark.skip(reason="chama APIs reais; use RUN_REAL_TESTS=1")
    for item in items:
        if "real" in item.keywords:
            item.add_marker(pular)


@pytest.fixture(autouse=True)
def sem_telegram(request):
    """Nenhum teste com mocks deve enviar mensagens de verdade."""
    if request.node.get_closest_marker("real"):
        yield None
        return
    with mock.patch("notifications.telegram.requests.post") as post:
        post.return_value.status_code = 200
        yield post
