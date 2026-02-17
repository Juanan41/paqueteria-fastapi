1️⃣ CREACIÓN DEL PROYECTO DESDE CERO HASTA FUNCIONANDO EN DOCKER
📌 1. Crear la carpeta del proyecto

Abrir PowerShell y ejecutar:

mkdir Paqueteria
cd Paqueteria

📌 2. Crear entorno virtual
python -m venv venv


Activar entorno virtual:

venv\Scripts\activate


Si está activado verás:

(venv)


al inicio de la línea.

📌 3. Crear archivo requirements.txt

Crear el archivo:

notepad requirements.txt


Pegar dentro:

fastapi
uvicorn
sqlalchemy
pydantic
python-dotenv
psycopg2-binary
jinja2
python-multipart


Guardar y cerrar.

Instalar dependencias:

pip install -r requirements.txt

📌 4. Crear estructura del proyecto

Crear carpeta principal de aplicación:

mkdir app


Dentro de app crear archivos:

mi_proyecto_fastapi/
│
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── templates/
│   │   └── index.html
│
├── .env
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md


📌 5. Crear archivo .env

En la raíz del proyecto:

notepad .env


Contenido:

DATABASE_URL=postgresql://postgres:postgres@db:5432/institutos


Guardar.

📌 6. Crear database.py

Contenido:

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

📌 7. Crear models.py (modelo obligatorio con Date, DateTime, Boolean)

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


Este modelo incluye:

Integer
String
Date
DateTime
Boolean
(Requisito obligatorio cumplido)

📌 8. Crear main.py correctamente

⚠ IMPORTANTE: crear tablas en evento startup

from fastapi import FastAPI
from .database import engine
from .models import Base

app = FastAPI()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {"mensaje": "API funcionando correctamente"}

📌 9. Crear Dockerfile

En la raíz:

notepad Dockerfile


Contenido:

FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

📌 10. Crear docker-compose.yml
notepad docker-compose.yml


Contenido:

services:

  db:
    image: postgres:15
    container_name: postgres_db
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: institutos
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    container_name: fastapi_app
    depends_on:
      - db
    ports:
      - "8000:8000"
    env_file:
      - .env

volumes:
  postgres_data:


⚠ No se expone el puerto 5432 para evitar conflictos.

📌 11. Levantar el proyecto

Desde la raíz:

docker compose down
docker compose up --build

📌 12. Comprobar funcionamiento

Abrir navegador:

http://localhost:8000


Debe mostrar:

{"mensaje":"API funcionando correctamente"}

✅ Estado final del Paso 1

En este punto tenemos:

Proyecto estructurado correctamente
Entorno virtual creado
Dependencias instaladas
PostgreSQL funcionando en Docker
FastAPI funcionando en Docker
Conexión correcta mediante .env
Tabla creada automáticamente
Modelo con Date, DateTime y Boolean
Arquitectura lista para continuar

# ###############################################
2️⃣ CREACIÓN DE SCHEMAS Y PRIMER CRUD (CREATE + READ)
🎯 Objetivo del Paso 2

En este punto vamos a:

Crear los schemas con Pydantic

Separar correctamente modelo y respuesta

Crear el endpoint POST (Create)

Crear el endpoint GET (Read - listar todos)

Probar en Swagger

Confirmar que guarda en PostgreSQL

📌 1. ¿Por qué necesitamos Schemas?

En FastAPI:

models.py → define cómo se guarda en la base de datos

schemas.py → define cómo entran y salen los datos por la API

⚠ Nunca se devuelve directamente el modelo SQLAlchemy.

Siempre usamos schemas.

📌 2. Crear archivo schemas.py

Ruta:

app/schemas.py


Contenido completo:

from pydantic import BaseModel
from datetime import date, datetime


# ---------------------------
# Schema base
# ---------------------------
class PaqueteBase(BaseModel):
    numero_seguimiento: str
    destinatario: str
    peso: int
    fecha_envio: date
    entregado: bool


# ---------------------------
# Schema para crear
# ---------------------------
class PaqueteCreate(PaqueteBase):
    pass


# ---------------------------
# Schema para respuesta
# ---------------------------
class PaqueteResponse(PaqueteBase):
    id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True

📌 3. Explicación de cada Schema
🔹 PaqueteBase

Contiene los campos obligatorios:

numero_seguimiento → String

destinatario → String

peso → Integer

fecha_envio → Date

entregado → Boolean

🔹 PaqueteCreate

Se usa cuando creamos un paquete.

Hereda todo de PaqueteBase.

🔹 PaqueteResponse

Se usa cuando devolvemos datos al cliente.

Incluye:

id

fecha_creacion (DateTime automático)

El parámetro:

from_attributes = True


Permite convertir objetos SQLAlchemy en JSON.

📌 4. Modificar main.py para añadir CRUD

Abrir:

app/main.py


Añadir estos imports arriba:

from fastapi import Depends
from sqlalchemy.orm import Session
from .database import get_db
from . import models, schemas


El archivo completo debe quedar así:

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import engine, get_db
from .models import Base
from . import models, schemas

app = FastAPI()


# Crear tablas cuando arranca la aplicación
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


# Ruta principal
@app.get("/")
def home():
    return {"mensaje": "API funcionando correctamente"}


# ---------------------------
# CREATE - Crear paquete
# ---------------------------
@app.post("/paquetes/", response_model=schemas.PaqueteResponse)
def crear_paquete(paquete: schemas.PaqueteCreate, db: Session = Depends(get_db)):
    nuevo_paquete = models.Paquete(**paquete.dict())
    db.add(nuevo_paquete)
    db.commit()
    db.refresh(nuevo_paquete)
    return nuevo_paquete


# ---------------------------
# READ - Listar todos
# ---------------------------
@app.get("/paquetes/", response_model=list[schemas.PaqueteResponse])
def listar_paquetes(db: Session = Depends(get_db)):
    return db.query(models.Paquete).all()

📌 5. Explicación del endpoint POST
@app.post("/paquetes/")


Recibe datos en formato JSON.

paquete: schemas.PaqueteCreate


Valida automáticamente los datos.

db: Session = Depends(get_db)


Inyecta la conexión a la base de datos.

Proceso interno:

Crea objeto SQLAlchemy

Lo añade a la sesión

Hace commit

Refresca objeto

Lo devuelve como JSON

📌 6. Explicación del endpoint GET
@app.get("/paquetes/")


Devuelve una lista.

response_model=list[schemas.PaqueteResponse]


FastAPI transforma cada objeto SQLAlchemy en JSON automáticamente.

📌 7. Reconstruir contenedores

Desde la raíz del proyecto ejecutar:

docker compose down
docker compose up --build


Esperar a que termine.

📌 8. Probar en Swagger

Abrir navegador:

http://localhost:8000/docs

🔹 Probar CREATE

Seleccionar:

POST /paquetes/

Click en Try it out

Ejemplo de prueba:

{
  "numero_seguimiento": "PKT001",
  "destinatario": "Juan",
  "peso": 5,
  "fecha_envio": "2026-02-17",
  "entregado": false
}


Click en Execute.

Debe devolver algo similar a:

{
  "numero_seguimiento": "PKT001",
  "destinatario": "Juan",
  "peso": 5,
  "fecha_envio": "2026-02-17",
  "entregado": false,
  "id": 1,
  "fecha_creacion": "2026-02-17T15:30:00"
}

🔹 Probar GET

Seleccionar:

GET /paquetes/

Execute.

Debe devolver lista con los paquetes creados.

✅ Estado final del Paso 2

En este punto tenemos:

✔ Schemas creados correctamente
✔ Separación modelo / schema
✔ Endpoint POST funcionando
✔ Endpoint GET funcionando
✔ Persistencia real en PostgreSQL
✔ Validación automática con Pydantic
✔ Respuesta estructurada
✔ Swagger operativo

