from pydantic import BaseModel, Field
from datetime import date, datetime

# class PaqueteBase(BaseModel):
#     numero_seguimiento: str
#     destinatario: str
#     peso: float
#     fecha_envio: date
#     entregado: bool

class PaqueteBase(BaseModel):
    numero_seguimiento: str = Field(..., min_length=3, max_length=50)
    destinatario: str = Field(..., min_length=2, max_length=100)
    peso: int = Field(..., gt=0)
    fecha_envio: date
    entregado: bool
    
class PaqueteCreate(PaqueteBase):
    pass

class PaqueteResponse(PaqueteBase):
    id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True