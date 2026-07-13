import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4
from app.main import app # Asegúrate de que esta sea tu instancia de FastAPI

client = TestClient(app)

# ---------------------------------------------------------
# TEST 1: Procesar pago con tarjeta
# ---------------------------------------------------------
@patch("app.services.pagos_service.mercadopago.SDK")
def test_procesar_pago_tarjeta_exito(mock_sdk):
    # Configurar el mock de Mercado Pago
    mock_payment = mock_sdk.return_value.payment.return_value
    mock_payment.create.return_value = {
        "status": 201,
        "response": {"id": 12345, "status": "approved", "status_detail": "accredited"}
    }
    id_cuota_fake = str(uuid4())
    payload = {
        "token": "card_token_123",
        "transaction_amount": 5000.0,
        "installments": 1,
        "payment_method_id": "visa",
        "payer": {"email": "test@test.com"},
        "id_cuota": id_cuota_fake
    }

    response = client.post("/api/v1/pagos/procesar", json=payload)
    
    assert response.status_code == 200
    assert response.json()["estado"] == "approved"
    mock_payment.create.assert_called_once()

# ---------------------------------------------------------
# TEST 2: Webhook - Pago Aprobado (debe llamar al Club)
# ---------------------------------------------------------
@patch("app.services.pagos_service.httpx2.AsyncClient.post")
@patch("app.services.pagos_service.mercadopago.SDK")
def test_webhook_pago_aprobado_llama_al_club(mock_sdk, mock_httpx_post):
    # Mock de MP: Retorna estado aprobado y un external_reference (ID Cuota)
    id_cuota_fake = str(uuid4())
    mock_payment = mock_sdk.return_value.payment.return_value
    mock_payment.get.return_value = {
        "status": 200, 
        "response": {"status": "approved", "external_reference": id_cuota_fake}
    }
    
    # Mock de HTTP: Simula respuesta exitosa del ms-club
    mock_httpx_post.return_value.status_code = 200

    webhook_payload = {
        "action": "payment.updated",
        "api_version": "v1",
        "data": {"id": "123456"},
        "date_created": "2026-07-13T00:00:00Z",
        "id": 123456,
        "live_mode": True,
        "type": "payment",
        "user_id": 999
    }

    response = client.post("/api/v1/pagos/webhook", json=webhook_payload)
    
    assert response.status_code == 200
    # Verificamos que se intentó avisar al Club
    mock_httpx_post.assert_called_once()
    assert id_cuota_fake in mock_httpx_post.call_args[0][0]

# ---------------------------------------------------------
# TEST 3: Webhook - Pago Rechazado (no debe llamar al Club)
# ---------------------------------------------------------
@patch("app.services.pagos_service.httpx2.AsyncClient.post")
@patch("app.services.pagos_service.mercadopago.SDK")
def test_webhook_pago_rechazado_no_llama_al_club(mock_sdk, mock_httpx_post):
    # Mock de MP: Retorna estado rechazado
    mock_payment = mock_sdk.return_value.payment.return_value
    mock_payment.get.return_value = {
        "status": 200, 
        "response": {"status": "rejected"}
    }
    
    webhook_payload = {
        "action": "payment.updated",
        "api_version": "v1",
        "data": {"id": "123456"},
        "date_created": "2026-07-13T00:00:00Z",
        "id": 123456,
        "live_mode": True,
        "type": "payment",
        "user_id": 999
    }

    response = client.post("/api/v1/pagos/webhook", json=webhook_payload)
    
    assert response.status_code == 200
    # Verificamos que NO se llamó al Club porque el pago no fue aprobado
    mock_httpx_post.assert_not_called()