# #################################################
3️⃣ CRUD COMPLETO (GET por ID, UPDATE, DELETE) + MANEJO DE ERRORES
🎯 Objetivo del Paso 3

En este paso completamos la API añadiendo:

Obtener un paquete por ID

Actualizar un paquete

Eliminar un paquete

Manejo correcto de errores (404)

Buenas prácticas en FastAPI

Al finalizar este paso tendremos un CRUD completo funcional.

📌 1. Añadir HTTPException

Abrir:

app/main.py


Añadir en los imports:

from fastapi import HTTPException


Esto nos permitirá lanzar errores personalizados.

📌 2. READ - Obtener paquete por ID

Añadir el siguiente endpoint debajo del GET que lista todos:

# ---------------------------
# READ - Obtener por ID
# ---------------------------
@app.get("/paquetes/{paquete_id}", response_model=schemas.PaqueteResponse)
def obtener_paquete(paquete_id: int, db: Session = Depends(get_db)):
    paquete = db.query(models.Paquete).filter(models.Paquete.id == paquete_id).first()
    
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    
    return paquete

🔎 Explicación

Recibe el ID desde la URL.

Busca el paquete en la base de datos.

Si no existe → devuelve error 404.

Si existe → lo devuelve en formato JSON.

📌 3. UPDATE - Modificar paquete

Añadir debajo:

# ---------------------------
# UPDATE - Modificar paquete
# ---------------------------
@app.put("/paquetes/{paquete_id}", response_model=schemas.PaqueteResponse)
def actualizar_paquete(paquete_id: int, datos: schemas.PaqueteCreate, db: Session = Depends(get_db)):
    
    paquete = db.query(models.Paquete).filter(models.Paquete.id == paquete_id).first()

    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")

    for key, value in datos.dict().items():
        setattr(paquete, key, value)

    db.commit()
    db.refresh(paquete)

    return paquete

🔎 Explicación

Busca el paquete por ID.

Si no existe → error 404.

Recorre los campos recibidos.

Usa setattr() para actualizar dinámicamente.

Guarda los cambios en la base de datos.

Uso profesional y limpio.

📌 4. DELETE - Eliminar paquete

Añadir debajo:

# ---------------------------
# DELETE - Eliminar paquete
# ---------------------------
@app.delete("/paquetes/{paquete_id}")
def eliminar_paquete(paquete_id: int, db: Session = Depends(get_db)):
    
    paquete = db.query(models.Paquete).filter(models.Paquete.id == paquete_id).first()

    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")

    db.delete(paquete)
    db.commit()

    return {"mensaje": "Paquete eliminado correctamente"}

🔎 Explicación

Busca el paquete.

Si no existe → error 404.

Si existe → lo elimina.

Confirma con commit.

Devuelve mensaje de éxito.

📌 5. Reconstruir contenedores

Después de modificar el código ejecutar:

docker compose down
docker compose up --build


Esperar a que termine la construcción.

📌 6. Probar en Swagger

Abrir navegador:

http://localhost:8000/docs


Ahora deben aparecer los siguientes endpoints:

POST /paquetes/

GET /paquetes/

GET /paquetes/{id}

PUT /paquetes/{id}

DELETE /paquetes/{id}

📌 7. Pruebas recomendadas
🔹 Probar GET por ID

Probar con un ID existente:

/paquetes/1


Si no existe debe devolver:

{
  "detail": "Paquete no encontrado"
}

🔹 Probar UPDATE

Ejemplo:

{
  "numero_seguimiento": "PKT001",
  "destinatario": "Maria",
  "peso": 10,
  "fecha_envio": "2026-02-20",
  "entregado": true
}

🔹 Probar DELETE

Eliminar un ID existente.

Luego probar GET por ese ID → debe devolver error 404.

✅ Estado final del Paso 3

En este punto la aplicación tiene:

✔ CRUD completo
✔ Manejo de errores con HTTPException
✔ Validación automática con Pydantic
✔ Persistencia real en PostgreSQL
✔ API REST estructurada correctamente
✔ Docker funcionando
✔ Separación modelo / schema correcta

# ######################################################################
4️⃣ VALIDACIONES AVANZADAS + CONTROL DE DUPLICADOS + SOFT DELETE + PAGINACIÓN
🎯 Objetivo del Paso 4

En este paso mejoramos la API para que sea más profesional y robusta:

Añadir validaciones avanzadas con Pydantic

Evitar números de seguimiento duplicados

Implementar Soft Delete (borrado lógico)

Añadir paginación en los listados

Resolver el problema de sincronización con Docker

📌 1. Añadir validaciones avanzadas en Schemas

Abrir:

app/schemas.py


Modificar la clase PaqueteBase de la siguiente forma:

from pydantic import BaseModel, Field
from datetime import date, datetime


class PaqueteBase(BaseModel):
    numero_seguimiento: str = Field(..., min_length=3, max_length=50)
    destinatario: str = Field(..., min_length=2, max_length=100)
    peso: int = Field(..., gt=0)
    fecha_envio: date
    entregado: bool

🔎 Explicación

min_length → mínimo de caracteres permitidos.

max_length → máximo de caracteres permitidos.

gt=0 → el peso debe ser mayor que 0.

Si se envía:

"peso": -5


FastAPI devolverá error automáticamente (validación automática de Pydantic).

📌 2. Control de duplicados (numero_seguimiento único)

Modificar el endpoint POST en main.py.

Buscar:

@app.post("/paquetes/")


Reemplazar por:

@app.post("/paquetes/", response_model=schemas.PaqueteResponse)
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

🔎 Explicación

Antes de insertar:

Se consulta si ya existe ese número de seguimiento.

Si existe → error 400.

Si no existe → se crea normalmente.

Esto evita duplicados a nivel aplicación.

📌 3. Implementar Soft Delete (Borrado Lógico)

En lugar de eliminar físicamente el registro,
vamos a añadir un campo adicional en el modelo.

Abrir:

app/models.py


Añadir dentro de la clase Paquete:

activo = Column(Boolean, default=True)


Modelo actualizado (parte relevante):

entregado = Column(Boolean, default=False)
activo = Column(Boolean, default=True)

⚠ Importante

Al modificar el modelo es necesario reconstruir completamente la base:

docker compose down -v
docker compose up --build


El parámetro -v elimina el volumen y recrea la base de datos.

📌 4. Modificar DELETE para Soft Delete

Reemplazar el endpoint DELETE por:

@app.delete("/paquetes/{paquete_id}")
def eliminar_paquete(paquete_id: int, db: Session = Depends(get_db)):

    paquete = db.query(models.Paquete).filter(models.Paquete.id == paquete_id).first()

    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")

    paquete.activo = False
    db.commit()

    return {"mensaje": "Paquete desactivado correctamente"}

🔎 Explicación

No se elimina el registro.

Solo se cambia activo = False.

Se conserva historial en base de datos.

Esto es práctica profesional.

📌 5. Modificar GET para mostrar solo activos + paginación

Modificar el endpoint que lista todos:

@app.get("/paquetes/", response_model=list[schemas.PaqueteResponse])
def listar_paquetes(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(models.Paquete)\
             .filter(models.Paquete.activo == True)\
             .offset(skip)\
             .limit(limit)\
             .all()

🔎 Explicación

skip → número de registros a saltar.

limit → número máximo de resultados.

Solo muestra paquetes activos.

Implementa paginación básica.

Ejemplo de uso:

/paquetes/?skip=0&limit=5

📌 6. Resolver problema de sincronización Docker

Cuando se usa:

docker compose down -v


PostgreSQL tarda más en arrancar.

Para evitar error "Connection refused", modificar el evento startup en main.py.

Añadir:

import time


Y modificar el startup:

@app.on_event("startup")
def startup():
    time.sleep(5)
    Base.metadata.create_all(bind=engine)

🔎 Explicación

Docker depends_on no garantiza que la base esté lista.

El sleep(5) da tiempo a PostgreSQL a arrancar antes de crear tablas.

Soluciona el error de conexión.

📌 7. Reconstrucción final

Después de todos los cambios:

docker compose down -v
docker compose up --build

📌 8. Pruebas recomendadas
🔹 Crear paquete con peso negativo

Debe devolver error automático.

🔹 Crear paquete con número duplicado

Debe devolver error 400.

🔹 Eliminar paquete

Debe marcar activo = False.

🔹 Listar paquetes

Solo deben aparecer los activos.

🔹 Probar paginación
/paquetes/?skip=0&limit=2

✅ Estado Final del Paso 4

La API ahora tiene:

✔ Validaciones avanzadas
✔ Control de duplicados
✔ Soft delete
✔ Paginación
✔ Manejo correcto de errores
✔ Sincronización estable con Docker
✔ Arquitectura profesional

# #####################################################################
5️⃣ FRONTEND CON JINJA2 (VISTAS WEB + FORMULARIOS)
🎯 Objetivo del Paso 5.1

Convertir nuestra API en una aplicación web completa:

Mostrar paquetes en una página HTML

Crear paquetes desde formulario

Integrar Jinja2

Usar python-multipart

Mantener API REST funcionando

📌 1. Crear estructura de templates

Dentro de app/ crear:

app/templates/


Si no existe:

mkdir app\templates

📌 2. Configurar Jinja2 en main.py

Abrir app/main.py.

Añadir imports arriba:

from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse


Después de crear app = FastAPI(), añadir:

templates = Jinja2Templates(directory="app/templates")

📌 3. Crear vista HTML principal

Crear archivo:

app/templates/index.html


Contenido:

<!DOCTYPE html>
<html>
<head>
    <title>Paquetería</title>
</head>
<body>
    <h1>Lista de Paquetes</h1>

    <table border="1">
        <tr>
            <th>ID</th>
            <th>Número</th>
            <th>Destinatario</th>
            <th>Peso</th>
            <th>Fecha Envío</th>
            <th>Entregado</th>
        </tr>
        {% for paquete in paquetes %}
        <tr>
            <td>{{ paquete.id }}</td>
            <td>{{ paquete.numero_seguimiento }}</td>
            <td>{{ paquete.destinatario }}</td>
            <td>{{ paquete.peso }}</td>
            <td>{{ paquete.fecha_envio }}</td>
            <td>{{ paquete.entregado }}</td>
        </tr>
        {% endfor %}
    </table>

    <h2>Crear nuevo paquete</h2>

    <form action="/paquetes-web/" method="post">
        <label>Número seguimiento:</label>
        <input type="text" name="numero_seguimiento" required><br>

        <label>Destinatario:</label>
        <input type="text" name="destinatario" required><br>

        <label>Peso:</label>
        <input type="number" name="peso" required><br>

        <label>Fecha envío:</label>
        <input type="date" name="fecha_envio" required><br>

        <label>Entregado:</label>
        <input type="checkbox" name="entregado"><br>

        <button type="submit">Crear</button>
    </form>

</body>
</html>

📌 4. Crear ruta web para mostrar paquetes

Añadir en main.py:

# ---------------------------
# VISTA WEB - Listar paquetes
# ---------------------------
@app.get("/web/", response_class=HTMLResponse)
def vista_paquetes(request: Request, db: Session = Depends(get_db)):
    paquetes = db.query(models.Paquete).filter(models.Paquete.activo == True).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "paquetes": paquetes
    })

📌 5. Crear ruta web para crear desde formulario

Añadir en main.py:

from fastapi import Form

