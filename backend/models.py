from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings

# Usar la configuración desde config.py
engine = create_engine(settings.database_url, echo=False)

# Crear la sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo para almacenar los datos del cliente
class ClientData(Base):
    __tablename__ = "client_data"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, index=True, nullable=False)
    client_type = Column(String, default="No especificado")
    executive = Column(String, default="No asignado")
    product = Column(String, default="No especificado")
    value = Column(Float, default=0.0)
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=True)
    category = Column(String, default="General")  # Nueva columna para categoría

# Modelo para emails autorizados
class AuthorizedEmail(Base):
    __tablename__ = "authorized_emails"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    added_by = Column(String, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

def create_tables():
    """Función para crear todas las tablas"""
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente")

def get_database():
    """Función para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Crear las tablas al importar el módulo
if __name__ == "__main__":
    create_tables()