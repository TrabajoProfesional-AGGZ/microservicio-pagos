# app/services/pagos_service.py
import asyncio
from datetime import datetime
import mercadopago
from fastapi import HTTPException
from app.schemas.pagos import PagoProcesarRequest, PreferenciaRequest, PreferenciaResponse, WebhookNotification
from app.utils.config import mp_token, ms_club_url
import httpx2
from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.repositories.pagos_repository import PagosRepository
from app.utils.redis import publicar_evento_pago

tareas_en_segundo_plano = set()
class PagosService:
    def __init__(self):
        access_token = mp_token
        self.mp = mercadopago.SDK(access_token)
        
    async def procesar_notificacion_webhook(self, notificacion: WebhookNotification, db: Session) -> dict:
        if notificacion.type != "payment":
            return {"status": "ignorado", "detalle": "No es un evento de pago"}

        id_pago_externo = str(notificacion.data.id)
        respuesta = self.mp.payment().get(id_pago_externo)

        if respuesta["status"] != 200:
            raise HTTPException(status_code=400, detail="No se pudo verificar el pago en MP")

        info_pago = respuesta["response"]
        estado_pago = info_pago["status"]
        monto = info_pago.get("transaction_amount")
        metodo_pago = info_pago.get("payment_method_id")
        
        external_ref = info_pago.get("external_reference")

        id_item_uuid = None
        tipo_item = None
        id_item_str = None

        if external_ref and "|" in external_ref:
            tipo_item, id_item_str = external_ref.split("|")
            try:
                id_item_uuid = UUID(id_item_str)
            except ValueError:
                return {"status": "error", "detalle": "El ID en external_reference no es un UUID válido"}

        pago_existente = PagosRepository.get_pago_by_externo(db, id_pago_externo)
        pago_ya_estaba_aprobado = False
        
        if pago_existente:
            if pago_existente.estado == "approved" and estado_pago == "approved":
                pago_ya_estaba_aprobado = True
            PagosRepository.update_estado_pago(db, pago_existente, estado_pago)
        else:
            PagosRepository.create_pago(
                db=db,
                id_pago_externo=id_pago_externo,
                monto=monto,
                estado=estado_pago,
                id_item=id_item_uuid, # 🚀 Usamos el UUID extraído
                metodo_pago=metodo_pago
            )

        if estado_pago == "approved":
            if pago_ya_estaba_aprobado:
                return {"status": "procesado", "estado": "Ya estaba aprobado previamente", "id_pago": id_pago_externo}
            
            if not id_item_str:
                return {"status": "procesado", "estado": "Aprobado sin ID de referencia"}

            endpoint_interno = "cuotas" if tipo_item == "cuota" else "reservas"

            async with httpx2.AsyncClient() as client:
                try:
                    res = await client.post(
                        f"{ms_club_url}/api/v1/internos/{endpoint_interno}/{id_item_str}/marcar-pagada"
                    )
                    res.raise_for_status()

                    periodo_actual = datetime.now().strftime("%Y-%m")
                    concepto_pago = info_pago.get("description", "Pago Genérico") 
                    
                    payload_evento = {
                        "periodo": periodo_actual,
                        "concepto": concepto_pago,
                        "monto": monto
                    }

                    tarea_redis = asyncio.create_task(publicar_evento_pago(payload_evento))
                    tareas_en_segundo_plano.add(tarea_redis)
                    tarea_redis.add_done_callback(tareas_en_segundo_plano.discard)
                except httpx2.HTTPError as e:
                    print(f"Error crítico: Falló la comunicación con ms-club: {e}")
                    
            return {"status": "procesado", "estado": "Aprobado", "id_pago": id_pago_externo}
        
        elif estado_pago == "rejected":
            return {"status": "procesado", "estado": "Rechazado", "id_pago": id_pago_externo}
        else:
            return {"status": "pendiente", "estado": estado_pago, "id_pago": id_pago_externo}
        
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
            "description": f"Pago de {pago_data.tipo_item} - SocioUnido",
            #(Ej: "cuota|1234-5678-..." o "reserva|1234-5679-...")
            "external_reference": f"{pago_data.tipo_item}|{str(pago_data.id_item)}" 
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