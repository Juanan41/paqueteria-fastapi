from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime
from datetime import datetime
from .database import Base

class Paquete(Base):
    __tablename__ = "paquetes"

    id = Column(Integer, primary_key=True, index=True)

    numero_seguimiento = Column(String, unique=True, index=True)
    destinatario = Column(String, index=True)

    peso = Column(Integer)

    fecha_envio = Column(Date)

    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    entregado = Column(Boolean, default=False)
    
    activo = Column(Boolean, default=True)
