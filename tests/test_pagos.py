import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4
from app.main import app 

client = TestClient(app)

# ---------------------------------------------------------
# TEST 1: Procesar pago con tarjeta
# ---------------------------------------------------------
@patch("app.services.pagos_service.mercadopago.SDK")
def test_procesar_pago_tarjeta_exito(mock_sdk):
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
# TEST 2: Webhook - Pago Nuevo Aprobado (Crea registro y avisa al Club)
# ---------------------------------------------------------
@patch("app.services.pagos_service.PagosRepository")
@patch("app.services.pagos_service.httpx2.AsyncClient.post")
@patch("app.services.pagos_service.mercadopago.SDK")
def test_webhook_pago_nuevo_aprobado_llama_al_club(mock_sdk, mock_httpx_post, mock_repo):
    id_cuota_fake = str(uuid4())
    
    # 1. Mock de MP: Agregamos los campos que ahora busca el servicio
    mock_payment = mock_sdk.return_value.payment.return_value
    mock_payment.get.return_value = {
        "status": 200, 
        "response": {
            "status": "approved", 
            "external_reference": id_cuota_fake,
            "transaction_amount": 1500.0,
            "payment_method_id": "credit_card"
        }
    }
    
    # 2. Mock de Repo: Simulamos que el pago NO existe en la base de datos
    mock_repo.get_pago_by_externo.return_value = None
    
    # 3. Mock de HTTP
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
    
    # Verificaciones
    mock_repo.get_pago_by_externo.assert_called_once()
    mock_repo.create_pago.assert_called_once() # Como no existía, debe crearlo
    mock_repo.update_estado_pago.assert_not_called()
    mock_httpx_post.assert_called_once()


# ---------------------------------------------------------
# TEST 3: Webhook - Pago Existente Aprobado (Actualiza registro y avisa al Club)
# ---------------------------------------------------------
@patch("app.services.pagos_service.PagosRepository")
@patch("app.services.pagos_service.httpx2.AsyncClient.post")
@patch("app.services.pagos_service.mercadopago.SDK")
def test_webhook_pago_existente_aprobado_actualiza(mock_sdk, mock_httpx_post, mock_repo):
    id_cuota_fake = str(uuid4())
    
    mock_payment = mock_sdk.return_value.payment.return_value
    mock_payment.get.return_value = {
        "status": 200, 
        "response": {
            "status": "approved", 
            "external_reference": id_cuota_fake,
            "transaction_amount": 1500.0,
            "payment_method_id": "credit_card"
        }
    }
    
    # 2. Mock de Repo: Simulamos que el pago YA existía (ej. estaba en pending)
    mock_pago_existente = MagicMock()
    mock_repo.get_pago_by_externo.return_value = mock_pago_existente
    
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
    
    mock_repo.get_pago_by_externo.assert_called_once()
    mock_repo.create_pago.assert_not_called() # No debe crearlo
    mock_repo.update_estado_pago.assert_called_once_with(mock_repo.get_pago_by_externo.call_args[0][0], mock_pago_existente, "approved")


# ---------------------------------------------------------
# TEST 4: Webhook - Pago Rechazado (Crea/Actualiza pero NO llama al Club)
# ---------------------------------------------------------
@patch("app.services.pagos_service.PagosRepository")
@patch("app.services.pagos_service.httpx2.AsyncClient.post")
@patch("app.services.pagos_service.mercadopago.SDK")
def test_webhook_pago_rechazado_no_llama_al_club(mock_sdk, mock_httpx_post, mock_repo):
    mock_payment = mock_sdk.return_value.payment.return_value
    mock_payment.get.return_value = {
        "status": 200, 
        "response": {
            "status": "rejected",
            "transaction_amount": 5000.0,
            "payment_method_id": "visa"
        }
    }
    
    # Simulamos pago nuevo
    mock_repo.get_pago_by_externo.return_value = None

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
    
    # Verificamos que se guardó el rechazo en nuestra DB
    mock_repo.create_pago.assert_called_once()
    
    # Verificamos que NO se llamó al Club porque el pago no fue aprobado
    mock_httpx_post.assert_not_called()