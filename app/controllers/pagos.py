# app/api/routers/pagos_router.py
from fastapi import APIRouter, Depends
from app.services.pagos import PagosService
from app.schemas.pagos import PagoProcesarRequest, PreferenciaRequest, PreferenciaResponse, WebhookNotification

router = APIRouter(prefix="/api/v1/pagos", tags=["Pagos"])

@router.post("/preferencia-test", response_model=PreferenciaResponse)
async def crear_preferencia(
    datos: PreferenciaRequest,
    service: PagosService = Depends()
):
    """
    Crea una preferencia de pago en Mercado Pago para probar la conexión.
    """
    return service.crear_preferencia_prueba(datos)

@router.post("/webhook")
async def recibir_webhook_mercadopago(
    notificacion: WebhookNotification,
    service: PagosService = Depends()
):
    """
    Recibe las notificaciones IPN/Webhooks de Mercado Pago.
    """
    resultado = service.procesar_notificacion_webhook(notificacion)
    
    return resultado

@router.post("/procesar")
async def procesar_pago_endpoint(
    request: PagoProcesarRequest,
    service: PagosService = Depends()
):
    """
    Recibe el token de tarjeta desde el Checkout Brick y ejecuta el cobro.
    """
    resultado = service.procesar_pago_tarjeta(request)
    return resultado