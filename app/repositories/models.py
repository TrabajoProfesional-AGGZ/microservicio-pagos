import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
# Asegurate de importar tu Base desde donde la tengas definida
from app.repositories.database import Base 

class Pago(Base):
    __tablename__ = "pagos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ID que nos da Mercado Pago (lo guardamos como String por flexibilidad)
    id_pago_externo = Column(String, unique=True, index=True, nullable=False)
    
    pasarela = Column(String, default="MercadoPago", nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    
    # approved, pending, rejected, in_process, etc.
    estado = Column(String, nullable=False) 
    
    # Guardamos a qué cuota corresponde este pago
    id_cuota = Column(UUID(as_uuid=True), index=True, nullable=True) 
    
    # credit_card, account_money, ticket, etc.
    metodo_pago = Column(String, nullable=True) 
    
    fecha_creacion = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )