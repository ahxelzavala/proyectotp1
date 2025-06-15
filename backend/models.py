from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Crear el engine con configuración mejorada
engine = create_engine(
    settings.database_url, 
    echo=False,  # Cambiar a True para ver las queries SQL en desarrollo
    pool_pre_ping=True,  # Verificar conexiones antes de usarlas
    pool_recycle=300,    # Reciclar conexiones cada 5 minutos
)

# Crear la sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo para almacenar los datos del cliente
class ClientData(Base):
    __tablename__ = "client_data"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(255), index=True, nullable=False)
    client_type = Column(String(100), default="No especificado")
    executive = Column(String(100), default="No asignado")
    product = Column(String(200), default="No especificado")
    value = Column(Float, default=0.0)
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<ClientData(id={self.id}, client_name='{self.client_name}', value={self.value})>"

# Modelo para emails autorizados
class AuthorizedEmail(Base):
    __tablename__ = "authorized_emails"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    added_by = Column(String(100), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AuthorizedEmail(id={self.id}, email='{self.email}')>"

def create_tables():
    """Función para crear todas las tablas"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")
        logger.info("Tablas creadas exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        logger.error(f"Error creando tablas: {e}")
        return False

def get_database():
    """Función para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error en sesión de base de datos: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def test_database_connection():
    """Probar la conexión a la base de datos"""
    try:
        db = SessionLocal()
        # Ejecutar una query simple
        result = db.execute("SELECT 1").fetchone()
        db.close()
        print("✅ Conexión a la base de datos exitosa")
        return True
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return False

# Crear las tablas al importar el módulo (solo en desarrollo)
if __name__ == "__main__":
    create_tables()