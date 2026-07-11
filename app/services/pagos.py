# app/services/pagos_service.py
import os
import mercadopago
from fastapi import HTTPException
from app.schemas.pagos import PreferenciaRequest, PreferenciaResponse, WebhookNotification
from app.utils.config import mp_token

class PagosService:
    def __init__(self):
        access_token = mp_token
        self.mp = mercadopago.SDK(access_token)

    def crear_preferencia_prueba(self, datos: PreferenciaRequest) -> PreferenciaResponse:
        # Armamos el diccionario tal como lo pide la documentación de Checkout Bricks
        preference_data = {
            "items": [
                {
                    "title": datos.titulo,
                    "quantity": datos.cantidad,
                    "unit_price": datos.precio_unitario
                }
            ],
            # Acá después agregaremos la URL de tu Webhook (back_urls / notification_url)
        }

        # Hacemos la petición real a Mercado Pago
        respuesta = self.mp.preference().create(preference_data)

        # MP devuelve un status 201 si sale todo bien
        if respuesta["status"] == 201:
            return PreferenciaResponse(
                id_preferencia=respuesta["response"]["id"],
                init_point=respuesta["response"]["init_point"]
            )
        else:
            # Si falla (por ej. credenciales inválidas), lanzamos un error
            raise HTTPException(
                status_code=400, 
                detail=f"Error al crear preferencia en MP: {respuesta.get('response')}"
            )
    
    def procesar_notificacion_webhook(self, notificacion: WebhookNotification) -> dict:
        # MP manda notificaciones de varios tipos. Solo nos importan los "pagos"
        if notificacion.type != "payment":
            return {"status": "ignorado", "detalle": "No es un evento de pago"}

        id_pago = notificacion.data.id

        # 1. Consultamos a MP el estado real de este pago
        respuesta = self.mp.payment().get(id_pago)

        if respuesta["status"] != 200:
            raise HTTPException(status_code=400, detail="No se pudo verificar el pago en MP")

        info_pago = respuesta["response"]
        estado_pago = info_pago["status"]
        
        # Opcional: Podés recuperar el ID de tu cuota si lo enviaste en la preferencia (external_reference)
        # external_reference = info_pago.get("external_reference")

        # 2. Lógica de negocio según el estado
        if estado_pago == "approved":
            # ACÁ VA TU LÓGICA DE BASE DE DATOS
            # Ej: cuota_repository.marcar_como_pagada(external_reference)
            return {"status": "procesado", "estado": "Aprobado", "id_pago": id_pago}
        
        elif estado_pago == "rejected":
            return {"status": "procesado", "estado": "Rechazado", "id_pago": id_pago}
        
        else:
            return {"status": "pendiente", "estado": estado_pago, "id_pago": id_pago}