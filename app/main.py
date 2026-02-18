import os
import uvicorn
from fastapi import FastAPI
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Form
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse  
from .database import get_db
from .database import engine
from datetime import datetime
from sqlalchemy.orm import Session
from . import models, schemas
from .models import Base
import time

app = FastAPI()

# Configurar Jinja2 para renderizar plantillas HTML
templates = Jinja2Templates(directory="app/templates")

# Crear las tablas en la base de datos al iniciar la aplicación
# @app.on_event("startup")
# def startup():
#     time.sleep(5)  # Esperar un poco para asegurarse de que la base de datos esté lista
#     Base.metadata.create_all(bind=engine)Sin RENDEL
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

    


# Endpoint de prueba para verificar que la API funciona
@app.get("/")
def home():
    return {"mensaje": "API funcionando correctamente"}

# Crear un nuevo paquete
# @app.post("/paquetes/", response_model=schemas.PaqueteResponse)
# def crear_paquete(paquete: schemas.PaqueteCreate, db: Session = Depends(get_db)):
#     nuevo_paquete = models.Paquete(**paquete.dict())
#     db.add(nuevo_paquete)
#     db.commit()
#     db.refresh(nuevo_paquete)
#     return nuevo_paquete@app.post("/paquetes/", response_model=schemas.PaqueteResponse)
def crear_paquete(paquete: schemas.PaqueteCreate, db: Session = Depends(get_db)):

    paquete_existente = db.query(models.Paquete).filter(
        models.Paquete.numero_seguimiento == paquete.numero_seguimiento
    ).first()

    if paquete_existente:
        raise HTTPException(status_code=400, detail="El número de seguimiento ya existe")

    nuevo_paquete = models.Paquete(**paquete.dict())

    db.add(nuevo_paquete)
    db.commit()
    db.refresh(nuevo_paquete)

    return nuevo_paquete



# Listar todos los paquetes
@app.get("/paquetes/", response_model=list[schemas.PaqueteResponse])
def listar_paquetes(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(models.Paquete)\
        .filter(models.Paquete.activo == True)\
        .offset(skip)\
        .limit(limit)\
        .all()

# Obtener un paquete por ID
@app.get("/paquetes/{paquete_id}", response_model=schemas.PaqueteResponse)
def obtener_paquete(paquete_id: int, db: Session = Depends(get_db)):
    paquete = db.query(models.Paquete).filter(models.Paquete.id == paquete_id).first()
    
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    
    return paquete

# Actualizar un paquete por ID
@app.put("/paquetes/{paquete_id}", response_model=schemas.PaqueteResponse)
def actualizar_paquete(paquete_id: int, paquete_actualizado: schemas.PaqueteCreate, db: Session = Depends(get_db)):
    
    paquete = db.query(models.Paquete).filter(models.Paquete.id == paquete_id).first()
    
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    
    for key, value in paquete_actualizado.dict().items():
        setattr(paquete, key, value)
        
    db.commit()
    db.refresh(paquete)
    
    return paquete

# Vista web para listar paquetes
@app.get("/web/", response_class=HTMLResponse)
def vista_paquetes_web(request: Request, db: Session = Depends(get_db)):
    paquetes = db.query(models.Paquete).filter(models.Paquete.activo == True).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "paquetes": paquetes
})
    
# Vista para editar un paquete
@app.get("/editar/{paquete_id}", response_class=HTMLResponse)
def editar_paquete(paquete_id: int, request: Request, db: Session = Depends(get_db)):
    paquete = db.query(models.Paquete).filter(models.Paquete.id == paquete_id).first()
    return templates.TemplateResponse("editar.html", {
        "request": request,
        "paquete": paquete
    })
    
# Vista web para crear un nuevo paquete
@app.post("/paquetes-web/")
def crear_paquete_web(
    numero_seguimiento: str = Form(...),
    destinatario: str = Form(...),
    peso: int = Form(...),
    fecha_envio: str = Form(...),
    entregado: bool = Form(False),
    db: Session = Depends(get_db)
):
    # Convertir la fecha de envío de string a date
    fecha_convertida = datetime.strptime(fecha_envio, "%Y-%m-%d").date()
    
    nuevo_paquete = models.Paquete(
        numero_seguimiento=numero_seguimiento,
        destinatario=destinatario,
        peso=peso,
        fecha_envio=fecha_envio,
        entregado=entregado
    )
    
    db.add(nuevo_paquete)
    db.commit()
    
    return RedirectResponse(url="/web/", status_code=303)


# Vista para borrar un paquete
@app.get("/borrar/{paquete_id}")
def borrar_paquete(paquete_id: int, db: Session = Depends(get_db)):
    paquete = db.query(models.Paquete).filter(models.Paquete.id == paquete_id).first()
    if paquete:
        db.delete(paquete)
        db.commit()
    return RedirectResponse(url="/web/", status_code=303)

# Eliminar un paquete por ID
@app.delete("/paquetes/{paquete_id}")
def eliminar_paquete(paquete_id: int, db: Session = Depends(get_db)):
    
    paquete = db.query(models.Paquete).filter(models.Paquete.id == paquete_id).first()
    
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    
    # db.delete(paquete)
    paquete.activo = False
    db.commit()
    
    return {"mensaje": "Paquete eliminado correctamente"}
   
   
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Obtener el puerto de la variable de entorno o usar 10000 por defecto
    uvicorn.run(app, host="0.0.0.0", port=port)