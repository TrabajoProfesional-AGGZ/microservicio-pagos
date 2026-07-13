# app/services/pagos_service.py
import os
import mercadopago
from fastapi import HTTPException
from app.schemas.pagos import PagoProcesarRequest, PreferenciaRequest, PreferenciaResponse, WebhookNotification
from app.utils.config import mp_token, ms_club_url
import httpx2
from fastapi import HTTPException

class PagosService:
    def __init__(self):
        access_token = mp_token
        self.mp = mercadopago.SDK(access_token)
        
    async def procesar_notificacion_webhook(self, notificacion: WebhookNotification) -> dict:
        if notificacion.type != "payment":
            return {"status": "ignorado", "detalle": "No es un evento de pago"}

        id_pago = notificacion.data.id

        respuesta = self.mp.payment().get(id_pago)

        if respuesta["status"] != 200:
            raise HTTPException(status_code=400, detail="No se pudo verificar el pago en MP")

        info_pago = respuesta["response"]
        estado_pago = info_pago["status"]
        
        id_cuota = info_pago.get("external_reference")

        if estado_pago == "approved":
            if not id_cuota:
                return {"status": "procesado", "estado": "Aprobado sin ID de cuota"}

            async with httpx2.AsyncClient() as client:
                try:
                    res = await client.post(
                        f"{ms_club_url}/api/v1/internos/cuotas/{id_cuota}/marcar-pagada"
                    )
                    res.raise_for_status()
                except httpx2.HTTPError as e:
                    print(f"Error crítico: Falló la comunicación con ms-club: {e}")
                    
            return {"status": "procesado", "estado": "Aprobado", "id_pago": id_pago}
        
        elif estado_pago == "rejected":
            return {"status": "procesado", "estado": "Rechazado", "id_pago": id_pago}
        
        else:
            return {"status": "pendiente", "estado": estado_pago, "id_pago": id_pago}
        
    def procesar_pago_tarjeta(self, pago_data: PagoProcesarRequest) -> dict:
        # 1. Armamos el diccionario agregando external_reference
        payment_data = {
            "transaction_amount": pago_data.transaction_amount,
            "token": pago_data.token,
            "installments": pago_data.installments,
            "payment_method_id": pago_data.payment_method_id,
            "issuer_id": pago_data.issuer_id,
            "payer": {
                "email": pago_data.payer.email,
                "identification": pago_data.payer.identification
            },
            "description": "Pago de cuota societaria - SocioUnido",
            "external_reference": str(pago_data.id_cuota) 
        }

        # 2. Le pedimos a Mercado Pago que procese el pago
        respuesta = self.mp.payment().create(payment_data)

        # 3. Validamos la respuesta
        if respuesta["status"] not in [200, 201]:
            # Si MP rechaza la petición (ej. token vencido o datos mal armados)
            raise HTTPException(
                status_code=400, 
                detail=f"Error al procesar el pago: {respuesta.get('response', 'Desconocido')}"
            )

        info_pago = respuesta["response"]
        
        # 4. Devolvemos el estado del pago al frontend
        # Puede ser "approved" (aprobado), "in_process" (en revisión) o "rejected" (rechazado)
        return {
            "id_pago": info_pago["id"],
            "estado": info_pago["status"],
            "estado_detalle": info_pago["status_detail"]
        }