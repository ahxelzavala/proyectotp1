import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = ""
    secret_key: str = "dev-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    mail_username: Optional[str] = None
    mail_password: Optional[str] = None
    mail_from: Optional[str] = None
    mail_port: Optional[int] = 587
    mail_server: Optional[str] = None
    mail_tls: Optional[bool] = True
    mail_ssl: Optional[bool] = False
    use_credentials: Optional[bool] = True
    
    class Config:
        case_sensitive = False
        extra = "ignore"

# Crear settings con valores de entorno
settings = Settings(
    database_url=os.getenv("DATABASE_URL", ""),
    secret_key=os.getenv("SECRET_KEY", "dev-secret-key")
)

# DEBUG: Imprimir para ver qué valor tiene (TEMPORAL)
print(f"🔍 DATABASE_URL configurada: {settings.database_url[:50]}...")  # Solo primeros 50 caracteres
print(f"🔍 DATABASE_URL está vacía: {len(settings.database_url) == 0}")