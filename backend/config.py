import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Base de datos
    database_url: str = os.getenv("DATABASE_URL", "")
    
    # Seguridad
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Configuración de correo (opcional)
    mail_username: Optional[str] = None
    mail_password: Optional[str] = None
    mail_from: Optional[str] = None
    mail_port: Optional[int] = 587
    mail_server: Optional[str] = None
    mail_tls: Optional[bool] = True
    mail_ssl: Optional[bool] = False
    use_credentials: Optional[bool] = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # ← IMPORTANTE: Ignora campos extra del .env

settings = Settings()