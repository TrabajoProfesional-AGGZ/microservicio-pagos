from fastapi import Header, HTTPException
from app.utils.config import SHARED_SECRET
from app.utils.config import env

def verify_secret(x_internal_secret: str = Header(None, include_in_schema=False)):
    if env == "development":
        # En desarrollo, permitimos pasar sin el secreto para facilitar pruebas
        return
    
    # Comparamos el header recibido con nuestro secreto
    if x_internal_secret != SHARED_SECRET:
        raise HTTPException(status_code=403, detail="Acceso denegado: Token interno inválido")