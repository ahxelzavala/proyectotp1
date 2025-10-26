import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Para desarrollo local (opcional)
    #local_database_url: str = "postgresql://postgres:ben10ultimatealien@localhost:5432/anders_db"
    
    # Para producción con Supabase
    database_url: str = os.getenv("DATABASE_URL", "")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    
    class Config:
        env_file = ".env"


settings = Settings()