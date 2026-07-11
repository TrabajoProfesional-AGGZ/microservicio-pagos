from pydantic import BaseModel

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