# ---------------------------
# VISTA WEB - Crear paquete
# ---------------------------
@app.post("/paquetes-web/")
def crear_paquete_web(
    numero_seguimiento: str = Form(...),
    destinatario: str = Form(...),
    peso: int = Form(...),
    fecha_envio: str = Form(...),
    entregado: bool = Form(False),
    db: Session = Depends(get_db)
):

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


Añadir import arriba:

from fastapi.responses import RedirectResponse

📌 6. Reconstruir contenedores
docker compose down
docker compose up --build

📌 7. Probar en navegador

Ir a:

http://localhost:8000/web/


Debe aparecer:

Tabla de paquetes

Formulario funcional

Al enviar → redirige a la lista

✅ Estado final del Paso 5.1

Ahora el proyecto tiene:

✔ API REST funcional
✔ Frontend con Jinja2
✔ Formulario HTML real
✔ Integración con base de datos
✔ Docker funcionando
✔ Backend + Frontend en una sola app

# #################################################
📦 PASO 5.1 — Frontend Profesional con Jinja2 + CRUD Completo
🎯 Objetivo de este paso

Convertir la interfaz web básica en una aplicación profesional con:

✅ Diseño con Bootstrap

✅ Placeholders claros en todos los campos

✅ Tabla visual mejorada

✅ Iconos para acciones

✅ Crear paquete

✅ Editar paquete

✅ Borrar paquete

✅ Confirmación al eliminar

✅ Badges visuales para estado entregado

✅ Mensajes de éxito

📁 Estructura del proyecto en este punto
Paqueteria/
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── templates/
│   │   ├── index.html
│   │   └── editar.html
│   └── static/
│
├── Dockerfile
├── docker-compose.yml
└── requirements.txt

🟢 PASO 1 — Instalar iconos Bootstrap

No hay que instalar nada en Python.
Simplemente se usa CDN en el HTML:

<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">

🟢 PASO 2 — Mejorar index.html

Ruta:

app/templates/index.html


Reemplazar completamente por:

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Paquetería</title>

    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- Iconos -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
</head>

<body class="bg-light">

<div class="container mt-5">

    <h1 class="mb-4">📦 Gestión de Paquetería</h1>

    {% if mensaje %}
        <div class="alert alert-success">
            {{ mensaje }}
        </div>
    {% endif %}

    <!-- TABLA -->
    <div class="card mb-4 shadow-sm">
        <div class="card-header bg-dark text-white">
            Lista de Paquetes
        </div>

        <div class="card-body">
            <table class="table table-striped table-bordered align-middle text-center">
                <thead class="table-dark">
                    <tr>
                        <th>ID</th>
                        <th>Nº Seguimiento</th>
                        <th>Destinatario</th>
                        <th>Peso</th>
                        <th>Fecha</th>
                        <th>Entregado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {% for paquete in paquetes %}
                    <tr>
                        <td>{{ paquete.id }}</td>
                        <td>{{ paquete.numero_seguimiento }}</td>
                        <td>{{ paquete.destinatario }}</td>
                        <td>{{ paquete.peso }} kg</td>
                        <td>{{ paquete.fecha_envio }}</td>
                        <td>
                            {% if paquete.entregado %}
                                <span class="badge bg-success">Sí</span>
                            {% else %}
                                <span class="badge bg-danger">No</span>
                            {% endif %}
                        </td>
                        <td>

                            <a href="/editar/{{ paquete.id }}" class="btn btn-warning btn-sm">
                                <i class="bi bi-pencil-square"></i>
                            </a>

                            <a href="/borrar/{{ paquete.id }}" class="btn btn-danger btn-sm"
                               onclick="return confirm('¿Seguro que deseas eliminar este paquete?');">
                                <i class="bi bi-trash"></i>
                            </a>

                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- FORMULARIO -->
    <div class="card shadow-sm">
        <div class="card-header bg-primary text-white">
            Crear Nuevo Paquete
        </div>

        <div class="card-body">
            <form action="/paquetes-web/" method="post">

                <div class="mb-3">
                    <label class="form-label">Número de Seguimiento</label>
                    <input type="text" name="numero_seguimiento"
                           class="form-control"
                           placeholder="Ejemplo: PKT-0001"
                           required>
                </div>

                <div class="mb-3">
                    <label class="form-label">Destinatario</label>
                    <input type="text" name="destinatario"
                           class="form-control"
                           placeholder="Nombre completo del destinatario"
                           required>
                </div>

                <div class="mb-3">
                    <label class="form-label">Peso (kg)</label>
                    <input type="number" name="peso"
                           class="form-control"
                           placeholder="Ejemplo: 2"
                           required>
                </div>

                <div class="mb-3">
                    <label class="form-label">Fecha de Envío</label>
                    <input type="date" name="fecha_envio"
                           class="form-control"
                           required>
                </div>

                <div class="form-check mb-3">
                    <input type="checkbox" name="entregado"
                           class="form-check-input">
                    <label class="form-check-label">
                        ¿Paquete entregado?
                    </label>
                </div>

                <button type="submit" class="btn btn-success">
                    <i class="bi bi-plus-circle"></i> Crear Paquete
                </button>

            </form>
        </div>
    </div>

