from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from app.repositories.models import Pago 

class PagosRepository:
    
    @staticmethod
    def get_pago_by_externo(db: Session, id_pago_externo: str) -> Optional[Pago]:
        """Busca si un pago de Mercado Pago ya fue registrado previamente."""
        return db.query(Pago).filter(Pago.id_pago_externo == str(id_pago_externo)).first()

    @staticmethod
    def create_pago(
        db: Session, 
        id_pago_externo: str, 
        monto: float, 
        estado: str, 
        id_item: UUID | None = None, 
        metodo_pago: str | None = None,
        pasarela: str = "MercadoPago"
    ) -> Pago:
        """Crea un nuevo registro de pago en la base de datos."""
        nuevo_pago = Pago(
            id_pago_externo=str(id_pago_externo),
            pasarela=pasarela,
            monto=monto,
            estado=estado,
            id_item=id_item,
            metodo_pago=metodo_pago
        )
        db.add(nuevo_pago)
        db.commit()
        db.refresh(nuevo_pago)
        return nuevo_pago

    @staticmethod
    def update_estado_pago(db: Session, pago: Pago, nuevo_estado: str) -> Pago:
        """Actualiza el estado de un pago existente."""
        pago.estado = nuevo_estado
        db.commit()
        db.refresh(pago)
        return pago