from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from config import settings
import re

app = FastAPI()

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración del correo
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_TLS=settings.MAIL_TLS,
    MAIL_SSL=settings.MAIL_SSL,
    USE_CREDENTIALS=settings.USE_CREDENTIALS
)

class Analyst(BaseModel):
    email: EmailStr

class User(BaseModel):
    email: EmailStr
    password: str

# Simulando una base de datos
analysts_db = set()
users_db = set()

def validate_anders_email(email: str) -> bool:
    return email.endswith('@anders.com')

async def send_confirmation_email(email: str, background_tasks: BackgroundTasks):
    message = MessageSchema(
        subject="Confirmación de Registro - Anders",
        recipients=[email],
        body="""Gracias por registrarte en Anders.
        
Por favor, haz clic en el siguiente enlace para confirmar tu registro:
http://localhost:3000/login

Saludos,
Equipo Anders""",
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

@app.post('/analysts')
async def add_analyst(analyst: Analyst):
    if not validate_anders_email(analyst.email):
        raise HTTPException(status_code=400, detail='El correo debe ser de dominio anders.com')
    analysts_db.add(analyst.email)
    return {'message': 'Analista agregado correctamente'}

@app.get('/analysts')
async def get_analysts():
    return list(analysts_db)

@app.post('/register')
async def register_user(user: User, background_tasks: BackgroundTasks):
    if user.email in users_db:
        raise HTTPException(status_code=400, detail='Usuario ya registrado')
    if user.email not in analysts_db:
        raise HTTPException(status_code=400, detail='Correo no autorizado')
    
    await send_confirmation_email(user.email, background_tasks)
    users_db.add(user.email)
    
    return {'message': 'Usuario registrado. Por favor revise su correo para confirmar el registro'}