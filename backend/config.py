import os
from pydantic import BaseSettings
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Settings(BaseSettings):
    # Base de datos
    database_url: str = os.getenv("DATABASE_URL", "postgresql://dev:sernazavala2025@34.58.203.106:5432/anders_db")
    
    # Configuración de correo
    mail_username: str = os.getenv("MAIL_USERNAME", "")
    mail_password: str = os.getenv("MAIL_PASSWORD", "")
    mail_from: str = os.getenv("MAIL_FROM", "")
    mail_port: int = int(os.getenv("MAIL_PORT", "587"))
    mail_server: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    mail_tls: bool = os.getenv("MAIL_TLS", "True").lower() == "true"
    mail_ssl: bool = os.getenv("MAIL_SSL", "False").lower() == "true"
    use_credentials: bool = os.getenv("USE_CREDENTIALS", "True").lower() == "true"
    
    # Configuración de la aplicación
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()