</div>

</body>
</html>

🟢 PASO 3 — Ruta BORRAR en main.py

Añadir:

from fastapi.responses import RedirectResponse


Después:

@app.get("/borrar/{paquete_id}")
def borrar_paquete(paquete_id: int, db: Session = Depends(get_db)):
    paquete = db.query(models.Paquete).filter(models.Paquete.id == paquete_id).first()

    if paquete:
        db.delete(paquete)
        db.commit()

    return RedirectResponse(url="/web/", status_code=303)

🟢 PASO 4 — Ruta EDITAR en main.py
@app.get("/editar/{paquete_id}", response_class=HTMLResponse)
def editar_paquete(paquete_id: int, request: Request, db: Session = Depends(get_db)):
    paquete = db.query(models.Paquete).filter(models.Paquete.id == paquete_id).first()

    return templates.TemplateResponse("editar.html", {
        "request": request,
        "paquete": paquete
    })

🟢 PASO 5 — Crear editar.html

Ruta:

app/templates/editar.html


Contenido:

<!DOCTYPE html>
<html>
<head>
    <title>Editar Paquete</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>

<body class="container mt-5">

<h2>Editar Paquete</h2>

<form action="/actualizar/{{ paquete.id }}" method="post">

    <input type="text" name="numero_seguimiento"
           value="{{ paquete.numero_seguimiento }}"
           class="form-control mb-3">

    <input type="text" name="destinatario"
           value="{{ paquete.destinatario }}"
           class="form-control mb-3">

    <input type="number" name="peso"
           value="{{ paquete.peso }}"
           class="form-control mb-3">

    <input type="date" name="fecha_envio"
           value="{{ paquete.fecha_envio }}"
           class="form-control mb-3">

    <button type="submit" class="btn btn-primary">Actualizar</button>

</form>

</body>
</html>

🟢 PASO 6 — Ruta ACTUALIZAR en main.py
from datetime import datetime

@app.post("/actualizar/{paquete_id}")
def actualizar_paquete(paquete_id: int,
                       numero_seguimiento: str = Form(...),
                       destinatario: str = Form(...),
                       peso: int = Form(...),
                       fecha_envio: str = Form(...),
                       db: Session = Depends(get_db)):

    paquete = db.query(models.Paquete).filter(models.Paquete.id == paquete_id).first()

    fecha_convertida = datetime.strptime(fecha_envio, "%Y-%m-%d").date()

    paquete.numero_seguimiento = numero_seguimiento
    paquete.destinatario = destinatario
    paquete.peso = peso
    paquete.fecha_envio = fecha_convertida

    db.commit()

    return RedirectResponse(url="/web/", status_code=303)

🟢 PASO 7 — Reiniciar Docker

Siempre después de cambios:

docker compose down
docker compose up --build

🎉 Resultado Final

Ahora tienes:

