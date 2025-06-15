from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Crear el engine con configuración optimizada
engine = create_engine(
    settings.database_url, 
    echo=False,  # ✅ Cambiar a False para reducir logs en producción
    pool_pre_ping=True,  # Verificar conexiones antes de usarlas
    pool_recycle=300,    # Reciclar conexiones cada 5 minutos
    pool_size=10,        # ✅ Aumentar pool de conexiones
    max_overflow=20,     # ✅ Permitir más conexiones temporales
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
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
        logger.info("Creando tablas en la base de datos...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas exitosamente")
        
        # Verificar que las tablas se crearon
        with engine.connect() as conn:
            # Para PostgreSQL
            if "postgresql" in settings.database_url:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in result]
                logger.info(f"Tablas existentes: {tables}")
            # Para SQLite
            elif "sqlite" in settings.database_url:
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table'
                """))
                tables = [row[0] for row in result]
                logger.info(f"Tablas existentes: {tables}")
            
        return True
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
        logger.info(f"Probando conexión a: {settings.database_url[:50]}...")
        db = SessionLocal()
        
        # Ejecutar una query simple
        result = db.execute(text("SELECT 1")).fetchone()
        logger.info(f"Query de prueba exitosa: {result}")
        
        # Verificar si las tablas existen
        existing_tables = []
        if "postgresql" in settings.database_url:
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables_result = db.execute(tables_query).fetchall()
            existing_tables = [row[0] for row in tables_result]
        elif "sqlite" in settings.database_url:
            tables_query = text("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
            """)
            tables_result = db.execute(tables_query).fetchall()
            existing_tables = [row[0] for row in tables_result]
        
        logger.info(f"Tablas existentes en la base de datos: {existing_tables}")
        
        if 'client_data' not in existing_tables:
            logger.warning("⚠️ La tabla 'client_data' no existe")
        
        db.close()
        logger.info("✅ Conexión a la base de datos exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# Función adicional para debug
def count_records():
    """Contar registros en la tabla client_data"""
    try:
        db = SessionLocal()
        count = db.query(ClientData).count()
        db.close()
        logger.info(f"Registros en client_data: {count}")
        return count
    except Exception as e:
        logger.error(f"Error contando registros: {e}")
        return -1

# Función para limpiar logs excesivos
def optimize_database_logging():
    """Optimizar logging de la base de datos"""
    # Reducir el nivel de logging de SQLAlchemy
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    
# Llamar la optimización al importar
optimize_database_logging()

# Crear las tablas al importar el módulo (solo en desarrollo)
if __name__ == "__main__":
    logger.info("Ejecutando creación de tablas desde models.py")
    if test_database_connection():
        create_tables()
        count_records()