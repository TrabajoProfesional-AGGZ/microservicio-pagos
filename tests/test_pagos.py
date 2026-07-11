# tests/test_pagos.py
import pytest
from unittest.mock import patch
from fastapi import status
from app.main import app 
from app.utils.verify_token import verify_token

# ==========================================
# FIXTURES Y MOCKS
# ==========================================

def mock_verify_token():
    return {"uid": "test_user", "rol": "socio"}

@pytest.fixture(autouse=True)
def override_seguridad():
    """Bypass de la seguridad para los tests."""
    app.dependency_overrides[verify_token] = mock_verify_token
    yield
    app.dependency_overrides = {}

# ==========================================
# TESTS
# ==========================================

# Parcheamos la clase SDK de Mercado Pago directamente donde se importa en el servicio
@patch("app.services.pagos_service.mercadopago.SDK")
def test_crear_preferencia_exito(mock_mp_sdk, client):
    # 1. ARRANGE: Configuramos el comportamiento de mentira de Mercado Pago
    # Simulamos la respuesta JSON que devolvería MP si le pasamos credenciales válidas
    mock_sdk_instance = mock_mp_sdk.return_value
    mock_sdk_instance.preference().create.return_value = {
        "status": 201,
        "response": {
            "id": "123456789-mocked-id",
            "init_point": "https://sandbox.mercadopago.com.ar/checkout/v1/redirect?pref_id=123"
        }
    }

    payload = {
        "titulo": "Cuota Mensual Test",
        "cantidad": 1,
        "precio_unitario": 5000.0
    }

    # 2. ACT: Hacemos la petición a nuestro backend
    response = client.post("/api/v1/pagos/preferencia-test", json=payload)

    # 3. ASSERT: Verificamos que todo responda como esperamos
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["id_preferencia"] == "123456789-mocked-id"
    assert "sandbox.mercadopago" in data["init_point"]
    
    # Validamos que el SDK haya sido llamado exactamente 1 vez con los datos correctos
    mock_sdk_instance.preference().create.assert_called_once()
    argumentos_llamada = mock_sdk_instance.preference().create.call_args[0][0]
    assert argumentos_llamada["items"][0]["title"] == "Cuota Mensual Test"


@patch("app.services.pagos_service.mercadopago.SDK")
def test_crear_preferencia_falla_credenciales(mock_mp_sdk, client):
    # Simulamos que MP rechaza la petición (ej: Access Token inválido)
    mock_sdk_instance = mock_mp_sdk.return_value
    mock_sdk_instance.preference().create.return_value = {
        "status": 401,
        "response": {"message": "Unauthorized"}
    }

    payload = {"titulo": "Error", "cantidad": 1, "precio_unitario": 100}
    response = client.post("/api/v1/pagos/preferencia-test", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Error al crear preferencia" in response.json()["detail"]