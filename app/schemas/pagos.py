from pydantic import BaseModel, UUID4
from typing import Optional
from decimal import Decimal
class PreferenciaRequest(BaseModel):
    titulo: str
    cantidad: int
    precio_unitario: float

class PreferenciaResponse(BaseModel):
    id_preferencia: str
    init_point: str # Esta es la URL a la que mandamos al frontend

class DataNotificacion(BaseModel):
    id: str

class WebhookNotification(BaseModel):
    action: str
    api_version: str
    data: DataNotificacion
    date_created: str
    id: int
    live_mode: bool
    type: str
    user_id: int

class Payer(BaseModel):
    email: str
    identification: Optional[dict] = None

class PagoProcesarRequest(BaseModel):
    token: str
    transaction_amount: float
    installments: int
    payment_method_id: str
    issuer_id: Optional[str] = None
    payer: Payer
    id_cuota: UUID4