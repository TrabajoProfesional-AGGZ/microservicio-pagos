import json
import redis.asyncio as aioredis
from app.utils.config import REDIS_URL

requires_ssl = REDIS_URL.startswith("rediss://")

# 1. Armamos un diccionario con los parámetros base que funcionan siempre
redis_kwargs = {
    "encoding": "utf-8",
    "decode_responses": True
}

# 2. SOLO agregamos el parámetro SSL si realmente la URL lo pide
if requires_ssl:
    redis_kwargs["ssl_cert_reqs"] = "none"

# 3. Desempaquetamos el diccionario con **
redis_client = aioredis.from_url(REDIS_URL, **redis_kwargs)

import json
import asyncio
from app.utils.redis import redis_client

async def publicar_evento_pago(datos_pago: dict):
    """
    Publica el evento de pago en el canal de Redis de forma asíncrona.
    """
    try:
        canal = "finanzas.pagos"
        mensaje = json.dumps(datos_pago)
        
        await redis_client.publish(canal, mensaje)
        print(f"✅ Evento de pago publicado en {canal}: {datos_pago}")
        
    except Exception as e:
        print(f"❌ Error al publicar evento en Redis: {e}")
