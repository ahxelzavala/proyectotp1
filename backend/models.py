from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, func, text, DECIMAL
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
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Crear la sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MODELO CLIENTDATA COMPLETO - Con todas las columnas del CSV
class ClientData(Base):
    __tablename__ = "client_data"
    
    # ID y metadatos
    id = Column(Integer, primary_key=True, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    filename = Column(String(255), nullable=True)
    
    # ===== TODAS LAS COLUMNAS DE TU CSV =====
    
    # Información básica de transacción
    fecha = Column(String(50), nullable=True, index=True)
    tipo_de_venta = Column(String(100), nullable=True)
    documento = Column(String(100), nullable=True)
    factura = Column(String(100), nullable=True, index=True)
    codigo = Column(String(100), nullable=True, index=True)
    
    # Información del cliente
    cliente = Column(String(255), nullable=True, index=True)  # Cliente principal
    tipo_de_cliente = Column(String(100), nullable=True)
    
    # Información del producto
    sku = Column(String(100), nullable=True)
    articulo = Column(String(500), nullable=True)
    proveedor = Column(String(255), nullable=True, index=True)
    almacen = Column(String(100), nullable=True)
    
    # Información de cantidad y medida
    cantidad = Column(DECIMAL(15,4), nullable=True)
    um = Column(String(50), nullable=True)  # U.M. (Unidad de Medida)
    
    # Información financiera
    p_venta = Column(DECIMAL(15,4), nullable=True)      # P. Venta
    c_unit = Column(DECIMAL(15,4), nullable=True)       # C. Unit
    venta = Column(DECIMAL(15,4), nullable=True, index=True)  # Venta total
    costo = Column(DECIMAL(15,4), nullable=True)        # Costo
    mb = Column(DECIMAL(15,4), nullable=True)           # MB (Margen Bruto)
    mb_percent = Column(String(20), nullable=True)      # %MB (Porcentaje MB)
    
    # Información organizacional
    sociedad = Column(String(100), nullable=True)
    bc = Column(String(100), nullable=True)
    bt = Column(String(100), nullable=True)
    bu = Column(String(255), nullable=True)
    bs = Column(String(255), nullable=True)
    
    # Información comercial y clasificación
    comercial = Column(String(255), nullable=True, index=True)  # Ejecutivo/Vendedor
    tipo_cliente = Column(String(100), nullable=True)           # Tipo_Cliente
    categoria = Column(String(255), nullable=True, index=True)  # CATEGORIA
    supercategoria = Column(String(255), nullable=True, index=True)  # SUPERCATEGORIA
    cruce = Column(String(10), nullable=True)                   # CRUCE
    
    # Campos adicionales para compatibilidad con código existente
    client_name = Column(String(255), nullable=True, index=True)    # Mapea a 'cliente'
    client_type = Column(String(100), nullable=True)               # Mapea a 'tipo_de_cliente'
    executive = Column(String(100), nullable=True)                 # Mapea a 'comercial'
    product = Column(String(200), nullable=True)                   # Mapea a 'articulo'
    value = Column(Float, nullable=True)                            # Mapea a 'venta'
    date = Column(DateTime, nullable=True)                          # Mapea a 'fecha' convertida
    description = Column(Text, nullable=True)                      # Campo libre
    
    def __repr__(self):
        return f"<ClientData(id={self.id}, cliente='{self.cliente}', factura='{self.factura}', venta={self.venta})>"

class Clients(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(255), nullable=False, index=True)
    client_type = Column(String(100), nullable=True)
    executive = Column(String(100), nullable=True)
    product = Column(String(200), nullable=True)
    value = Column(Float, nullable=True)
    date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Clients(id={self.id}, client_name='{self.client_name}', value={self.value})>"

# Modelo para emails autorizados (mantener igual)
class AuthorizedEmail(Base):
    __tablename__ = "authorized_emails"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    added_by = Column(String(100), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AuthorizedEmail(id={self.id}, email='{self.email}')>"

def create_tables():
    """Función para crear todas las tablas incluyendo clients"""
    try:
        logger.info("Creando tablas en la base de datos...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas exitosamente")
        
        # Verificar que las tablas se crearon
        with engine.connect() as conn:
            if "postgresql" in settings.database_url:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in result]
                logger.info(f"Tablas existentes: {tables}")
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

def migrate_add_new_columns():
    """Agregar las nuevas columnas a la tabla client_data existente"""
    try:
        logger.info("🔄 Agregando nuevas columnas a client_data...")
        
        # Lista de columnas a agregar con sus tipos
        new_columns = [
            ("uploaded_at", "TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP"),
            ("filename", "VARCHAR(255)"),
            ("fecha", "VARCHAR(50)"),
            ("tipo_de_venta", "VARCHAR(100)"),
            ("documento", "VARCHAR(100)"),
            ("factura", "VARCHAR(100)"),
            ("codigo", "VARCHAR(100)"),
            ("cliente", "VARCHAR(255)"),
            ("tipo_de_cliente", "VARCHAR(100)"),
            ("sku", "VARCHAR(100)"),
            ("articulo", "VARCHAR(500)"),
            ("proveedor", "VARCHAR(255)"),
            ("almacen", "VARCHAR(100)"),
            ("cantidad", "DECIMAL(15,4)"),
            ("um", "VARCHAR(50)"),
            ("p_venta", "DECIMAL(15,4)"),
            ("c_unit", "DECIMAL(15,4)"),
            ("venta", "DECIMAL(15,4)"),
            ("costo", "DECIMAL(15,4)"),
            ("mb", "DECIMAL(15,4)"),
            ("mb_percent", "VARCHAR(20)"),
            ("sociedad", "VARCHAR(100)"),
            ("bc", "VARCHAR(100)"),
            ("bt", "VARCHAR(100)"),
            ("bu", "VARCHAR(255)"),
            ("bs", "VARCHAR(255)"),
            ("comercial", "VARCHAR(255)"),
            ("tipo_cliente", "VARCHAR(100)"),
            ("categoria", "VARCHAR(255)"),
            ("supercategoria", "VARCHAR(255)"),
            ("cruce", "VARCHAR(10)")
        ]
        
        with engine.connect() as conn:
            # Verificar qué columnas ya existen
            if "postgresql" in settings.database_url:
                existing_columns_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'client_data'
                """)
            else:  # SQLite
                existing_columns_query = text("PRAGMA table_info(client_data)")
            
            result = conn.execute(existing_columns_query)
            
            if "postgresql" in settings.database_url:
                existing_columns = [row[0] for row in result]
            else:
                existing_columns = [row[1] for row in result]  # SQLite format
                
            logger.info(f"Columnas existentes: {existing_columns}")
            
            # Agregar columnas que no existen
            added_count = 0
            for col_name, col_type in new_columns:
                if col_name not in existing_columns:
                    try:
                        add_column_sql = text(f"ALTER TABLE client_data ADD COLUMN {col_name} {col_type}")
                        conn.execute(add_column_sql)
                        logger.info(f"  ✅ Agregada columna: {col_name}")
                        added_count += 1
                    except Exception as e:
                        logger.warning(f"  ⚠️  No se pudo agregar {col_name}: {e}")
                else:
                    logger.info(f"  ℹ️  Columna {col_name} ya existe")
            
            conn.commit()
            
            # Crear índices importantes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_client_data_fecha ON client_data(fecha)",
                "CREATE INDEX IF NOT EXISTS idx_client_data_cliente ON client_data(cliente)",
                "CREATE INDEX IF NOT EXISTS idx_client_data_factura ON client_data(factura)",
                "CREATE INDEX IF NOT EXISTS idx_client_data_codigo ON client_data(codigo)",
                "CREATE INDEX IF NOT EXISTS idx_client_data_proveedor ON client_data(proveedor)",
                "CREATE INDEX IF NOT EXISTS idx_client_data_venta ON client_data(venta)",
                "CREATE INDEX IF NOT EXISTS idx_client_data_comercial ON client_data(comercial)",
                "CREATE INDEX IF NOT EXISTS idx_client_data_categoria ON client_data(categoria)",
                "CREATE INDEX IF NOT EXISTS idx_client_data_supercategoria ON client_data(supercategoria)"
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    logger.info(f"  ✅ Índice creado")
                except Exception as e:
                    logger.warning(f"  ⚠️  Error creando índice: {e}")
            
            conn.commit()
            
            logger.info(f"✅ Migración completada. {added_count} columnas agregadas")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en migración: {e}")
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
        
        result = db.execute(text("SELECT 1")).fetchone()
        logger.info(f"Query de prueba exitosa: {result}")
        
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

def optimize_database_logging():
    """Optimizar logging de la base de datos"""
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)

# Llamar la optimización al importar
optimize_database_logging()

# Script de migración integrado
if __name__ == "__main__":
    logger.info("Ejecutando migración completa desde models.py")
    if test_database_connection():
        # Primero crear tablas básicas
        create_tables()
        
        # Luego agregar nuevas columnas
        migrate_add_new_columns()
        
        count_records()