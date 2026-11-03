import json
import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("API_KEY_MAESTRA", "clave-test")

from fastapi.testclient import TestClient  # noqa: E402

from app import main  # noqa: E402

RESPUESTA_LLM = {
    "categoria_sugerida": "Soporte Técnico",
    "sentimiento": "Negativo",
    "urgencia": "Alta",
    "idioma": "Español",
    "datos_clave": ["contraseña"],
    "resumen": "No puede acceder a su cuenta",
}
PAYLOAD = {
    "texto_ticket": "No puedo entrar en mi cuenta, la contraseña no funciona.",
    "categorias_disponibles": ["Facturación", "Soporte Técnico", "Ventas", "Otro"],
}


@pytest.fixture
def client(monkeypatch):
    async def falso_create(**kwargs):
        mensaje = SimpleNamespace(content=json.dumps(RESPUESTA_LLM))
        return SimpleNamespace(choices=[SimpleNamespace(message=mensaje)])

    monkeypatch.setattr(main.client.chat.completions, "create", falso_create)
    return TestClient(main.app)


def test_sin_api_key_rechaza(client):
    assert client.post("/api/v1/triage", json=PAYLOAD).status_code in (401, 403)


def test_api_key_incorrecta(client):
    r = client.post("/api/v1/triage", json=PAYLOAD, headers={"X-API-KEY": "mala"})
    assert r.status_code == 403


def test_triaje_correcto(client):
    r = client.post("/api/v1/triage", json=PAYLOAD, headers={"X-API-KEY": "clave-test"})
    assert r.status_code == 200
    assert r.json() == RESPUESTA_LLM
