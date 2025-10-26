import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Base de datos
    database_url: str = ""
    
    # Seguridad
    secret_key: str = "dev-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Configuración de correo (opcional - no usado)
    mail_username: Optional[str] = None
    mail_password: Optional[str] = None
    mail_from: Optional[str] = None
    mail_port: Optional[int] = 587
    mail_server: Optional[str] = None
    mail_tls: Optional[bool] = True
    mail_ssl: Optional[bool] = False
    use_credentials: Optional[bool] = True
    
    class Config:
        # NO LEER archivo .env
        case_sensitive = False
        extra = "ignore"

# Crear settings obteniendo valores de variables de entorno directamente
settings = Settings(
    database_url=os.getenv("DATABASE_URL", ""),
    secret_key=os.getenv("SECRET_KEY", "dev-secret-key")
)