✔ CRUD completo
✔ Diseño profesional
✔ Confirmación al borrar
✔ Edición funcional
✔ Placeholders claros
✔ Iconos profesionales
✔ Badges visuales

# #############################################
📘 PASO 5.2 — Preparar el proyecto para PRODUCCIÓN (Render)
🎯 OBJETIVO

Adaptar el proyecto Paquetería (FastAPI + PostgreSQL) para que funcione correctamente en:

🌍 Render (hosting en la nube)

🐳 Docker

🔐 Con variables de entorno seguras

⚙️ Compatible con puerto dinámico (PORT)

🧠 ¿Qué cambia respecto a local?

En local usamos:

uvicorn app.main:app --port 8000


En Render:

El puerto lo asigna Render

Debemos usar variable de entorno PORT

No usamos localhost

La base de datos será externa (Render PostgreSQL)

📦 1️⃣ requirements.txt para producción

Ejemplo profesional compatible con Render:

fastapi==0.110.2
uvicorn[standard]==0.29.0

# Base de datos
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
alembic==1.13.1

# Validación
pydantic==2.7.1
pydantic-settings==2.2.1

# Templates
jinja2==3.1.3
python-multipart==0.0.9

# Seguridad
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0

# Entorno
python-dotenv==1.0.1

# Producción
gunicorn==21.2.0

# Utilidades
email-validator==2.1.1

🐳 2️⃣ Dockerfile preparado para Render

Este es el punto MÁS IMPORTANTE.

FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

🔥 ¿Por qué así?

Render define automáticamente una variable:

PORT=10000


Nosotros NO ponemos el puerto fijo.

Así funciona tanto:

En local (si definimos PORT=8000)

En Render (Render define el puerto automáticamente)

🌱 3️⃣ Archivo .env para PRODUCCIÓN

En Render NO se sube .env.

Las variables se configuran en el panel de Render.

Ejemplo de variables que pondrás en Render:

DATABASE_URL=postgresql://usuario:password@host:5432/paqueteria
PORT=10000

🛠 4️⃣ Modificar database.py para usar DATABASE_URL

En database.py debe existir algo como esto:

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

🚀 5️⃣ main.py preparado para producción

Debe incluir el startup seguro:

import time
from fastapi import FastAPI
from app.database import engine
from app.models import Base

app = FastAPI()

@app.on_event("startup")
def startup():
    time.sleep(5)
    Base.metadata.create_all(bind=engine)

🧱 6️⃣ docker-compose para desarrollo local

Este SOLO es para desarrollo.

Render NO usa docker-compose.

services:

  db:
    image: postgres:15
    container_name: postgres_db
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: paqueteria
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    container_name: fastapi_app
    depends_on:
      - db
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - PORT=8000

volumes:
  postgres_data:

🌍 7️⃣ Subir a GitHub

Desde la raíz del proyecto:

git init
git add .
git commit -m "Proyecto listo para producción"
git branch -M main
git remote add origin [Juanan41](https://github.com/Juanan41/paqueteria-fastapi.git)
git push -u origin main

# Si sale esto: remote origin already exists

-Escribimos esto:
git remote remove origin
git remote add origin https://github.com/Juanan41/paqueteria-fastapi.git
git push -u origin main

☁️ 8️⃣ Crear servicio en Render

Ir a render.com

New → Web Service

Conectar repositorio GitHub

Elegir Docker

Deploy

🔑 9️⃣ Configurar variables en Render

En el panel:

Environment → Add Variable

Agregar:

DATABASE_URL = (la que te da Render PostgreSQL)
PORT = 10000

🧪 10️⃣ Verificar

Si todo está bien:

Deploy exitoso

App funcionando

Swagger disponible

Base de datos conectada

🎓 Resultado profesional

Tu proyecto ahora:

✅ Funciona en local
✅ Funciona con Docker
✅ Funciona en Render
✅ Usa variables de entorno
✅ Está listo para producción real