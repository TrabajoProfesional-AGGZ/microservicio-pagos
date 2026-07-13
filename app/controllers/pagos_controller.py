# app/api/routers/pagos_router.py
from fastapi import APIRouter, Depends
from app.services.pagos_service import PagosService
from app.schemas.pagos import PagoProcesarRequest, PreferenciaRequest, PreferenciaResponse, WebhookNotification

router = APIRouter(prefix="/api/v1/pagos", tags=["Pagos"])

@router.get("/health")
def health_check():
    """Endpoint para verificar que el microservicio está funcionando correctamente."""
    return {"status": "ok", "service": "ms-pagos"}

@router.post("/webhook")
async def recibir_webhook_mercadopago(
    notificacion: WebhookNotification,
    service: PagosService = Depends()
):
    """
    Recibe las notificaciones IPN/Webhooks de Mercado Pago.
    """
    resultado = await service.procesar_notificacion_webhook(notificacion)
    
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