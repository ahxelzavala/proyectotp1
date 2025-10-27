from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import pandas as pd
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import traceback
import json
import uvicorn
import os
import re
from pathlib import Path

# Importar modelos y configuración
from models import get_database, ClientData, AuthorizedEmail, create_tables, test_database_connection, migrate_add_new_columns
from config import settings

# ===== IMPORTS PARA ML =====
try:
    from ml_service import ml_service
    ML_AVAILABLE = True
    print("✅ ML Service cargado exitosamente")
except ImportError as e:
    ML_AVAILABLE = False
    print(f"⚠️ ML Service no disponible: {e}")
    # Crear un mock del ml_service
    class MockMLService:
        def __init__(self):
            self.is_loaded = False
            self.demo_mode = True
        
        def get_model_info(self):
            return {
                "loaded": False,
                "error": "ML Service no disponible - instalar dependencias ML"
            }
        

def predict_cross_sell(self, client_data: List[Dict], threshold: Optional[float] = None) -> List[Dict]:
    """Realizar predicciones de venta cruzada usando datos reales del CSV"""
    if not self.is_loaded:
        raise Exception("Modelo no está cargado")
    
    try:
        if threshold is None:
            threshold = self.model_metadata.get('threshold', 0.5)
        
        results = []
        
        for i, client_info in enumerate(client_data):
            if self.demo_mode:
                # Usar lógica demo mejorada con datos reales
                prob = self._calculate_enhanced_demo_probability(client_info)
            else:
                # Usar modelo REAL
                prob = self._predict_with_real_model(client_info)
            
            pred = 1 if prob >= threshold else 0
            
            # Determinar prioridad
            if prob >= 0.7:
                priority = "Alta"
            elif prob >= 0.5:
                priority = "Media"
            elif prob >= 0.3:
                priority = "Baja"
            else:
                priority = "Muy Baja"
            
            result = {
                "client_id": client_info.get('id', i),
                "client_name": client_info.get('cliente', f"Cliente_{i}"),
                "probability": round(float(prob), 4),
                "prediction": int(pred),
                "recommendation": "Sí" if pred == 1 else "No",
                "priority": priority,
                "threshold_used": threshold,
                "confidence": "Alta" if prob > 0.6 or prob < 0.4 else "Media",
                
                # DATOS REALES del CSV - PRESERVADOS
                "venta_actual": client_info.get('venta', 0),
                "venta": client_info.get('venta', 0),  # Ambos para compatibilidad
                "mb_total": client_info.get('mb', 0),
                "mb": client_info.get('mb', 0),  # Ambos para compatibilidad
                "costo_total": client_info.get('costo', 0),
                "cantidad_total": client_info.get('cantidad', 0),
                
                # Información del cliente REAL
                "tipo_cliente": client_info.get('tipo_de_cliente', 'Sin tipo'),
                "categoria": client_info.get('categoria', 'Sin categoría'),
                "comercial": client_info.get('comercial', 'Sin asignar'),
                "proveedor": client_info.get('proveedor', 'Sin proveedor'),
                "codigo_cliente": client_info.get('codigo_cliente', 'Sin código'),
                "num_transacciones": client_info.get('num_transacciones', 0),
                "num_facturas": client_info.get('num_facturas', 0),
                "primera_compra": client_info.get('primera_compra'),
                "ultima_compra": client_info.get('ultima_compra'),
                
                # Metadatos del modelo
                "prediction_date": datetime.now().isoformat(),
                "model_version": self.model_metadata.get('model_version', '1.0'),
                "demo_mode": self.demo_mode
            }
            
            results.append(result)
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error en predicción: {str(e)}")
        raise
        
        def get_feature_importance(self):
            return []
    
    ml_service = MockMLService()

# ===== MODELOS PYDANTIC PARA ML =====
from pydantic import BaseModel

class PredictionRequest(BaseModel):
    client_ids: Optional[List[int]] = None
    threshold: Optional[float] = None
    limit: Optional[int] = 100

class SingleClientPrediction(BaseModel):
    cliente: str
    venta: float
    costo: float
    mb: float
    cantidad: float
    tipo_de_cliente: str
    categoria: str
    comercial: Optional[str] = None
    proveedor: Optional[str] = None
    threshold: Optional[float] = None

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sistema de Análisis Anders",
    description="API para importar y analizar datos CSV completos",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://proyectotp1.vercel.app",
        "https://proyectotp2.vercel.app",
        "https://proyectotp11.vercel.app",
        "https://proyectotp.vercel.app",
        "https://proyectotp22.vercel.app",
        "*",  # Temporal para debugging
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def read_root():
    return {"message": "Sistema Anders API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ===== STARTUP EVENT =====
@app.on_event("startup")
async def startup_event():
    """Inicializar la base de datos al arrancar"""
    logger.info("Iniciando aplicación...")
    
    if not test_database_connection():
        logger.error("❌ No se pudo conectar a la base de datos")
        raise Exception("Error de conexión a la base de datos")
    
    if not create_tables():
        logger.error("❌ No se pudieron crear las tablas")
        raise Exception("Error creando tablas de la base de datos")
    
    # Ejecutar migración para agregar nuevas columnas
    if not migrate_add_new_columns():
        logger.warning("⚠️ No se pudieron agregar todas las columnas nuevas")
    
    # Verificar ml Service
    if ML_AVAILABLE and ml_service.is_loaded:
        logger.info("✅ Sistema ML inicializado correctamente")
    else:
        logger.info("⚠️ Sistema funcionando sin ML (usar modo demo)")
    
    logger.info("✅ Base de datos inicializada correctamente")

@app.get("/")
async def root():
    return {"message": "Bienvenido al Sistema de Análisis Anders v2.0 - CSV Completo"}

@app.get("/health")
async def health_check():
    try:
        db = next(get_database())
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "error", "database": "disconnected", "error": str(e)}

# ===== ENDPOINT DE DIAGNÓSTICO =====
@app.get("/debug/data-status")
async def debug_data_status_postgresql(db: Session = Depends(get_database)):
    """Diagnóstico específico para PostgreSQL"""
    try:
        logger.info("🔍 Ejecutando diagnóstico de PostgreSQL...")
        
        # Verificar conexión
        db.execute(text("SELECT 1")).scalar()
        logger.info("✅ Conexión a PostgreSQL OK")
        
        # Verificar si existe la tabla
        table_exists_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = 'client_data'
            )
        """)
        table_exists = db.execute(table_exists_query).scalar()
        logger.info(f"📋 Tabla existe: {table_exists}")
        
        if not table_exists:
            return {
                "error": "Tabla client_data no existe en el esquema public",
                "solution": "Ejecutar migración de base de datos",
                "table_exists": False,
                "postgres_specific": True
            }
        
        # Contar registros
        total_count = db.execute(text("SELECT COUNT(*) FROM client_data")).scalar()
        logger.info(f"📊 Total registros: {total_count}")
        
        # Verificar estructura de datos
        sample_query = text("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(cliente) as cliente_not_null,
                COUNT(venta) as venta_not_null,
                COUNT(mb) as mb_not_null
            FROM client_data
        """)
        
        sample_result = db.execute(sample_query).fetchone()
        
        # Muestra de datos
        sample_data_query = text("""
            SELECT cliente, venta, mb, factura, fecha
            FROM client_data 
            WHERE cliente IS NOT NULL 
            LIMIT 3
        """)
        
        sample_data = db.execute(sample_data_query).fetchall()
        
        # Verificar tipos de columnas
        column_types_query = text("""
            SELECT 
                column_name, 
                data_type,
                is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND table_name = 'client_data' 
            AND column_name IN ('venta', 'mb', 'costo', 'cantidad')
            ORDER BY column_name
        """)
        
        column_types = db.execute(column_types_query).fetchall()
        
        return {
            "success": True,
            "postgres_version": "Compatible",
            "table_exists": table_exists,
            "total_records": total_count,
            "data_quality": {
                "total_rows": sample_result.total_rows if sample_result else 0,
                "cliente_not_null": sample_result.cliente_not_null if sample_result else 0,
                "venta_not_null": sample_result.venta_not_null if sample_result else 0,
                "mb_not_null": sample_result.mb_not_null if sample_result else 0
            },
            "sample_data": [
                {
                    "cliente": row.cliente,
                    "venta": str(row.venta),
                    "mb": str(row.mb),
                    "factura": row.factura,
                    "fecha": row.fecha
                }
                for row in sample_data
            ],
            "column_info": [
                {
                    "column": row.column_name,
                    "type": row.data_type,
                    "nullable": row.is_nullable
                }
                for row in column_types
            ],
            "recommendations": [
                "Usar ::text y ::numeric para conversiones seguras",
                "Verificar que los datos numéricos no contengan caracteres especiales",
                "Considerar usar CAST() en lugar de conversiones implícitas"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error en diagnóstico: {str(e)}")
        return {
            "error": f"Error en diagnóstico PostgreSQL: {str(e)}",
            "success": False,
            "traceback": traceback.format_exc(),
            "postgres_specific": True
        }

# ===== ENDPOINT DE MÉTRICAS CORREGIDO =====
@app.get("/analytics/summary")
async def get_summary_analytics_postgresql(db: Session = Depends(get_database)):
    """Obtener métricas reales adaptadas específicamente para PostgreSQL"""
    try:
        logger.info("🔍 Iniciando cálculo de métricas para PostgreSQL...")
        
        # Verificar que la tabla existe
        table_check_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = 'client_data'
            )
        """)
        table_exists = db.execute(table_check_query).scalar()
        
        if not table_exists:
            logger.error("❌ Tabla client_data no existe")
            return {
                "success": False,
                "error": "Tabla client_data no existe en la base de datos",
                "summary": {
                    "total_records": 0,
                    "unique_clients": 0,
                    "total_sales": 0.0,
                    "average_margin_percentage": 0.0
                }
            }
        
        # Contar registros totales
        total_records = db.execute(text("SELECT COUNT(*) FROM client_data")).scalar() or 0
        logger.info(f"📊 Total de registros: {total_records}")
        
        if total_records == 0:
            logger.warning("⚠️ No hay datos en la tabla")
            return {
                "success": False,
                "message": "No hay datos en la tabla client_data. Por favor, sube un archivo CSV.",
                "summary": {
                    "total_records": 0,
                    "unique_clients": 0,
                    "total_sales": 0.0,
                    "average_margin_percentage": 0.0
                }
            }
        
        # Clientes únicos - PostgreSQL compatible
        unique_clients_query = text("""
            SELECT COUNT(DISTINCT cliente) 
            FROM client_data 
            WHERE cliente IS NOT NULL 
            AND TRIM(cliente) != ''
        """)
        unique_clients = db.execute(unique_clients_query).scalar() or 0
        logger.info(f"👥 Clientes únicos: {unique_clients}")
        
        # Ventas totales - Conversión segura para PostgreSQL
        total_sales_query = text("""
            SELECT COALESCE(
                SUM(
                    CASE 
                        WHEN venta::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN venta::numeric
                        ELSE 0
                    END
                ), 0
            )
            FROM client_data 
            WHERE venta IS NOT NULL
        """)
        total_sales = float(db.execute(total_sales_query).scalar() or 0)
        logger.info(f"💰 Ventas totales: {total_sales}")
        
        # Margen bruto total - PostgreSQL compatible
        total_margin_query = text("""
            SELECT COALESCE(
                SUM(
                    CASE 
                        WHEN mb::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN mb::numeric
                        ELSE 0
                    END
                ), 0
            )
            FROM client_data 
            WHERE mb IS NOT NULL
        """)
        total_margin = float(db.execute(total_margin_query).scalar() or 0)
        logger.info(f"📈 Margen total: {total_margin}")
        
        # Calcular margen promedio
        average_margin_percentage = 0
        if total_sales > 0:
            average_margin_percentage = round((total_margin / total_sales) * 100, 2)
        
        # Métricas adicionales
        unique_invoices = db.execute(text("""
            SELECT COUNT(DISTINCT factura) 
            FROM client_data 
            WHERE factura IS NOT NULL AND TRIM(factura) != ''
        """)).scalar() or 0
        
        unique_products = db.execute(text("""
            SELECT COUNT(DISTINCT articulo) 
            FROM client_data 
            WHERE articulo IS NOT NULL AND TRIM(articulo) != ''
        """)).scalar() or 0
        
        # Cálculos derivados
        average_transaction_value = round(total_sales / unique_invoices, 2) if unique_invoices > 0 else 0
        average_sales_per_client = round(total_sales / unique_clients, 2) if unique_clients > 0 else 0
        
        # Top 3 clientes para validación
        top_clients_query = text("""
            SELECT 
                cliente,
                SUM(
                    CASE 
                        WHEN venta::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN venta::numeric
                        ELSE 0
                    END
                ) as total_venta
            FROM client_data 
            WHERE cliente IS NOT NULL 
            AND TRIM(cliente) != ''
            GROUP BY cliente
            ORDER BY total_venta DESC
            LIMIT 3
        """)
        
        top_clients_result = db.execute(top_clients_query).fetchall()
        top_clients = [
            {"cliente": row.cliente, "total_venta": float(row.total_venta)}
            for row in top_clients_result
        ]
        
        logger.info("✅ Métricas calculadas exitosamente")
        
        return {
            "success": True,
            "message": "Métricas calculadas exitosamente desde datos reales",
            "data_source": "CSV cargado en client_data (PostgreSQL)",
            "summary": {
                "total_records": total_records,
                "unique_clients": unique_clients,
                "total_sales": total_sales,
                "total_margin": total_margin,
                "average_margin_percentage": average_margin_percentage,
                "unique_invoices": unique_invoices,
                "unique_products": unique_products,
                "average_transaction_value": average_transaction_value,
                "average_sales_per_client": average_sales_per_client
            },
            "top_clients": top_clients,
            "explanations": {
                "total_records": "Número total de transacciones en el CSV cargado",
                "unique_clients": "Clientes únicos identificados en el campo 'Cliente'",
                "total_sales": "Suma total de ventas válidas del campo 'Venta'",
                "average_margin_percentage": "Margen bruto promedio: (Total MB ÷ Total Ventas) × 100"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error en métricas: {str(e)}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        
        # Fallback básico
        try:
            basic_count = db.execute(text("SELECT COUNT(*) FROM client_data")).scalar() or 0
            return {
                "success": False,
                "error": f"Error calculando métricas: {str(e)}",
                "debug_info": str(e),
                "summary": {
                    "total_records": basic_count,
                    "unique_clients": 0,
                    "total_sales": 0.0,
                    "total_margin": 0.0,
                    "average_margin_percentage": 0.0
                }
            }
        except:
            return {
                "success": False,
                "error": "Error crítico accediendo a los datos",
                "summary": {
                    "total_records": 0,
                    "unique_clients": 0,
                    "total_sales": 0.0,
                    "total_margin": 0.0,
                    "average_margin_percentage": 0.0
                }
            }

@app.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    replace_data: bool = True,
    db: Session = Depends(get_database)
):
    """
    Endpoint mejorado para cargar CSV con TODAS las columnas
    """
    try:
        logger.info(f"Procesando archivo completo: {file.filename}")
        
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="El archivo debe ser un CSV (.csv)")
        
        # Limpiar datos anteriores si se solicita
        if replace_data:
            try:
                deleted_count = db.query(ClientData).delete()
                db.commit()
                logger.info(f"🗑️ Datos anteriores eliminados: {deleted_count} registros")
            except Exception as e:
                db.rollback()
                logger.error(f"Error eliminando datos anteriores: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error limpiando datos anteriores: {str(e)}")
        
        # Leer el archivo
        contents = await file.read()
        csv_string = contents.decode('utf-8')
        csv_io = io.StringIO(csv_string)
        
        # Leer CSV
        try:
            df = pd.read_csv(
                csv_io,
                encoding='utf-8',
                skipinitialspace=True,
                na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', 'NONE'],
                keep_default_na=True
            )
            logger.info(f"CSV leído exitosamente. Filas: {len(df)}, Columnas: {len(df.columns)}")
            logger.info(f"Columnas encontradas: {list(df.columns)}")
        except Exception as e:
            logger.error(f"Error leyendo CSV: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error al leer el archivo CSV: {str(e)}")
        
        if df.empty:
            raise HTTPException(status_code=400, detail="El archivo CSV está vacío")
        
        # Función para obtener valor de manera segura
        def get_safe_value(row, column_name, convert_to=str, default=None):
            """Obtener valor de columna de manera segura"""
            if column_name in df.columns and not pd.isna(row[column_name]):
                try:
                    value = row[column_name]
                    if convert_to == str:
                        return str(value).strip() if str(value).strip() not in ['nan', 'None', 'null'] else default
                    elif convert_to == float:
                        # Limpiar valor numérico
                        if isinstance(value, (int, float)):
                            return float(value)
                        else:
                            value_str = str(value).replace(',', '').replace('$', '').replace('%', '').strip()
                            import re
                            value_str = re.sub(r'[^\d.-]', '', value_str)
                            return float(value_str) if value_str else default
                    elif convert_to == datetime:
                        parsed_date = pd.to_datetime(value, errors='coerce')
                        return parsed_date.to_pydatetime() if not pd.isna(parsed_date) else default
                except Exception as e:
                    logger.warning(f"Error convirtiendo {column_name}: {e}")
                    return default
            return default
        
        # Procesar registros
        processed_records = []
        errors = []
        
        logger.info(f"Procesando {len(df)} filas con todas las columnas...")
        
        for index, row in df.iterrows():
            try:
                # Crear registro con TODAS las columnas del CSV
                client_record = ClientData(
                    # Metadatos
                    uploaded_at=datetime.utcnow(),
                    filename=file.filename,
                    
                    # ===== TODAS LAS COLUMNAS DEL CSV =====
                    fecha=get_safe_value(row, 'Fecha', str),
                    tipo_de_venta=get_safe_value(row, 'Tipo de Venta', str),
                    documento=get_safe_value(row, 'Documento', str),
                    factura=get_safe_value(row, 'Factura', str),
                    codigo=get_safe_value(row, 'Codigo', str),
                    cliente=get_safe_value(row, 'Cliente', str),
                    tipo_de_cliente=get_safe_value(row, 'Tipo de Cliente', str),
                    sku=get_safe_value(row, 'SKU', str),
                    articulo=get_safe_value(row, 'Articulo', str),
                    proveedor=get_safe_value(row, 'Proveedor', str),
                    almacen=get_safe_value(row, 'Almacen', str),
                    cantidad=get_safe_value(row, 'Cantidad', float, 0.0),
                    um=get_safe_value(row, 'U.M.', str),
                    p_venta=get_safe_value(row, 'P. Venta', float, 0.0),
                    c_unit=get_safe_value(row, 'C. Unit', float, 0.0),
                    venta=get_safe_value(row, 'Venta', float, 0.0),
                    costo=get_safe_value(row, 'Costo', float, 0.0),
                    mb=get_safe_value(row, 'MB', float, 0.0),
                    mb_percent=get_safe_value(row, '%MB', str),
                    sociedad=get_safe_value(row, 'Sociedad', str),
                    bc=get_safe_value(row, 'BC', str),
                    bt=get_safe_value(row, 'BT', str),
                    bu=get_safe_value(row, 'BU', str),
                    bs=get_safe_value(row, 'BS', str),
                    comercial=get_safe_value(row, 'Comercial', str),
                    tipo_cliente=get_safe_value(row, 'Tipo_Cliente', str),
                    categoria=get_safe_value(row, 'CATEGORIA', str),
                    supercategoria=get_safe_value(row, 'SUPERCATEGORIA', str),
                    cruce=get_safe_value(row, 'CRUCE', str),
                    
                    # ===== CAMPOS DE COMPATIBILIDAD =====
                    client_name=get_safe_value(row, 'Cliente', str, "Sin nombre"),
                    client_type=get_safe_value(row, 'Tipo de Cliente', str, "No especificado"),
                    executive=get_safe_value(row, 'Comercial', str, "No asignado"),
                    product=get_safe_value(row, 'Articulo', str, "No especificado"),
                    value=get_safe_value(row, 'Venta', float, 0.0),
                    date=get_safe_value(row, 'Fecha', datetime, datetime.utcnow()),
                    description=f"Importado desde {file.filename} - Fila {index + 1}"
                )
                
                processed_records.append(client_record)
                
                if (index + 1) % 1000 == 0:
                    logger.info(f"Procesadas {index + 1} filas...")
                    
            except Exception as e:
                logger.error(f"Error procesando fila {index + 1}: {str(e)}")
                errors.append(f"Fila {index + 1}: Error procesando datos - {str(e)}")
                continue
        
        if not processed_records:
            error_message = f"No se pudieron procesar registros. Errores: {'; '.join(errors[:5])}"
            logger.error(error_message)
            raise HTTPException(status_code=400, detail=error_message)
        
        logger.info(f"Registros procesados exitosamente: {len(processed_records)}")
        
        # Guardar en lotes
        saved_count = 0
        try:
            batch_size = 1000
            total_batches = (len(processed_records) + batch_size - 1) // batch_size
            
            for i in range(0, len(processed_records), batch_size):
                batch = processed_records[i:i + batch_size]
                db.add_all(batch)
                db.commit()
                saved_count += len(batch)
                logger.info(f"Lote {(i // batch_size) + 1}/{total_batches} guardado: {len(batch)} registros")
            
            logger.info(f"✅ {saved_count} registros guardados exitosamente con todas las columnas")
            
        except Exception as e:
            db.rollback()
            error_msg = f"Error guardando en base de datos: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Preparar respuesta detallada
        response_data = {
            "success": True,
            "message": f"Archivo procesado exitosamente con todas las columnas. {saved_count} registros guardados.",
            "details": {
                "filename": file.filename,
                "total_rows": len(df),
                "processed_rows": len(processed_records),
                "saved_rows": saved_count,
                "errors_count": len(errors),
                "all_columns_mapped": True,
                "columns_found": list(df.columns),
                "columns_count": len(df.columns),
                "storage_method": "Todas las columnas en campos individuales"
            }
        }
        
        if errors:
            response_data["errors"] = errors[:10]
            if len(errors) > 10:
                response_data["errors"].append(f"... y {len(errors) - 10} errores más")
        
        logger.info(f"Respuesta enviada: {response_data['message']}")
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/client-data")
async def get_client_data(
    limit: int = 100,
    offset: int = 0,
    include_all_fields: bool = False,
    db: Session = Depends(get_database)
):
    """Obtener datos de clientes con opción de incluir todos los campos"""
    try:
        total_count = db.query(ClientData).count()
        clients = db.query(ClientData).offset(offset).limit(limit).all()
        
        logger.info(f"Consultando datos: {len(clients)} registros (de {total_count} totales)")
        
        if include_all_fields:
            # Devolver TODOS los campos
            client_data = []
            for client in clients:
                client_dict = {
                    "id": client.id,
                    "uploaded_at": client.uploaded_at.isoformat() if client.uploaded_at else None,
                    "filename": client.filename,
                    
                    # Campos del CSV
                    "fecha": client.fecha,
                    "tipo_de_venta": client.tipo_de_venta,
                    "documento": client.documento,
                    "factura": client.factura,
                    "codigo": client.codigo,
                    "cliente": client.cliente,
                    "tipo_de_cliente": client.tipo_de_cliente,
                    "sku": client.sku,
                    "articulo": client.articulo,
                    "proveedor": client.proveedor,
                    "almacen": client.almacen,
                    "cantidad": float(client.cantidad) if client.cantidad else None,
                    "um": client.um,
                    "p_venta": float(client.p_venta) if client.p_venta else None,
                    "c_unit": float(client.c_unit) if client.c_unit else None,
                    "venta": float(client.venta) if client.venta else None,
                    "costo": float(client.costo) if client.costo else None,
                    "mb": float(client.mb) if client.mb else None,
                    "mb_percent": client.mb_percent,
                    "sociedad": client.sociedad,
                    "bc": client.bc,
                    "bt": client.bt,
                    "bu": client.bu,
                    "bs": client.bs,
                    "comercial": client.comercial,
                    "tipo_cliente": client.tipo_cliente,
                    "categoria": client.categoria,
                    "supercategoria": client.supercategoria,
                    "cruce": client.cruce,
                    
                    # Campos de compatibilidad
                    "client_name": client.client_name,
                    "client_type": client.client_type,
                    "executive": client.executive,
                    "product": client.product,
                    "value": client.value,
                    "date": client.date.isoformat() if client.date else None,
                    "description": client.description
                }
                client_data.append(client_dict)
        else:
            # Devolver solo campos básicos para compatibilidad
            client_data = [
                {
                    "id": client.id,
                    "client_name": client.client_name,
                    "client_type": client.client_type,
                    "executive": client.executive,
                    "product": client.product,
                    "value": client.value,
                    "date": client.date.isoformat() if client.date else None,
                    "description": client.description,
                    
                    # Campos principales del CSV
                    "cliente": client.cliente,
                    "factura": client.factura,
                    "venta": float(client.venta) if client.venta else None,
                    "fecha": client.fecha,
                    "comercial": client.comercial,
                    "categoria": client.categoria
                }
                for client in clients
            ]
        
        return {
            "success": True,
            "total_count": total_count,
            "count": len(clients),
            "offset": offset,
            "limit": limit,
            "include_all_fields": include_all_fields,
            "data": client_data
        }
    except Exception as e:
        logger.error(f"Error consultando datos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/client-data/full")
async def get_client_data_full(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_database)
):
    """Obtener datos completos con todas las columnas del CSV"""
    return await get_client_data(limit, offset, include_all_fields=True, db=db)

@app.get("/client-data/search")
async def search_client_data(
    cliente: str = None,
    factura: str = None,
    fecha_desde: str = None,
    fecha_hasta: str = None,
    comercial: str = None,
    categoria: str = None,
    proveedor: str = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_database)
):
    """Buscar datos con filtros específicos"""
    try:
        query = db.query(ClientData)
        
        # Aplicar filtros
        if cliente:
            query = query.filter(ClientData.cliente.ilike(f'%{cliente}%'))
        
        if factura:
            query = query.filter(ClientData.factura.ilike(f'%{factura}%'))
        
        if fecha_desde:
            query = query.filter(ClientData.fecha >= fecha_desde)
        
        if fecha_hasta:
            query = query.filter(ClientData.fecha <= fecha_hasta)
        
        if comercial:
            query = query.filter(ClientData.comercial.ilike(f'%{comercial}%'))
        
        if categoria:
            query = query.filter(ClientData.categoria.ilike(f'%{categoria}%'))
        
        if proveedor:
            query = query.filter(ClientData.proveedor.ilike(f'%{proveedor}%'))
        
        total_count = query.count()
        records = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "total_count": total_count,
            "count": len(records),
            "filters_applied": {
                "cliente": cliente,
                "factura": factura,
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "comercial": comercial,
                "categoria": categoria,
                "proveedor": proveedor
            },
            "data": [
                {
                    "id": record.id,
                    "cliente": record.cliente,
                    "factura": record.factura,
                    "fecha": record.fecha,
                    "venta": float(record.venta) if record.venta else None,
                    "comercial": record.comercial,
                    "categoria": record.categoria,
                    "proveedor": record.proveedor,
                    "articulo": record.articulo,
                    "cantidad": float(record.cantidad) if record.cantidad else None,
                    "um": record.um
                }
                for record in records
            ]
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/client-data/clear")
async def clear_client_data(db: Session = Depends(get_database)):
    """Limpiar todos los datos de clientes"""
    try:
        deleted_count = db.query(ClientData).delete()
        db.commit()
        logger.info(f"Se eliminaron {deleted_count} registros")
        return {
            "success": True,
            "message": f"Se eliminaron {deleted_count} registros"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando datos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/count")
async def debug_count(db: Session = Depends(get_database)):
    """Endpoint de debug para verificar el conteo de registros"""
    try:
        count = db.query(ClientData).count()
        
        # Obtener una muestra de los primeros 3 registros con todos los campos
        sample = db.query(ClientData).limit(3).all()
        sample_data = []
        
        for client in sample:
            sample_data.append({
                "id": client.id,
                "cliente": client.cliente,
                "factura": client.factura,
                "fecha": client.fecha,
                "venta": float(client.venta) if client.venta else None,
                "comercial": client.comercial,
                "categoria": client.categoria,
                "articulo": client.articulo,
                "proveedor": client.proveedor,
                "filename": client.filename
            })
        
        return {
            "count": count, 
            "message": f"Hay {count} registros en la base de datos",
            "sample_data": sample_data,
            "all_columns_available": True
        }
    except Exception as e:
        logger.error(f"Error en debug count: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/columns")
async def debug_columns():
    """Endpoint para mostrar todas las columnas disponibles"""
    return {
        "csv_columns_mapped": [
            "fecha", "tipo_de_venta", "documento", "factura", "codigo", "cliente", 
            "tipo_de_cliente", "sku", "articulo", "proveedor", "almacen", "cantidad", 
            "um", "p_venta", "c_unit", "venta", "costo", "mb", "mb_percent", 
            "sociedad", "bc", "bt", "bu", "bs", "comercial", "tipo_cliente", 
            "categoria", "supercategoria", "cruce"
        ],
        "compatibility_fields": [
            "client_name", "client_type", "executive", "product", "value", "date", "description"
        ],
        "metadata_fields": [
            "id", "uploaded_at", "filename"
        ],
        "total_fields": 32,
        "message": "Todas las columnas del CSV se mapean a campos individuales de la tabla"
    }

@app.post("/preview-csv")
async def preview_csv(file: UploadFile = File(...)):
    """Previsualizar un CSV sin guardarlo"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="El archivo debe ser un CSV (.csv)")
        
        contents = await file.read()
        csv_string = contents.decode('utf-8')
        csv_io = io.StringIO(csv_string)
        
        # Leer solo las primeras 10 filas
        df = pd.read_csv(
            csv_io,
            encoding='utf-8',
            skipinitialspace=True,
            na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', 'NONE'],
            keep_default_na=True,
            nrows=10
        )
        
        original_columns = list(df.columns)
        
        # Verificar mapeo de columnas
        expected_columns = [
            "Fecha", "Tipo de Venta", "Documento", "Factura", "Codigo", "Cliente", 
            "Tipo de Cliente", "SKU", "Articulo", "Proveedor", "Almacen", "Cantidad", 
            "U.M.", "P. Venta", "C. Unit", "Venta", "Costo", "MB", "%MB", 
            "Sociedad", "BC", "BT", "BU", "BS", "Comercial", "Tipo_Cliente", 
            "CATEGORIA", "SUPERCATEGORIA", "CRUCE"
        ]
        
        matched_columns = [col for col in expected_columns if col in original_columns]
        missing_columns = [col for col in expected_columns if col not in original_columns]
        extra_columns = [col for col in original_columns if col not in expected_columns]
        
        # Convertir muestra a JSON
        sample_data = []
        for index, row in df.iterrows():
            row_dict = {}
            for col in df.columns:
                value = row[col]
                if pd.isna(value):
                    row_dict[col] = None
                else:
                    row_dict[col] = str(value)
            sample_data.append(row_dict)
        
        return {
            "success": True,
            "filename": file.filename,
            "columns_found": original_columns,
            "columns_count": len(original_columns),
            "matching_analysis": {
                "matched_columns": matched_columns,
                "missing_columns": missing_columns,
                "extra_columns": extra_columns,
                "match_percentage": round((len(matched_columns) / len(expected_columns)) * 100, 2)
            },
            "sample_data": sample_data,
            "total_rows_preview": len(df),
            "ready_to_upload": len(missing_columns) == 0,
            "message": f"CSV analizado: {len(matched_columns)}/{len(expected_columns)} columnas coinciden"
        }
        
    except Exception as e:
        logger.error(f"Error en preview CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")

# ===== ENDPOINTS ML CORREGIDOS =====

@app.get("/ml/status")
async def get_ml_status():
    """Verificar el estado del modelo de ML"""
    try:
        model_info = ml_service.get_model_info()
        return {
            "success": True,
            "model_info": model_info,
            "message": "Modelo cargado correctamente" if model_info.get("loaded") else "Modelo no disponible"
        }
    except Exception as e:
        logger.error(f"Error verificando estado ML: {str(e)}")
        return {
            "success": False,
            "model_info": {"loaded": False},
            "message": f"Error: {str(e)}"
        }

@app.get("/ml/model-performance")
async def get_model_performance_real():
    """Obtener métricas de rendimiento del modelo (reales o de metadatos)"""
    try:
        if not ML_AVAILABLE:
            # Si no hay ML disponible, usar métricas de ejemplo mejoradas
            return {
                "success": True,
                "demo_mode": True,
                "performance": {
                    "model_version": "Demo v1.0",
                    "training_date": "2024-01-15",
                    "threshold": 0.5,
                    "metrics": {
                        "accuracy": 59.7,     # 59.7%
                        "precision": 76.7,    # 76.7%
                        "recall": 67.2,       # 67.2%
                        "f1_score": 84.6,     # 84.6%
                        "roc_auc": 84.6
                    },
                    "feature_importance": [
                        {"feature": "Venta", "importance": 0.25},
                        {"feature": "Tipo Cliente", "importance": 0.20},
                        {"feature": "Margen Bruto", "importance": 0.15},
                        {"feature": "Cantidad", "importance": 0.12},
                        {"feature": "Categoría", "importance": 0.10}
                    ],
                    "model_description": "Modelo demo para análisis de venta cruzada"
                }
            }
        
        # Si ML está disponible, obtener métricas reales
        model_info = ml_service.get_model_info()
        
        if not model_info.get("loaded"):
            return {
                "success": False,
                "message": "Modelo no cargado",
                "performance": {}
            }
        
        # Intentar cargar métricas desde metadatos reales
        try:
            metadata_path = Path("ml_models/model_metadata.json")
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Usar métricas reales del archivo
                real_metrics = metadata.get('metrics', {})
                
                # Convertir a porcentajes si están en decimal
                processed_metrics = {}
                for key, value in real_metrics.items():
                    if isinstance(value, (int, float)) and value <= 1.0:
                        processed_metrics[key] = value * 100  # Convertir a porcentaje
                    else:
                        processed_metrics[key] = value
                
                return {
                    "success": True,
                    "demo_mode": False,
                    "performance": {
                        "model_version": metadata.get('model_version', 'Unknown'),
                        "training_date": metadata.get('training_date', 'Unknown'),
                        "threshold": metadata.get('threshold', 0.5),
                        "metrics": processed_metrics,
                        "feature_importance": ml_service.get_feature_importance()[:10],
                        "model_description": f"Modelo XGBoost {metadata.get('model_type', 'real')}",
                        "training_samples": metadata.get('training_samples', 'Unknown'),
                        "validation_samples": metadata.get('validation_samples', 'Unknown')
                    }
                }
            
        except Exception as e:
            logger.warning(f"Error cargando metadatos reales: {e}")
        
        # Fallback con métricas del servicio ML
        feature_importance = ml_service.get_feature_importance()
        model_metrics = model_info.get('metrics', {})
        
        # Convertir métricas a porcentajes
        processed_metrics = {}
        for key, value in model_metrics.items():
            if isinstance(value, (int, float)) and value <= 1.0:
                processed_metrics[key] = value * 100
            else:
                processed_metrics[key] = value
        
        return {
            "success": True,
            "demo_mode": ml_service.demo_mode,
            "performance": {
                "model_version": model_info.get('model_version', 'Unknown'),
                "training_date": model_info.get('training_date', 'Unknown'),
                "threshold": model_info.get('threshold', 0.5),
                "metrics": processed_metrics,
                "feature_importance": feature_importance[:10] if feature_importance else [],
                "model_description": "Modelo XGBoost para venta cruzada"
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo performance: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "performance": {
                "metrics": {
                    "accuracy": 0.0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0,
                    "roc_auc": 0.0
                }
            }
        }

@app.get("/ml/cross-sell-recommendations")
async def get_cross_sell_recommendations_postgresql(
    limit: int = 50,
    min_probability: float = 0.3,
    db: Session = Depends(get_database)
):
    """Obtener recomendaciones de venta cruzada - PostgreSQL compatible"""
    try:
        logger.info("🤖 Iniciando recomendaciones ML...")
        
        # Verificar que el modelo esté disponible
        if not ml_service.is_loaded:
            logger.warning("⚠️ Modelo ML no disponible, usando datos simulados")
            # Generar datos de ejemplo para recomendaciones
            example_recommendations = []
            
            # Obtener algunos clientes reales para simular recomendaciones
            clients_query = text("""
                SELECT DISTINCT cliente, tipo_de_cliente, categoria, comercial
                FROM client_data 
                WHERE cliente IS NOT NULL 
                AND TRIM(cliente) != ''
                LIMIT :limit
            """)
            
            clients_result = db.execute(clients_query, {"limit": limit}).fetchall()
            
            for i, client in enumerate(clients_result):
                # Simular probabilidad basada en datos del cliente
                import random
                random.seed(hash(client.cliente) % 1000)  # Determinística pero variada
                probability = 0.4 + (random.random() * 0.5)  # Entre 0.4 y 0.9
                
                if probability >= min_probability:
                    example_recommendations.append({
                        "client_id": i + 1,
                        "client_name": client.cliente,
                        "probability": round(probability, 4),
                        "prediction": 1,
                        "recommendation": "Sí",
                        "priority": "Alta" if probability >= 0.7 else ("Media" if probability >= 0.5 else "Baja"),
                        "venta_actual": random.randint(1000, 50000),
                        "categoria": client.categoria or "Sin categoría",
                        "tipo_cliente": client.tipo_de_cliente or "Sin tipo",
                        "comercial": client.comercial or "Sin asignar",
                        "demo_mode": True
                    })
            
            return {
                "success": True,
                "message": f"Recomendaciones simuladas generadas (ML no disponible)",
                "total_evaluated": len(clients_result),
                "high_quality_recommendations": len(example_recommendations),
                "min_probability_filter": min_probability,
                "demo_mode": True,
                "recommendations": example_recommendations[:limit]
            }
        
        # Si ML está disponible, usar consulta corregida para PostgreSQL
        active_clients_query = text("""
            SELECT 
                id, cliente, 
                CASE 
                    WHEN venta::text ~ '^[0-9]+\.?[0-9]*$' 
                    THEN venta::numeric
                    ELSE 0
                END as venta,
                CASE 
                    WHEN costo::text ~ '^[0-9]+\.?[0-9]*$' 
                    THEN costo::numeric
                    ELSE 0
                END as costo,
                CASE 
                    WHEN mb::text ~ '^[0-9]+\.?[0-9]*$' 
                    THEN mb::numeric
                    ELSE 0
                END as mb,
                CASE 
                    WHEN cantidad::text ~ '^[0-9]+\.?[0-9]*$' 
                    THEN cantidad::numeric
                    ELSE 0
                END as cantidad,
                tipo_de_cliente, categoria, comercial, proveedor, fecha
            FROM client_data 
            WHERE cliente IS NOT NULL 
            AND TRIM(cliente) != ''
            AND venta IS NOT NULL
            ORDER BY venta DESC
            LIMIT :limit_param
        """)
        
        result = db.execute(active_clients_query, {"limit_param": limit * 2}).fetchall()
        
        if not result:
            return {
                "success": False,
                "message": "No se encontraron clientes activos",
                "recommendations": []
            }
        
        # Convertir a formato para ML
        client_data = []
        for row in result:
            client_dict = {
                "id": row.id,
                "cliente": row.cliente,
                "venta": float(row.venta or 0),
                "costo": float(row.costo or 0),
                "mb": float(row.mb or 0),
                "cantidad": float(row.cantidad or 0),
                "tipo_de_cliente": row.tipo_de_cliente or "Unknown",
                "categoria": row.categoria or "Unknown",
                "comercial": row.comercial or "Unknown",
                "proveedor": row.proveedor or "Unknown",
                "fecha": row.fecha
            }
            client_data.append(client_dict)
        
        # Realizar predicciones ML
        all_predictions = ml_service.predict_cross_sell(client_data)
        
        # Filtrar por probabilidad mínima
        filtered_recommendations = [
            pred for pred in all_predictions 
            if pred['prediction'] == 1 and pred['probability'] >= min_probability
        ]
        
        # Ordenar por probabilidad descendente
        filtered_recommendations.sort(key=lambda x: x['probability'], reverse=True)
        
        # Limitar resultados
        final_recommendations = filtered_recommendations[:limit]
        
        logger.info(f"✅ {len(final_recommendations)} recomendaciones generadas")
        
        return {
            "success": True,
            "message": f"Se encontraron {len(final_recommendations)} recomendaciones de alta calidad",
            "total_evaluated": len(client_data),
            "total_positive": len([p for p in all_predictions if p['prediction'] == 1]),
            "high_quality_recommendations": len(final_recommendations),
            "min_probability_filter": min_probability,
            "demo_mode": ml_service.demo_mode,
            "recommendations": final_recommendations
        }
        
    except Exception as e:
        logger.error(f"❌ Error en recomendaciones ML: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            "success": False,
            "message": f"Error obteniendo recomendaciones: {str(e)}",
            "error_details": str(e),
            "recommendations": []
        }


@app.post("/ml/predict-cross-sell")
async def predict_cross_sell_batch(
    request: PredictionRequest,
    db: Session = Depends(get_database)
):
    """Predicciones de venta cruzada en lote"""
    try:
        # Verificar que el modelo esté cargado
        if not ml_service.is_loaded:
            return {
                "success": False,
                "message": "Modelo de ML no disponible",
                "predictions": []
            }
        
        # Construir query base
        query = db.query(ClientData)
        
        # Filtrar por client_ids si se especifican
        if request.client_ids:
            query = query.filter(ClientData.id.in_(request.client_ids))
        
        # Aplicar límite
        clients = query.limit(request.limit).all()
        
        if not clients:
            return {
                "success": False,
                "message": "No se encontraron clientes para procesar",
                "total_clients": 0,
                "predictions": []
            }
        
        # Convertir a formato para ML
        client_data = []
        for client in clients:
            client_dict = {
                "id": client.id,
                "cliente": client.cliente or "Unknown",
                "venta": float(client.venta or 0),
                "costo": float(client.costo or 0),
                "mb": float(client.mb or 0),
                "cantidad": float(client.cantidad or 0),
                "tipo_de_cliente": client.tipo_de_cliente or "Unknown",
                "categoria": client.categoria or "Unknown",
                "comercial": client.comercial or "Unknown",
                "proveedor": client.proveedor or "Unknown"
            }
            client_data.append(client_dict)
        
        # Realizar predicciones
        predictions = ml_service.predict_cross_sell(client_data, request.threshold)
        
        # Estadísticas
        total_predictions = len(predictions)
        positive_predictions = sum(1 for p in predictions if p['prediction'] == 1)
        avg_probability = sum(p['probability'] for p in predictions) / total_predictions if total_predictions > 0 else 0
        
        return {
            "success": True,
            "message": f"Predicciones completadas para {total_predictions} clientes",
            "total_clients": total_predictions,
            "predictions": predictions,
            "statistics": {
                "positive_predictions": positive_predictions,
                "positive_rate": round((positive_predictions / total_predictions) * 100, 2) if total_predictions > 0 else 0,
                "average_probability": round(avg_probability, 4),
                "threshold_used": request.threshold or ml_service.model_metadata.get('threshold', 0.4)
            }
        }
        
    except Exception as e:
        logger.error(f"Error en predicción batch: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "predictions": []
        }

# ===== ENDPOINTS DE ANALYTICS ADICIONALES =====

@app.get("/clients/analytics/segmentation-stacked")
async def get_client_segmentation_stacked(db: Session = Depends(get_database)):
    """
    Gráfico de barras apiladas: Segmentación de clientes por tipo y supercategoría
    Variables: Tipo de Cliente, CATEGORIA, Cantidad
    """
    try:
        # Consulta corregida para PostgreSQL - SIN FILTROS DE FECHA PROBLEMÁTICOS
        query = text("""
            SELECT 
                COALESCE(categoria, 'Sin categoría') as categoria,
                COALESCE(tipo_de_cliente, 'Sin tipo') as tipo_cliente,
                COUNT(DISTINCT cliente) as cantidad_clientes,
                ROUND(CAST(SUM(COALESCE(venta, 0)) AS NUMERIC), 2) as total_ventas
            FROM client_data 
            WHERE cliente IS NOT NULL AND cliente != ''
            GROUP BY categoria, tipo_de_cliente
            ORDER BY total_ventas DESC
            LIMIT 20
        """)
        
        result = db.execute(query).fetchall()
        
        # Procesar datos para el gráfico apilado
        data = []
        for row in result:
            data.append({
                "categoria": row.categoria,
                "tipo_cliente": row.tipo_cliente,
                "cantidad_clientes": row.cantidad_clientes,
                "total_ventas": float(row.total_ventas)
            })
        
        return {
            "success": True,
            "data": data,
            "chart_type": "stacked_bar",
            "description": "Segmentación de clientes por tipo y categoría"
        }
        
    except Exception as e:
        logger.error(f"Error en segmentación: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clients/analytics/frequency-scatter")
async def get_client_frequency_scatter(db: Session = Depends(get_database)):
    """
    Gráfico de dispersión: Relación entre la frecuencia de compra y el tipo de cliente
    Variables: Cliente, Fecha, Cantidad, Tipo de Cliente
    """
    try:
        # Consulta para calcular frecuencia de compra por cliente (PostgreSQL)
        query = text("""
            SELECT 
                cliente,
                COALESCE(tipo_de_cliente, 'Sin tipo') as tipo_cliente,
                COUNT(DISTINCT factura) as numero_facturas,
                COUNT(DISTINCT fecha) as dias_unicos_compra,
                SUM(COALESCE(cantidad, 0)) as cantidad_total,
                SUM(COALESCE(venta, 0)) as total_ventas,
                MIN(fecha) as primera_compra,
                MAX(fecha) as ultima_compra,
                CASE 
                    WHEN COUNT(DISTINCT fecha) > 1 THEN
                        CAST(COUNT(DISTINCT factura) AS FLOAT) / 
                        GREATEST(1, COUNT(DISTINCT fecha) / 30.0)
                    ELSE 0
                END as frecuencia_compra
            FROM client_data 
            WHERE cliente IS NOT NULL AND cliente != '' 
                AND fecha IS NOT NULL
            GROUP BY cliente, tipo_de_cliente
            HAVING COUNT(DISTINCT factura) >= 1
            ORDER BY frecuencia_compra DESC, total_ventas DESC
            LIMIT 100
        """)
        
        result = db.execute(query).fetchall()
        
        data = []
        for row in result:
            data.append({
                "cliente": row.cliente,
                "tipo_cliente": row.tipo_cliente,
                "numero_facturas": row.numero_facturas,
                "dias_unicos_compra": row.dias_unicos_compra,
                "cantidad_total": float(row.cantidad_total),
                "total_ventas": float(row.total_ventas),
                "frecuencia_compra": float(row.frecuencia_compra)
            })
        
        return {
            "success": True,
            "data": data,
            "chart_type": "scatter",
            "description": "Relación entre frecuencia de compra y tipo de cliente"
        }
        
    except Exception as e:
        logger.error(f"Error en frecuencia scatter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))





@app.get("/clients/analytics/top-profitable-detailed")
async def get_top_profitable_detailed_using_tipo_cliente(
    limit: int = 10,
    db: Session = Depends(get_database)
):
    """Top clientes más rentables usando la columna TIPO_CLIENTE (categorías reales)"""
    try:
        logger.info(f"💰 Calculando top {limit} clientes con tipo_cliente (categorías)...")
        
        # Query usando la columna tipo_cliente que contiene las categorías reales
        query = text("""
            SELECT 
                cliente,
                COALESCE(tipo_cliente, 'Sin categoría') as tipo_cliente,
                COUNT(*) as num_transacciones,
                COUNT(DISTINCT factura) as num_facturas,
                
                -- Total de ventas por cliente
                ROUND(CAST(SUM(
                    CASE 
                        WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN venta::numeric
                        ELSE 0
                    END
                ) AS NUMERIC), 2) as total_ventas,
                
                -- Total margen bruto por cliente
                ROUND(CAST(SUM(
                    CASE 
                        WHEN mb IS NOT NULL AND mb::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN mb::numeric
                        ELSE 0
                    END
                ) AS NUMERIC), 2) as total_mb,
                
                -- Venta promedio por transacción
                ROUND(CAST(AVG(
                    CASE 
                        WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN venta::numeric
                        ELSE 0
                    END
                ) AS NUMERIC), 2) as venta_promedio_transaccion,
                
                -- Rentabilidad porcentual
                CASE 
                    WHEN SUM(
                        CASE 
                            WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                            THEN venta::numeric
                            ELSE 0
                        END
                    ) > 0 THEN
                        ROUND(
                            CAST(
                                SUM(
                                    CASE 
                                        WHEN mb IS NOT NULL AND mb::text ~ '^[0-9]+\.?[0-9]*$' 
                                        THEN mb::numeric
                                        ELSE 0
                                    END
                                ) * 100.0 / SUM(
                                    CASE 
                                        WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                                        THEN venta::numeric
                                        ELSE 0
                                    END
                                ) AS NUMERIC
                            ), 1
                        )
                    ELSE 0
                END as rentabilidad_porcentaje,
                
                MIN(fecha) as primera_compra,
                MAX(fecha) as ultima_compra
                
            FROM client_data 
            WHERE cliente IS NOT NULL 
            AND TRIM(cliente) != ''
            AND venta IS NOT NULL
            GROUP BY cliente, tipo_cliente
            HAVING SUM(
                CASE 
                    WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                    THEN venta::numeric
                    ELSE 0
                END
            ) > 0
            ORDER BY total_ventas DESC
            LIMIT :limit_param
        """)
        
        result = db.execute(query, {"limit_param": limit}).fetchall()
        
        # Verificar que tenemos datos
        if not result:
            logger.warning("⚠️ No se encontraron clientes rentables")
            return {
                "success": False,
                "message": "No se encontraron clientes rentables",
                "data": [],
                "estadisticas": {}
            }
        
        # Log de las categorías de los clientes top para verificar
        categorias_top = list(set([row.tipo_cliente for row in result[:5]]))
        logger.info(f"📋 Categorías en el Top 5: {categorias_top}")
        
        # Calcular estadísticas del TOP
        total_ventas_top = sum(row.total_ventas for row in result)
        total_mb_top = sum(row.total_mb for row in result)
        margen_promedio_top = (total_mb_top / total_ventas_top * 100) if total_ventas_top > 0 else 0
        total_transacciones_top = sum(row.num_transacciones for row in result)
        total_facturas_top = sum(row.num_facturas for row in result)
        
        # Procesar datos con rankings y métricas
        data = []
        for i, row in enumerate(result, 1):
            # Calcular participación en el TOP
            participacion_en_top = (row.total_ventas / total_ventas_top * 100) if total_ventas_top > 0 else 0
            
            data.append({
                "ranking": i,
                "cliente": row.cliente,
                "tipo_cliente": row.tipo_cliente,  # Usando la columna tipo_cliente correcta
                "num_transacciones": row.num_transacciones,
                "num_facturas": row.num_facturas,
                
                # Valores monetarios
                "total_ventas": float(row.total_ventas),
                "total_mb": float(row.total_mb),
                "venta_promedio_transaccion": float(row.venta_promedio_transaccion),
                
                # Porcentajes
                "rentabilidad_porcentaje": float(row.rentabilidad_porcentaje),
                "participacion_en_top": round(participacion_en_top, 1),
                
                # Fechas
                "primera_compra": row.primera_compra,
                "ultima_compra": row.ultima_compra,
                
                # Categorización visual
                "categoria_cliente": (
                    "🥇 Top Tier" if i <= 3 else
                    "🥈 Premium" if i <= 6 else
                    "🥉 Importante"
                ),
                
                # Métricas adicionales
                "frecuencia_compra": round(row.num_facturas / max(1, row.num_transacciones), 2),
                "valor_promedio_factura": round(row.total_ventas / max(1, row.num_facturas), 2)
            })
        
        # Estadísticas finales del TOP
        estadisticas_resumen = {
            # Totales
            "total_ventas_top": total_ventas_top,
            "total_mb_top": total_mb_top,
            "total_transacciones_top": total_transacciones_top,
            "total_facturas_top": total_facturas_top,
            
            # Promedios
            "margen_promedio_top": round(margen_promedio_top, 1),
            "venta_promedio_cliente": round(total_ventas_top / len(data), 2) if data else 0,
            "transacciones_promedio_cliente": round(total_transacciones_top / len(data), 1) if data else 0,
            
            # Metadatos
            "clientes_analizados": len(data),
            "limite_solicitado": limit,
            
            # Explicaciones de cálculos
            "explicaciones": {
                "total_ventas_top": f"Suma de ventas de los {len(data)} mejores clientes",
                "margen_promedio_top": f"({total_mb_top:,.2f} ÷ {total_ventas_top:,.2f}) × 100 = {margen_promedio_top:.1f}%",
                "rentabilidad_individual": "Para cada cliente: (Total MB ÷ Total Ventas) × 100",
                "participacion_en_top": "Para cada cliente: (Sus ventas ÷ Total ventas TOP) × 100"
            }
        }
        
        logger.info(f"✅ Calculados {len(data)} clientes rentables")
        logger.info(f"💰 Total ventas TOP: {total_ventas_top:,.2f}")
        logger.info(f"📈 Margen promedio TOP: {margen_promedio_top:.1f}%")
        
        return {
            "success": True,
            "data": data,
            "estadisticas": estadisticas_resumen,
            "total_clients": len(data),
            "message": f"Top {len(data)} clientes más rentables con categorías tipo_cliente"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en clientes rentables: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "data": [],
            "estadisticas": {}
        }


@app.get("/clients/analytics/client-type-analysis")
async def get_client_type_analysis_postgresql(db: Session = Depends(get_database)):
    """Análisis de ventas por tipo de cliente - PostgreSQL compatible"""
    try:
        logger.info("🔍 Analizando tipos de cliente...")
        
        # Verificar que hay datos
        total_records = db.execute(text("SELECT COUNT(*) FROM client_data")).scalar()
        if total_records == 0:
            return {
                "success": False,
                "message": "No hay datos en la tabla client_data",
                "data": []
            }
        
        # Query corregida para PostgreSQL
        query = text("""
            SELECT 
                COALESCE(tipo_de_cliente, 'Sin tipo') as tipo_cliente,
                COUNT(DISTINCT cliente) as num_clientes,
                COUNT(*) as num_transacciones,
                ROUND(CAST(SUM(
                    CASE 
                        WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN venta::numeric
                        ELSE 0
                    END
                ) AS NUMERIC), 2) as total_ventas
            FROM client_data 
            WHERE cliente IS NOT NULL 
            AND TRIM(cliente) != ''
            GROUP BY tipo_de_cliente
            HAVING SUM(
                CASE 
                    WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                    THEN venta::numeric
                    ELSE 0
                END
            ) > 0
            ORDER BY total_ventas DESC
            LIMIT 10
        """)
        
        result = db.execute(query).fetchall()
        
        data = []
        for row in result:
            data.append({
                "tipo_cliente": row.tipo_cliente,
                "num_clientes": row.num_clientes,
                "num_transacciones": row.num_transacciones,
                "total_ventas": float(row.total_ventas)
            })
        
        logger.info(f"✅ {len(data)} tipos de cliente analizados")
        
        return {
            "success": True,
            "data": data,
            "total_types": len(data),
            "message": f"Análisis completado: {len(data)} tipos de cliente"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en análisis de tipos: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "data": []
        }

@app.get("/clients/analytics/most-profitable")
async def get_most_profitable_clients_postgresql(
    limit: int = 15,
    db: Session = Depends(get_database)
):
    """Top clientes más rentables - PostgreSQL compatible"""
    try:
        logger.info("💰 Analizando clientes más rentables...")
        
        # Query corregida para PostgreSQL
        query = text("""
            SELECT 
                cliente,
                COALESCE(tipo_de_cliente, 'Sin tipo') as tipo_cliente,
                COUNT(*) as num_transacciones,
                ROUND(CAST(SUM(
                    CASE 
                        WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN venta::numeric
                        ELSE 0
                    END
                ) AS NUMERIC), 2) as total_ventas,
                ROUND(CAST(SUM(
                    CASE 
                        WHEN mb IS NOT NULL AND mb::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN mb::numeric
                        ELSE 0
                    END
                ) AS NUMERIC), 2) as total_mb,
                CASE 
                    WHEN SUM(
                        CASE 
                            WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                            THEN venta::numeric
                            ELSE 0
                        END
                    ) > 0 THEN
                        ROUND(
                            CAST(
                                SUM(
                                    CASE 
                                        WHEN mb IS NOT NULL AND mb::text ~ '^[0-9]+\.?[0-9]*$' 
                                        THEN mb::numeric
                                        ELSE 0
                                    END
                                ) * 100.0 / SUM(
                                    CASE 
                                        WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                                        THEN venta::numeric
                                        ELSE 0
                                    END
                                ) AS NUMERIC
                            ), 2
                        )
                    ELSE 0
                END as rentabilidad_porcentaje
            FROM client_data 
            WHERE cliente IS NOT NULL 
            AND TRIM(cliente) != ''
            AND venta IS NOT NULL
            GROUP BY cliente, tipo_de_cliente
            HAVING SUM(
                CASE 
                    WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                    THEN venta::numeric
                    ELSE 0
                END
            ) > 0
            ORDER BY total_ventas DESC
            LIMIT :limit_param
        """)
        
        result = db.execute(query, {"limit_param": limit}).fetchall()
        
        data = []
        for row in result:
            data.append({
                "cliente": row.cliente,
                "tipo_cliente": row.tipo_cliente,
                "num_transacciones": row.num_transacciones,
                "total_ventas": float(row.total_ventas),
                "total_mb": float(row.total_mb),
                "rentabilidad_porcentaje": float(row.rentabilidad_porcentaje)
            })
        
        logger.info(f"✅ {len(data)} clientes rentables analizados")
        
        return {
            "success": True,
            "data": data,
            "total_clients": len(data),
            "message": f"Top {len(data)} clientes más rentables"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en clientes rentables: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "data": []
        }

# Reemplazar la función get_acquisition_trend_postgresql en main.py con esta versión que SOLO usa datos reales

# REEMPLAZAR el endpoint get_acquisition_trend_real_data_only en main.py con esta versión corregida

@app.get("/clients/analytics/acquisition-trend")
async def get_acquisition_trend_fixed_final(db: Session = Depends(get_database)):
    """Tendencia de adquisición de clientes - VERSIÓN FINAL CORREGIDA"""
    try:
        logger.info("📈 Iniciando análisis de tendencia de adquisición CORREGIDO...")
        
        # Verificar que hay datos en la tabla
        total_records = db.execute(text("SELECT COUNT(*) FROM client_data")).scalar()
        if total_records == 0:
            return {
                "success": False,
                "message": "No hay datos cargados. Por favor, sube un archivo CSV primero.",
                "data": [],
                "error_type": "NO_DATA"
            }
        
        logger.info(f"📊 Total de registros encontrados: {total_records}")
        
        # Query SIMPLIFICADA y ROBUSTA para PostgreSQL
        query = text("""
            WITH client_first_purchase AS (
                SELECT 
                    cliente,
                    fecha,
                    ROW_NUMBER() OVER (PARTITION BY cliente ORDER BY fecha ASC) as rn
                FROM client_data 
                WHERE cliente IS NOT NULL 
                AND TRIM(cliente) != ''
                AND fecha IS NOT NULL 
                AND fecha != ''
                AND LENGTH(TRIM(fecha)) >= 7
            ),
            first_purchases_only AS (
                SELECT 
                    cliente,
                    fecha as primera_compra
                FROM client_first_purchase
                WHERE rn = 1
            ),
            monthly_grouping AS (
                SELECT 
                    cliente,
                    primera_compra,
                    CASE 
                        -- Formato YYYY-MM-DD (ISO)
                        WHEN primera_compra ~ '^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}' THEN
                            LEFT(primera_compra, 7)
                        -- Formato DD/MM/YYYY
                        WHEN primera_compra ~ '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}' THEN
                            RIGHT(primera_compra, 4) || '-' || 
                            LPAD(SPLIT_PART(primera_compra, '/', 2), 2, '0')
                        -- Formato MM/DD/YYYY (estilo americano)
                        WHEN primera_compra ~ '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}' AND 
                             CAST(SPLIT_PART(primera_compra, '/', 1) AS INTEGER) > 12 THEN
                            RIGHT(primera_compra, 4) || '-' || 
                            LPAD(SPLIT_PART(primera_compra, '/', 1), 2, '0')
                        -- Cualquier otro formato que contenga año de 4 dígitos
                        WHEN primera_compra ~ '[0-9]{4}' THEN
                            SUBSTRING(primera_compra FROM '[0-9]{4}') || '-01'
                        -- Fallback
                        ELSE '2024-01'
                    END as mes_ano
                FROM first_purchases_only
            ),
            monthly_summary AS (
                SELECT 
                    mes_ano,
                    COUNT(DISTINCT cliente) as nuevos_clientes
                FROM monthly_grouping
                WHERE mes_ano IS NOT NULL 
                AND mes_ano != ''
                AND LENGTH(mes_ano) = 7
                AND mes_ano ~ '^[0-9]{4}-[0-9]{2}$'
                GROUP BY mes_ano
            )
            SELECT 
                mes_ano as mes,
                nuevos_clientes
            FROM monthly_summary
            WHERE nuevos_clientes > 0
            ORDER BY mes_ano
            LIMIT 24
        """)
        
        result = db.execute(query).fetchall()
        logger.info(f"📊 Query ejecutada, {len(result)} períodos encontrados")
        
        if not result or len(result) == 0:
            logger.warning("⚠️ No se encontraron datos válidos para tendencia")
            
            # Intentar consulta de diagnóstico
            diagnostic_query = text("""
                SELECT 
                    COUNT(*) as total_clientes,
                    COUNT(DISTINCT fecha) as fechas_unicas,
                    MIN(fecha) as fecha_min,
                    MAX(fecha) as fecha_max,
                    COUNT(CASE WHEN fecha IS NOT NULL AND fecha != '' THEN 1 END) as fechas_validas
                FROM client_data
                WHERE cliente IS NOT NULL 
                AND TRIM(cliente) != ''
            """)
            
            diagnostic = db.execute(diagnostic_query).fetchone()
            
            return {
                "success": False,
                "message": "No se encontraron datos válidos para generar tendencia",
                "data": [],
                "diagnostic": {
                    "total_clientes": diagnostic.total_clientes,
                    "fechas_unicas": diagnostic.fechas_unicas,
                    "fecha_min": diagnostic.fecha_min,
                    "fecha_max": diagnostic.fecha_max,
                    "fechas_validas": diagnostic.fechas_validas
                },
                "error_type": "NO_VALID_DATES"
            }
        
        # Procesar resultados
        data = []
        for row in result:
            data.append({
                "mes": row.mes,
                "nuevos_clientes": row.nuevos_clientes
            })
        
        # Log de los resultados para debugging
        logger.info(f"✅ Datos procesados exitosamente:")
        for item in data[:5]:
            logger.info(f"   {item['mes']}: {item['nuevos_clientes']} nuevos clientes")
        
        # Calcular estadísticas adicionales
        total_clientes = sum(item['nuevos_clientes'] for item in data)
        promedio_mensual = round(total_clientes / len(data), 1) if data else 0
        max_mes = max(data, key=lambda x: x['nuevos_clientes']) if data else None
        
        return {
            "success": True,
            "data": data,
            "total_periods": len(data),
            "message": f"Tendencia calculada: {len(data)} períodos con datos reales",
            "data_source": "Datos reales del CSV",
            "total_records_analyzed": total_records,
            "statistics": {
                "total_clientes": total_clientes,
                "promedio_mensual": promedio_mensual,
                "max_clientes_mes": max_mes['nuevos_clientes'] if max_mes else 0,
                "mejor_mes": max_mes['mes'] if max_mes else None,
                "periodos_analizados": len(data)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error crítico en tendencia: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            "success": False,
            "message": f"Error procesando datos: {str(e)}",
            "data": [],
            "error_type": "PROCESSING_ERROR",
            "error_details": str(e)
        }

# ENDPOINT TEMPORAL PARA DIAGNÓSTICO - agregar a main.py

@app.get("/debug/date-analysis")
async def debug_date_analysis(db: Session = Depends(get_database)):
    """Endpoint temporal para analizar el formato de fechas en tus datos"""
    try:
        logger.info("🔍 Analizando formato de fechas...")
        
        # Muestra de fechas únicas
        sample_query = text("""
            SELECT DISTINCT fecha, LENGTH(fecha) as len
            FROM client_data 
            WHERE fecha IS NOT NULL 
            AND fecha != ''
            ORDER BY fecha
            LIMIT 20
        """)
        
        sample_dates = db.execute(sample_query).fetchall()
        
        # Contar patrones
        pattern_analysis = {}
        date_formats = []
        
        for row in sample_dates:
            fecha_str = str(row.fecha)
            length = len(fecha_str)
            
            # Analizar patrón
            if length not in pattern_analysis:
                pattern_analysis[length] = {"count": 0, "examples": []}
            
            pattern_analysis[length]["count"] += 1
            if len(pattern_analysis[length]["examples"]) < 3:
                pattern_analysis[length]["examples"].append(fecha_str)
            
            date_formats.append({
                "fecha": fecha_str,
                "length": length,
                "contains_dash": "-" in fecha_str,
                "contains_slash": "/" in fecha_str,
                "starts_with_digit": fecha_str[0].isdigit() if fecha_str else False
            })
        
        # Análisis de primeras compras por cliente
        first_purchase_query = text("""
            SELECT 
                cliente,
                MIN(fecha) as primera_compra,
                COUNT(*) as total_registros
            FROM client_data 
            WHERE cliente IS NOT NULL 
            AND fecha IS NOT NULL 
            GROUP BY cliente
            ORDER BY primera_compra
            LIMIT 10
        """)
        
        first_purchases = db.execute(first_purchase_query).fetchall()
        
        # Intentar extraer mes-año de diferentes formas
        month_extraction_attempts = []
        for purchase in first_purchases[:5]:
            fecha_str = str(purchase.primera_compra)
            attempts = {
                "original": fecha_str,
                "substring_7": fecha_str[:7] if len(fecha_str) >= 7 else None,
                "split_dash": fecha_str.split('-')[:2] if '-' in fecha_str else None,
                "split_slash": fecha_str.split('/')[:2] if '/' in fecha_str else None
            }
            month_extraction_attempts.append(attempts)
        
        return {
            "success": True,
            "total_records_with_dates": len(sample_dates),
            "pattern_analysis": pattern_analysis,
            "sample_dates": date_formats,
            "first_purchases_sample": [
                {
                    "cliente": row.cliente,
                    "primera_compra": row.primera_compra,
                    "total_registros": row.total_registros
                }
                for row in first_purchases
            ],
            "month_extraction_attempts": month_extraction_attempts,
            "recommendations": [
                "Revisa los patrones de fecha más comunes",
                "Verifica si necesitas convertir el formato antes de extraer mes-año",
                "Los datos deben estar en formato YYYY-MM-DD para el análisis automático"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error en análisis de fechas: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

        # AGREGAR este endpoint temporalmente en main.py para debug

@app.get("/debug/check-tipo-cliente")
async def debug_check_tipo_cliente_column(db: Session = Depends(get_database)):
    """Debug: Revisar qué datos hay en la columna tipo_cliente"""
    try:
        # Revisar todas las columnas disponibles
        columns_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'client_data'
            ORDER BY column_name
        """)
        columns_result = db.execute(columns_query).fetchall()
        available_columns = [row.column_name for row in columns_result]
        
        # Revisar valores únicos en tipo_cliente
        valores_query = text("""
            SELECT 
                tipo_cliente,
                COUNT(*) as cantidad_registros,
                COUNT(DISTINCT cliente) as clientes_unicos,
                SUM(CASE WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' THEN venta::numeric ELSE 0 END) as total_ventas
            FROM client_data 
            WHERE tipo_cliente IS NOT NULL 
            AND TRIM(tipo_cliente) != ''
            GROUP BY tipo_cliente
            ORDER BY total_ventas DESC
        """)
        valores_result = db.execute(valores_query).fetchall()
        
        # También revisar tipo_de_cliente para comparar
        valores_query_2 = text("""
            SELECT 
                tipo_de_cliente,
                COUNT(*) as cantidad_registros,
                COUNT(DISTINCT cliente) as clientes_unicos,
                SUM(CASE WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' THEN venta::numeric ELSE 0 END) as total_ventas
            FROM client_data 
            WHERE tipo_de_cliente IS NOT NULL 
            AND TRIM(tipo_de_cliente) != ''
            GROUP BY tipo_de_cliente
            ORDER BY total_ventas DESC
        """)
        valores_result_2 = db.execute(valores_query_2).fetchall()
        
        # Contar registros totales
        total_query = text("SELECT COUNT(*) as total FROM client_data")
        total_result = db.execute(total_query).fetchone()
        
        return {
            "success": True,
            "total_registros": total_result.total,
            "columnas_disponibles": available_columns,
            "datos_tipo_cliente": [
                {
                    "categoria": row.tipo_cliente,
                    "registros": row.cantidad_registros,
                    "clientes_unicos": row.clientes_unicos,
                    "total_ventas": float(row.total_ventas) if row.total_ventas else 0
                } for row in valores_result
            ],
            "datos_tipo_de_cliente": [
                {
                    "categoria": row.tipo_de_cliente,
                    "registros": row.cantidad_registros,
                    "clientes_unicos": row.clientes_unicos,
                    "total_ventas": float(row.total_ventas) if row.total_ventas else 0
                } for row in valores_result_2
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# REEMPLAZAR el endpoint principal con esta versión más robusta

# REEMPLAZAR el endpoint get_sales_by_type_detailed_robust con esta versión corregida

@app.get("/clients/analytics/sales-by-type-detailed")
async def get_sales_by_type_detailed_robust(db: Session = Depends(get_database)):
    """Análisis detallado ROBUSTO usando tipo_cliente con tipos de datos corregidos"""
    try:
        logger.info("🔍 Iniciando análisis robusto de tipo_cliente...")
        
        # Importar Decimal para manejo correcto de tipos
        from decimal import Decimal
        
        # Primero verificar qué columnas existen
        check_columns = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'client_data' 
            AND column_name IN ('tipo_cliente', 'tipo_de_cliente')
        """)
        columns_exist = db.execute(check_columns).fetchall()
        existing_columns = [row.column_name for row in columns_exist]
        logger.info(f"📋 Columnas encontradas: {existing_columns}")
        
        # Verificar si existe tipo_cliente
        if 'tipo_cliente' not in existing_columns:
            logger.error("❌ Columna 'tipo_cliente' no existe en la tabla")
            return {
                "success": False,
                "message": "La columna 'tipo_cliente' no existe en la base de datos",
                "available_columns": existing_columns,
                "data": [],
                "pie_data": [],
                "resumen": {}
            }
        
        # Query principal con manejo robusto de errores
        query = text("""
            SELECT 
                CASE 
                    WHEN tipo_cliente IS NULL OR TRIM(tipo_cliente) = '' THEN 'Sin categoría'
                    ELSE TRIM(tipo_cliente)
                END as tipo_cliente_clean,
                COUNT(DISTINCT cliente) as num_clientes,
                COUNT(*) as num_transacciones,
                ROUND(CAST(SUM(
                    CASE 
                        WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN venta::numeric
                        ELSE 0
                    END
                ) AS NUMERIC), 2) as total_ventas,
                ROUND(CAST(AVG(
                    CASE 
                        WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN venta::numeric
                        ELSE 0
                    END
                ) AS NUMERIC), 2) as venta_promedio,
                ROUND(CAST(SUM(
                    CASE 
                        WHEN mb IS NOT NULL AND mb::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN mb::numeric
                        ELSE 0
                    END
                ) AS NUMERIC), 2) as total_mb
            FROM client_data 
            WHERE cliente IS NOT NULL 
            AND TRIM(cliente) != ''
            AND venta IS NOT NULL
            GROUP BY 
                CASE 
                    WHEN tipo_cliente IS NULL OR TRIM(tipo_cliente) = '' THEN 'Sin categoría'
                    ELSE TRIM(tipo_cliente)
                END
            HAVING SUM(
                CASE 
                    WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                    THEN venta::numeric
                    ELSE 0
                END
            ) > 0
            ORDER BY total_ventas DESC
        """)
        
        result = db.execute(query).fetchall()
        
        # Log de debugging
        logger.info(f"📊 Query ejecutada, {len(result)} resultados encontrados")
        if result:
            for i, row in enumerate(result[:5]):
                logger.info(f"  {i+1}. {row.tipo_cliente_clean}: {row.total_ventas} ventas, {row.num_clientes} clientes")
        
        # Verificar que tenemos datos
        if not result:
            logger.warning("⚠️ No se encontraron datos en tipo_cliente")
            
            # Intentar diagnóstico adicional
            diagnostic_query = text("""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT tipo_cliente) as distinct_tipos,
                    COUNT(CASE WHEN tipo_cliente IS NOT NULL THEN 1 END) as non_null_tipos,
                    COUNT(CASE WHEN venta IS NOT NULL THEN 1 END) as non_null_ventas
                FROM client_data
            """)
            diagnostic = db.execute(diagnostic_query).fetchone()
            
            return {
                "success": False,
                "message": "No se encontraron datos válidos en tipo_cliente",
                "diagnostic": {
                    "total_rows": diagnostic.total_rows,
                    "distinct_tipos": diagnostic.distinct_tipos,
                    "non_null_tipos": diagnostic.non_null_tipos,
                    "non_null_ventas": diagnostic.non_null_ventas
                },
                "data": [],
                "pie_data": [],
                "resumen": {}
            }
        
        # Función para convertir Decimal a float de manera segura
        def safe_float(value):
            if value is None:
                return 0.0
            if isinstance(value, Decimal):
                return float(value)
            if isinstance(value, (int, float)):
                return float(value)
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
        
        # Calcular totales generales - CONVERSIÓN SEGURA
        total_ventas_general = sum(safe_float(row.total_ventas) for row in result)
        total_tipos = len(result)
        total_mb_general = sum(safe_float(row.total_mb) for row in result)
        
        logger.info(f"📊 Total ventas general: {total_ventas_general:,.2f}")
        logger.info(f"📊 Total categorías encontradas: {total_tipos}")
        
        # Procesar todos los datos y calcular porcentajes - CONVERSIÓN SEGURA
        all_data = []
        for row in result:
            total_ventas_row = safe_float(row.total_ventas)
            total_mb_row = safe_float(row.total_mb)
            venta_promedio_row = safe_float(row.venta_promedio)
            
            porcentaje = (total_ventas_row / total_ventas_general * 100) if total_ventas_general > 0 else 0
            
            all_data.append({
                "tipo_cliente": row.tipo_cliente_clean,
                "num_clientes": row.num_clientes,
                "num_transacciones": row.num_transacciones,
                "total_ventas": total_ventas_row,
                "total_mb": total_mb_row,
                "venta_promedio": venta_promedio_row,
                "porcentaje": round(porcentaje, 1)
            })
        
        # Separar TOP 5 vs OTROS
        top_5 = all_data[:5]  # Los 5 primeros
        otros = all_data[5:]  # El resto
        
        # Preparar datos para el gráfico
        data_for_chart = top_5.copy()
        
        # Si hay más de 5 categorías, agrupar el resto como "Otros"
        if otros:
            # CONVERSIÓN SEGURA para cálculos de "Otros"
            otros_total_ventas = sum(item["total_ventas"] for item in otros)
            otros_total_mb = sum(item["total_mb"] for item in otros)
            otros_num_clientes = sum(item["num_clientes"] for item in otros)
            otros_num_transacciones = sum(item["num_transacciones"] for item in otros)
            otros_porcentaje = (otros_total_ventas / total_ventas_general * 100) if total_ventas_general > 0 else 0
            
            # Agregar categoría "Otros"
            data_for_chart.append({
                "tipo_cliente": "Otros",
                "num_clientes": otros_num_clientes,
                "num_transacciones": otros_num_transacciones,
                "total_ventas": otros_total_ventas,
                "total_mb": otros_total_mb,
                "venta_promedio": otros_total_ventas / len(otros) if otros else 0,
                "porcentaje": round(otros_porcentaje, 1),
                "is_others_category": True,
                "otros_count": len(otros),
                "otros_detail": [item["tipo_cliente"] for item in otros]
            })
            
            logger.info(f"📦 Agrupados {len(otros)} categorías como 'Otros': {[item['tipo_cliente'] for item in otros[:3]]}{'...' if len(otros) > 3 else ''}")
        
        # Preparar datos para el gráfico pie con colores
        colors = ['#8884D8', '#82CA9D', '#FFC658', '#FF7C7C', '#8DD1E1', '#D084D0']
        
        pie_data = []
        for i, item in enumerate(data_for_chart):
            pie_data.append({
                "name": item["tipo_cliente"],
                "value": item["total_ventas"],
                "percentage": item["porcentaje"],
                "color": colors[i % len(colors)],
                "num_clientes": item["num_clientes"],
                "num_transacciones": item["num_transacciones"],
                "total_mb": item["total_mb"],
                "is_others": item.get("is_others_category", False),
                "otros_count": item.get("otros_count", 0),
                "otros_detail": item.get("otros_detail", [])
            })
        
        # Resumen general - CONVERSIÓN SEGURA
        resumen = {
            "total_tipos": total_tipos,
            "total_ventas": total_ventas_general,
            "total_mb": total_mb_general,
            "margen_general": round((total_mb_general / total_ventas_general * 100), 1) if total_ventas_general > 0 else 0,
            "showing_top": len(top_5),
            "grouped_as_others": len(otros)
        }
        
        logger.info(f"✅ Análisis completado exitosamente")
        logger.info(f"🎯 Top 5: {[item['tipo_cliente'] for item in top_5]}")
        
        return {
            "success": True,
            "data": data_for_chart,  # Para tabla/lista detallada
            "pie_data": pie_data,    # Para gráfico pie
            "resumen": resumen,
            "all_data": all_data,    # Todos los datos sin agrupar
            "message": f"Análisis exitoso: {total_tipos} categorías, mostrando Top 5 + {len(otros)} como 'Otros'"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en análisis robusto: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "traceback": traceback.format_exc(),
            "data": [],
            "pie_data": [],
            "resumen": {}
        }

        # REEMPLAZA ESTA FUNCIÓN EN TU main.py


# TAMBIÉN AGREGA ESTE ENDPOINT DE DIAGNÓSTICO TEMPORAL
@app.get("/debug/test-acquisition")
async def debug_test_acquisition(db: Session = Depends(get_database)):
    """Endpoint temporal para debuggear la adquisición de clientes"""
    try:
        # Datos básicos
        total_count = db.execute(text("SELECT COUNT(*) FROM client_data")).scalar()
        
        # Muestra de fechas
        sample_dates_query = text("""
            SELECT DISTINCT fecha, COUNT(*) as count
            FROM client_data 
            WHERE fecha IS NOT NULL 
            AND fecha != ''
            GROUP BY fecha
            ORDER BY count DESC, fecha
            LIMIT 10
        """)
        
        sample_dates = db.execute(sample_dates_query).fetchall()
        
        # Clientes únicos con sus primeras fechas
        first_purchases_query = text("""
            SELECT 
                cliente,
                MIN(fecha) as primera_compra,
                COUNT(*) as total_registros
            FROM client_data 
            WHERE cliente IS NOT NULL 
            AND fecha IS NOT NULL 
            GROUP BY cliente
            ORDER BY primera_compra
            LIMIT 10
        """)
        
        first_purchases = db.execute(first_purchases_query).fetchall()
        
        return {
            "success": True,
            "total_records": total_count,
            "sample_dates": [
                {"fecha": row.fecha, "count": row.count} 
                for row in sample_dates
            ],
            "first_purchases_sample": [
                {
                    "cliente": row.cliente,
                    "primera_compra": row.primera_compra,
                    "total_registros": row.total_registros
                }
                for row in first_purchases
            ],
            "message": "Diagnóstico de datos para tendencia de adquisición"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }



@app.get("/products/analytics/top_products_6")
async def get_top_products_6_postgresql():
    """Obtiene los top 6 productos más vendidos desde PostgreSQL"""
    try:
        db = SessionLocal()
        try:
            logger.info("🔍 Obteniendo top 6 productos desde PostgreSQL...")
            
            result = db.execute(text("""
                SELECT 
                    product,
                    SUM(value) as total_sales,
                    SUM(value - cost) as total_margin,
                    COUNT(*) as quantity,
                    AVG(value) as avg_sale
                FROM client_data
                WHERE product IS NOT NULL 
                  AND value IS NOT NULL
                  AND value > 0
                GROUP BY product
                ORDER BY total_sales DESC
                LIMIT 6
            """))
            
            products = []
            for row in result:
                products.append({
                    "product": row[0],
                    "total_sales": float(row[1]) if row[1] else 0,
                    "total_margin": float(row[2]) if row[2] else 0,
                    "quantity": int(row[3]),
                    "avg_sale": float(row[4]) if row[4] else 0
                })
            
            logger.info(f"✅ Top 6 productos obtenidos: {len(products)} productos")
            
            return {
                "success": True,
                "products": products,
                "total": len(products)
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo top 6 productos: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "products": [],
            "error": str(e)
        }


        # 1. Modificar comparative-bars existente:
@app.get("/products/analytics/comparative-bars")
async def get_products_comparative_bars(
    period: str = "12m",  # 3m, 6m, 12m
    limit: int = 15,
    db: Session = Depends(get_database)
):
    """
    Gráfico de barras comparativo de productos: Ventas de productos más populares
    en diferentes períodos (3, 6 y 12 meses)
    Variables: Articulo, Venta, Cantidad, Fecha
    """
    try:
        # Definir el período
        period_mapping = {
            "3m": 3,
            "6m": 6, 
            "12m": 12
        }
        months = period_mapping.get(period, 12)
        
        # Consulta para obtener productos más vendidos por período
        query = text("""
            WITH product_sales AS (
                SELECT 
                    COALESCE(articulo, 'Producto sin nombre') as producto,
                    COALESCE(categoria, 'Sin categoría') as categoria,
                    COALESCE(proveedor, 'Sin proveedor') as proveedor,
                    SUM(COALESCE(venta, 0)) as total_ventas,
                    SUM(COALESCE(cantidad, 0)) as total_cantidad,
                    SUM(COALESCE(costo, 0)) as total_costo,
                    SUM(COALESCE(mb, 0)) as total_margen,
                    COUNT(DISTINCT factura) as num_facturas,
                    COUNT(DISTINCT cliente) as num_clientes,
                    CASE 
                        WHEN SUM(COALESCE(venta, 0)) > 0 THEN
                            ROUND((SUM(COALESCE(mb, 0)) / SUM(COALESCE(venta, 0))) * 100, 2)
                        ELSE 0
                    END as margen_porcentaje
                FROM client_data 
                WHERE articulo IS NOT NULL AND articulo != ''
                    AND fecha::date >= CURRENT_DATE - INTERVAL ':months months'
                GROUP BY articulo, categoria, proveedor
            )
            SELECT 
                producto,
                categoria,
                proveedor,
                total_ventas,
                total_cantidad,
                total_costo,
                total_margen,
                margen_porcentaje,
                num_facturas,
                num_clientes
            FROM product_sales
            WHERE total_ventas > 0
            ORDER BY total_ventas DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {"months": months, "limit": limit}).fetchall()
        
        data = []
        for row in result:
            data.append({
                "producto": row.producto,
                "categoria": row.categoria,
                "proveedor": row.proveedor,
                "total_ventas": float(row.total_ventas),
                "total_cantidad": float(row.total_cantidad),
                "total_costo": float(row.total_costo),
                "total_margen": float(row.total_margen),
                "margen_porcentaje": float(row.margen_porcentaje),
                "num_facturas": row.num_facturas,
                "num_clientes": row.num_clientes
            })
        
        return {
            "success": True,
            "data": data,
            "period": f"Últimos {months} meses",
            "chart_type": "comparative_bar",
            "description": f"Top {limit} productos más vendidos en los últimos {months} meses"
        }
        
    except Exception as e:
        logger.error(f"Error en gráfico comparativo de productos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

        # 2. Modificar trend-lines existente:
@app.get("/products/analytics/trend-lines")
async def get_products_trend_lines(
    top_products: int = 10,
    db: Session = Depends(get_database)
):
    """
    Gráfico de líneas de tendencias de productos: Tendencias de ventas a lo largo del tiempo
    Variables: Articulo, Fecha, Venta, Cantidad
    """
    try:
        # Primero obtener los productos más vendidos
        top_products_query = text("""
            SELECT 
                COALESCE(articulo, 'Producto sin nombre') as producto,
                SUM(COALESCE(venta, 0)) as total_ventas
            FROM client_data 
            WHERE articulo IS NOT NULL AND articulo != ''
                AND fecha IS NOT NULL
            GROUP BY articulo
            ORDER BY total_ventas DESC
            LIMIT :top_products
        """)
        
        top_products_result = db.execute(top_products_query, {"top_products": top_products}).fetchall()
        top_product_names = [row.producto for row in top_products_result]
        
        if not top_product_names:
            return {
                "success": True,
                "data": [],
                "message": "No se encontraron productos con datos válidos"
            }
        
        # Obtener tendencias mensuales para estos productos
        trend_query = text("""
            SELECT 
                COALESCE(articulo, 'Producto sin nombre') as producto,
                TO_CHAR(fecha::date, 'YYYY-MM') as mes,
                SUM(COALESCE(venta, 0)) as ventas_mes,
                SUM(COALESCE(cantidad, 0)) as cantidad_mes,
                COUNT(DISTINCT factura) as facturas_mes,
                AVG(COALESCE(venta, 0)) as venta_promedio
            FROM client_data 
            WHERE articulo = ANY(:product_names)
                AND fecha IS NOT NULL
                AND fecha::date >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY articulo, TO_CHAR(fecha::date, 'YYYY-MM')
            ORDER BY mes ASC, ventas_mes DESC
        """)
        
        result = db.execute(trend_query, {"product_names": top_product_names}).fetchall()
        
        data = []
        for row in result:
            data.append({
                "producto": row.producto,
                "mes": row.mes,
                "ventas_mes": float(row.ventas_mes),
                "cantidad_mes": float(row.cantidad_mes),
                "facturas_mes": row.facturas_mes,
                "venta_promedio": float(row.venta_promedio)
            })
        
        return {
            "success": True,
            "data": data,
            "chart_type": "line_trend",
            "description": f"Tendencias mensuales de los top {top_products} productos más vendidos"
        }
        
    except Exception as e:
        logger.error(f"Error en tendencias de productos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/analytics/rotation-speed")
async def get_rotation_speed(limit: int = 10, db: Session = Depends(get_database)):
    """
    Análisis de velocidad de rotación de productos basado en datos reales del CSV
    Calcula rotación basada en:
    - Frecuencia de transacciones por mes
    - Cantidad total vendida
    - Número de clientes únicos
    - Distribución temporal de ventas
    """
    try:
        # Query mejorada para calcular velocidad de rotación real
        query = text("""
            WITH product_metrics AS (
                SELECT 
                    COALESCE(articulo, 'Producto sin nombre') as producto,
                    COALESCE(categoria, 'Sin categoría') as categoria,
                    COALESCE(proveedor, 'Sin proveedor') as proveedor,
                    
                    -- Métricas de transacciones
                    COUNT(DISTINCT factura) as total_facturas,
                    COUNT(DISTINCT cliente) as clientes_unicos,
                    SUM(COALESCE(cantidad, 0)) as cantidad_total,
                    SUM(COALESCE(venta, 0)) as ventas_totales,
                    
                    -- Métricas temporales
                    COUNT(DISTINCT 
                        CASE 
                            WHEN fecha IS NOT NULL AND fecha != '' THEN
                                SUBSTRING(fecha, 1, 7)  -- Extraer YYYY-MM
                            ELSE NULL
                        END
                    ) as meses_activos,
                    
                    -- Calcular días únicos de actividad
                    COUNT(DISTINCT 
                        CASE 
                            WHEN fecha IS NOT NULL AND fecha != '' THEN
                                SUBSTRING(fecha, 1, 10)  -- Extraer YYYY-MM-DD
                            ELSE NULL
                        END
                    ) as dias_activos,
                    
                    -- Primera y última venta para calcular período
                    MIN(
                        CASE 
                            WHEN fecha IS NOT NULL AND fecha != '' THEN fecha
                            ELSE NULL
                        END
                    ) as primera_venta,
                    MAX(
                        CASE 
                            WHEN fecha IS NOT NULL AND fecha != '' THEN fecha
                            ELSE NULL
                        END
                    ) as ultima_venta
                    
                FROM client_data 
                WHERE articulo IS NOT NULL AND articulo != ''
                    AND cantidad IS NOT NULL AND cantidad > 0
                    AND venta IS NOT NULL AND venta > 0
                GROUP BY articulo, categoria, proveedor
                HAVING SUM(COALESCE(venta, 0)) > 500  -- Filtrar productos con ventas mínimas
            ),
            rotation_analysis AS (
                SELECT 
                    producto,
                    categoria,
                    proveedor,
                    total_facturas,
                    clientes_unicos,
                    cantidad_total,
                    ventas_totales,
                    meses_activos,
                    dias_activos,
                    primera_venta,
                    ultima_venta,
                    
                    -- Calcular velocidad de rotación (transacciones por mes)
                    CASE 
                        WHEN meses_activos > 0 THEN 
                            ROUND(CAST(total_facturas AS FLOAT) / GREATEST(meses_activos, 1), 2)
                        ELSE 0
                    END as rotacion_por_mes,
                    
                    -- Calcular índice de rotación alternativo (basado en clientes únicos)
                    CASE 
                        WHEN meses_activos > 0 THEN 
                            ROUND(CAST(clientes_unicos AS FLOAT) / GREATEST(meses_activos, 1), 2)
                        ELSE 0
                    END as clientes_por_mes,
                    
                    -- Calcular frecuencia de compra promedio
                    CASE 
                        WHEN dias_activos > 0 THEN 
                            ROUND(CAST(total_facturas AS FLOAT) / GREATEST(dias_activos, 1) * 30, 2)
                        ELSE 0
                    END as frecuencia_mensual,
                    
                    -- Promedio de venta por transacción
                    ROUND(CAST(ventas_totales AS FLOAT) / GREATEST(total_facturas, 1), 2) as venta_promedio_transaccion
                    
                FROM product_metrics
            ),
            final_rotation AS (
                SELECT 
                    producto,
                    categoria,
                    proveedor,
                    total_facturas,
                    clientes_unicos,
                    cantidad_total,
                    ventas_totales,
                    meses_activos,
                    rotacion_por_mes,
                    clientes_por_mes,
                    frecuencia_mensual,
                    venta_promedio_transaccion,
                    
                    -- Velocidad de rotación final (promedio ponderado)
                    ROUND(
                        (rotacion_por_mes * 0.6 + clientes_por_mes * 0.4), 2
                    ) as velocidad_rotacion,
                    
                    -- Categorizar velocidad de rotación
                    CASE 
                        WHEN (rotacion_por_mes * 0.6 + clientes_por_mes * 0.4) >= 6.0 THEN 'Rápida'
                        WHEN (rotacion_por_mes * 0.6 + clientes_por_mes * 0.4) >= 3.0 THEN 'Media'
                        ELSE 'Lenta'
                    END as categoria_rotacion,
                    
                    -- Calcular score de eficiencia
                    ROUND(
                        (rotacion_por_mes * 0.4) + 
                        (clientes_por_mes * 0.3) + 
                        (LEAST(frecuencia_mensual / 10, 1) * 0.3), 2
                    ) as score_eficiencia
                    
                FROM rotation_analysis
            )
            SELECT 
                producto,
                categoria,
                proveedor,
                total_facturas,
                clientes_unicos,
                CAST(cantidad_total AS INTEGER) as cantidad_total,
                CAST(ventas_totales AS INTEGER) as ventas_totales,
                meses_activos,
                velocidad_rotacion,
                categoria_rotacion,
                rotacion_por_mes,
                clientes_por_mes,
                frecuencia_mensual,
                venta_promedio_transaccion,
                score_eficiencia
            FROM final_rotation
            WHERE velocidad_rotacion > 0
            ORDER BY velocidad_rotacion DESC, ventas_totales DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {"limit": limit}).fetchall()
        
        if not result:
            logger.warning("No se encontraron datos de rotación, usando datos de ejemplo")
            # Datos de ejemplo si no hay resultados
            return {
                "success": True,
                "data": [
                    {"producto": "NATROSOL 250 LR - 25 KG", "velocidad_rotacion": 8.5, "categoria": "Rápida"},
                    {"producto": "BYK 037 - 185 KG", "velocidad_rotacion": 7.2, "categoria": "Rápida"},
                    {"producto": "KRONOS 2360 - 25 KG", "velocidad_rotacion": 6.8, "categoria": "Media"},
                    {"producto": "CLAYTONE APA - 12.500 KG", "velocidad_rotacion": 5.4, "categoria": "Media"},
                    {"producto": "TEXANOL - 200 KG", "velocidad_rotacion": 4.1, "categoria": "Lenta"},
                    {"producto": "EPOXI RESIN SM 90FR", "velocidad_rotacion": 3.8, "categoria": "Media"},
                    {"producto": "TITANIO DIOXIDO", "velocidad_rotacion": 3.2, "categoria": "Media"},
                    {"producto": "HEXAMETAFOSFATO DE SODIO", "velocidad_rotacion": 2.9, "categoria": "Lenta"}
                ],
                "chart_type": "rotation_analysis",
                "description": "Análisis de velocidad de rotación (datos de ejemplo)",
                "note": "Usando datos de ejemplo - verificar conexión con base de datos"
            }
        
        data = []
        for row in result:
            # Determinar color según categoría
            if row.categoria_rotacion == 'Rápida':
                color = '#27ae60'
            elif row.categoria_rotacion == 'Media':
                color = '#f39c12'
            else:
                color = '#e74c3c'
            
            data.append({
                "producto": row.producto,
                "categoria": row.categoria,
                "proveedor": row.proveedor,
                "total_facturas": row.total_facturas,
                "clientes_unicos": row.clientes_unicos,
                "cantidad_total": row.cantidad_total,
                "ventas_totales": row.ventas_totales,
                "meses_activos": row.meses_activos,
                "velocidad_rotacion": float(row.velocidad_rotacion),
                "categoria": row.categoria_rotacion,
                "rotacion_por_mes": float(row.rotacion_por_mes),
                "clientes_por_mes": float(row.clientes_por_mes),
                "frecuencia_mensual": float(row.frecuencia_mensual),
                "venta_promedio_transaccion": float(row.venta_promedio_transaccion),
                "score_eficiencia": float(row.score_eficiencia),
                "color": color
            })
        
        # Estadísticas adicionales
        total_productos = len(data)
        productos_rapidos = len([p for p in data if p['categoria'] == 'Rápida'])
        productos_medios = len([p for p in data if p['categoria'] == 'Media'])
        productos_lentos = len([p for p in data if p['categoria'] == 'Lenta'])
        
        velocidad_promedio = sum(p['velocidad_rotacion'] for p in data) / total_productos if total_productos > 0 else 0
        
        return {
            "success": True,
            "data": data,
            "statistics": {
                "total_productos": total_productos,
                "productos_rapidos": productos_rapidos,
                "productos_medios": productos_medios,
                "productos_lentos": productos_lentos,
                "velocidad_promedio": round(velocidad_promedio, 2),
                "distribucion": {
                    "rapida_pct": round((productos_rapidos / total_productos) * 100, 1) if total_productos > 0 else 0,
                    "media_pct": round((productos_medios / total_productos) * 100, 1) if total_productos > 0 else 0,
                    "lenta_pct": round((productos_lentos / total_productos) * 100, 1) if total_productos > 0 else 0
                }
            },
            "chart_type": "rotation_analysis",
            "description": f"Análisis de velocidad de rotación - Top {limit} productos",
            "methodology": {
                "calculation": "Promedio ponderado de transacciones/mes (60%) y clientes únicos/mes (40%)",
                "categories": {
                    "rapida": "≥ 6.0 rotaciones/mes",
                    "media": "3.0 - 5.9 rotaciones/mes", 
                    "lenta": "< 3.0 rotaciones/mes"
                },
                "filters": "Productos con ventas > S/ 500 y cantidad > 0"
            }
        }
        
    except Exception as e:
        logger.error(f"Error en análisis de rotación: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Devolver datos de ejemplo en caso de error
        return {
            "success": True,
            "data": [
                {"producto": "NATROSOL 250 LR - 25 KG", "velocidad_rotacion": 8.5, "categoria": "Rápida", "color": "#27ae60"},
                {"producto": "BYK 037 - 185 KG", "velocidad_rotacion": 7.2, "categoria": "Rápida", "color": "#27ae60"},
                {"producto": "KRONOS 2360 - 25 KG", "velocidad_rotacion": 6.8, "categoria": "Media", "color": "#f39c12"},
                {"producto": "CLAYTONE APA - 12.500 KG", "velocidad_rotacion": 5.4, "categoria": "Media", "color": "#f39c12"},
                {"producto": "TEXANOL - 200 KG", "velocidad_rotacion": 4.1, "categoria": "Lenta", "color": "#e74c3c"},
                {"producto": "EPOXI RESIN SM 90FR", "velocidad_rotacion": 3.8, "categoria": "Media", "color": "#f39c12"},
                {"producto": "TITANIO DIOXIDO", "velocidad_rotacion": 3.2, "categoria": "Media", "color": "#f39c12"},
                {"producto": "HEXAMETAFOSFATO DE SODIO", "velocidad_rotacion": 2.9, "categoria": "Lenta", "color": "#e74c3c"}
            ],
            "error": f"Error calculando rotación: {str(e)}",
            "fallback": True,
            "chart_type": "rotation_analysis",
            "description": "Análisis de velocidad de rotación (datos de respaldo)"
        }

# ===== MODIFICAR ENDPOINTS EXISTENTES PARA SOPORTAR FILTROS DE PERÍODO =====
# 3. Modificar pareto-80-20 existente:
@app.get("/products/analytics/pareto-80-20")
async def get_products_pareto_analysis(db: Session = Depends(get_database)):
    """
    Gráfico de Pareto (80/20): 20% de productos que generan 80% de las ventas
    Variables: Articulo, Venta, participación acumulada
    """
    try:
        # Consulta para análisis de Pareto
        query = text("""
            WITH product_sales AS (
                SELECT 
                    COALESCE(articulo, 'Producto sin nombre') as producto,
                    COALESCE(categoria, 'Sin categoría') as categoria,
                    SUM(COALESCE(venta, 0)) as total_ventas,
                    SUM(COALESCE(cantidad, 0)) as total_cantidad,
                    SUM(COALESCE(mb, 0)) as total_margen
                FROM client_data 
                WHERE articulo IS NOT NULL AND articulo != ''
                GROUP BY articulo, categoria
            ),
            ranked_products AS (
                SELECT 
                    producto,
                    categoria,
                    total_ventas,
                    total_cantidad,
                    total_margen,
                    ROW_NUMBER() OVER (ORDER BY total_ventas DESC) as ranking,
                    SUM(total_ventas) OVER () as ventas_totales
                FROM product_sales
                WHERE total_ventas > 0
            ),
            pareto_analysis AS (
                SELECT 
                    producto,
                    categoria,
                    total_ventas,
                    total_cantidad,
                    total_margen,
                    ranking,
                    ventas_totales,
                    ROUND((total_ventas / ventas_totales) * 100, 2) as participacion_individual,
                    ROUND((SUM(total_ventas) OVER (ORDER BY ranking) / ventas_totales) * 100, 2) as participacion_acumulada,
                    COUNT(*) OVER () as total_productos
                FROM ranked_products
            )
            SELECT 
                producto,
                categoria,
                total_ventas,
                total_cantidad,
                total_margen,
                ranking,
                participacion_individual,
                participacion_acumulada,
                total_productos,
                CASE 
                    WHEN participacion_acumulada <= 80 THEN 'Top 80%'
                    WHEN participacion_acumulada <= 95 THEN 'Medio 15%'
                    ELSE 'Bottom 5%'
                END as categoria_pareto,
                CASE 
                    WHEN participacion_acumulada <= 80 THEN true
                    ELSE false
                END as es_top_80
            FROM pareto_analysis
            ORDER BY ranking
            LIMIT 200
        """)
        
        result = db.execute(query).fetchall()
        
        data = []
        top_80_count = 0
        total_products = 0
        
        for row in result:
            total_products = row.total_productos
            if row.es_top_80:
                top_80_count += 1
                
            data.append({
                "producto": row.producto,
                "categoria": row.categoria,
                "total_ventas": float(row.total_ventas),
                "total_cantidad": float(row.total_cantidad),
                "total_margen": float(row.total_margen),
                "ranking": row.ranking,
                "participacion_individual": float(row.participacion_individual),
                "participacion_acumulada": float(row.participacion_acumulada),
                "categoria_pareto": row.categoria_pareto,
                "es_top_80": row.es_top_80
            })
        
        # Calcular estadísticas del Pareto
        pareto_stats = {
            "total_productos": total_products,
            "productos_top_80": top_80_count,
            "porcentaje_productos_top_80": round((top_80_count / total_products) * 100, 1) if total_products > 0 else 0,
            "cumple_regla_80_20": top_80_count <= (total_products * 0.3)  # Típicamente el 20-30% de productos genera el 80%
        }
        
        return {
            "success": True,
            "data": data,
            "pareto_stats": pareto_stats,
            "chart_type": "pareto",
            "description": f"Análisis de Pareto: {top_80_count} productos ({pareto_stats['porcentaje_productos_top_80']}%) generan el 80% de las ventas"
        }
        
    except Exception as e:
        logger.error(f"Error en análisis de Pareto: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



        # ENDPOINT PARA OBTENER COMERCIALES DEL CSV
# Agregar este endpoint al archivo main.py o al router correspondiente

@app.get("/analytics/comerciales")
async def get_comerciales():
    """
    Obtiene la lista única de comerciales del CSV cargado
    """
    try:
        if not hasattr(csv_service, 'data') or csv_service.data is None:
            return {
                "success": False,
                "error": "No hay datos CSV cargados",
                "comerciales": []
            }
        
        df = csv_service.data
        logger.info(f"📊 Obteniendo comerciales de {len(df)} registros")
        
        # Buscar columnas que puedan contener información de comerciales
        possible_columns = [col for col in df.columns 
                          if any(keyword in col.lower() 
                               for keyword in ['comercial', 'vendedor', 'agente', 'seller', 'sales'])]
        
        logger.info(f"🔍 Columnas posibles para comerciales: {possible_columns}")
        
        if not possible_columns:
            # Si no encuentra columnas específicas, buscar patrones en los datos
            logger.warning("⚠️ No se encontraron columnas específicas de comerciales")
            return {
                "success": True,
                "comerciales": [],
                "message": "No se encontraron columnas de comerciales en el CSV"
            }
        
        # Usar la primera columna encontrada
        comercial_column = possible_columns[0]
        logger.info(f"📋 Usando columna de comerciales: {comercial_column}")
        
        # Obtener valores únicos de comerciales
        comerciales_raw = df[comercial_column].dropna().unique().tolist()
        
        # Limpiar y filtrar comerciales
        comerciales_clean = []
        for comercial in comerciales_raw:
            if comercial and str(comercial).strip() and str(comercial).strip() != '':
                comercial_clean = str(comercial).strip()
                if comercial_clean not in comerciales_clean:
                    comerciales_clean.append(comercial_clean)
        
        # Ordenar alfabéticamente
        comerciales_clean.sort()
        
        logger.info(f"✅ Encontrados {len(comerciales_clean)} comerciales únicos")
        logger.info(f"📋 Primeros comerciales: {comerciales_clean[:5]}")
        
        return {
            "success": True,
            "comerciales": comerciales_clean,
            "total_comerciales": len(comerciales_clean),
            "column_used": comercial_column,
            "total_records": len(df)
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo comerciales: {str(e)}")
        return {
            "success": False,
            "error": f"Error procesando comerciales: {str(e)}",
            "comerciales": []
        }


# MODIFICACIÓN AL ENDPOINT DE RECOMENDACIONES ML
# Modificar el endpoint existente de recomendaciones para incluir filtro por comercial

@app.get("/ml/cross-sell-recommendations")
async def get_cross_sell_recommendations_postgresql(
    limit: int = 50,
    min_probability: float = 0.3,
    comercial: Optional[str] = None,  # Filtro por comercial
    db: Session = Depends(get_database)
):
    """Obtener recomendaciones de venta cruzada usando datos REALES del CSV"""
    try:
        logger.info("🤖 Iniciando recomendaciones ML con datos reales...")
        
        # Query base para obtener datos agregados por cliente
        base_query = """
            SELECT 
                cliente,
                COALESCE(tipo_de_cliente, 'Sin tipo') as tipo_de_cliente,
                COALESCE(comercial, 'Sin asignar') as comercial,
                COALESCE(categoria, 'Sin categoría') as categoria,
                COALESCE(codigo, 'Sin código') as codigo_cliente,
                COALESCE(proveedor, 'Sin proveedor') as proveedor,
                
                -- Métricas agregadas
                COUNT(*) as num_transacciones,
                COUNT(DISTINCT factura) as num_facturas,
                SUM(COALESCE(cantidad, 0)) as cantidad_total,
                
                -- Valores monetarios
                ROUND(CAST(SUM(
                    CASE 
                        WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN venta::numeric
                        ELSE 0
                    END
                ) AS NUMERIC), 2) as venta_total,
                
                ROUND(CAST(SUM(
                    CASE 
                        WHEN costo IS NOT NULL AND costo::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN costo::numeric
                        ELSE 0
                    END
                ) AS NUMERIC), 2) as costo_total,
                
                ROUND(CAST(SUM(
                    CASE 
                        WHEN mb IS NOT NULL AND mb::text ~ '^[0-9]+\.?[0-9]*$' 
                        THEN mb::numeric
                        ELSE 0
                    END
                ) AS NUMERIC), 2) as mb_total,
                
                -- Fechas
                MIN(fecha) as primera_compra,
                MAX(fecha) as ultima_compra
                
            FROM client_data 
            WHERE cliente IS NOT NULL 
            AND TRIM(cliente) != ''
            {comercial_filter}
            GROUP BY cliente, tipo_de_cliente, comercial, categoria, codigo, proveedor
            HAVING SUM(
                CASE 
                    WHEN venta IS NOT NULL AND venta::text ~ '^[0-9]+\.?[0-9]*$' 
                    THEN venta::numeric
                    ELSE 0
                END
            ) > 0
            ORDER BY venta_total DESC
            LIMIT :limit_param
        """
        
        # Aplicar filtro de comercial si se especifica
        comercial_filter = ""
        query_params = {"limit_param": limit}
        
        if comercial and comercial.strip():
            comercial_filter = "AND comercial ILIKE :comercial"
            query_params["comercial"] = f"%{comercial.strip()}%"
        
        final_query = text(base_query.format(comercial_filter=comercial_filter))
        result = db.execute(final_query, query_params).fetchall()
        
        if not result:
            return {
                "success": False,
                "message": f"No se encontraron clientes{' para el comercial ' + comercial if comercial else ''}",
                "recommendations": []
            }
        
        # Convertir datos para ML
        client_data = []
        for row in result:
            client_dict = {
                "id": len(client_data) + 1,
                "cliente": row.cliente,
                "venta": float(row.venta_total or 0),
                "costo": float(row.costo_total or 0),
                "mb": float(row.mb_total or 0),
                "cantidad": float(row.cantidad_total or 0),
                "tipo_de_cliente": row.tipo_de_cliente,
                "categoria": row.categoria,
                "comercial": row.comercial,
                "proveedor": row.proveedor,
                "codigo_cliente": row.codigo_cliente,
                "num_transacciones": row.num_transacciones,
                "num_facturas": row.num_facturas,
                "primera_compra": row.primera_compra,
                "ultima_compra": row.ultima_compra
            }
            client_data.append(client_dict)
        
        # Usar ML service para predicciones
        if not ml_service.is_loaded:
            logger.warning("⚠️ Modelo ML no disponible, usando predicciones demo")
        
        all_predictions = ml_service.predict_cross_sell(client_data)
        
        # Filtrar por probabilidad mínima y enriquecer con datos reales
        filtered_recommendations = []
        for pred in all_predictions:
            if pred['prediction'] == 1 and pred['probability'] >= min_probability:
                # Encontrar datos originales del cliente
                original_data = next((c for c in client_data if c['cliente'] == pred['client_name']), {})
                
                # Enriquecer predicción con datos reales
                enriched_pred = {
                    **pred,
                    # Datos reales del CSV
                    "codigo_cliente": original_data.get('codigo_cliente', 'Sin código'),
                    "tipo_cliente": original_data.get('tipo_de_cliente', 'Sin tipo'),  # Corregido
                    "categoria": original_data.get('categoria', 'Sin categoría'),
                    "comercial": original_data.get('comercial', 'Sin asignar'),
                    "proveedor": original_data.get('proveedor', 'Sin proveedor'),
                    "num_transacciones": original_data.get('num_transacciones', 0),
                    "num_facturas": original_data.get('num_facturas', 0),
                    "primera_compra": original_data.get('primera_compra'),
                    "ultima_compra": original_data.get('ultima_compra'),
                    "cantidad_total": original_data.get('cantidad', 0),
                    "costo_total": original_data.get('costo', 0),
                    "mb_total": original_data.get('mb', 0)
                }
                
                filtered_recommendations.append(enriched_pred)
        
        # Ordenar por probabilidad descendente
        filtered_recommendations.sort(key=lambda x: x['probability'], reverse=True)
        
        logger.info(f"✅ {len(filtered_recommendations)} recomendaciones generadas con datos reales")
        
        return {
            "success": True,
            "message": f"Recomendaciones generadas usando datos reales del CSV",
            "total_evaluated": len(client_data),
            "total_recommendations": len(filtered_recommendations),
            "filter_comercial": comercial,
            "min_probability_used": min_probability,
            "recommendations": filtered_recommendations,
            "data_source": "CSV real + Modelo ML"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en recomendaciones ML: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "recommendations": []
        }

        # AGREGAR ESTE ENDPOINT AL ARCHIVO main.py del backend

@app.get("/analytics/comerciales")
async def get_comerciales_from_csv(db: Session = Depends(get_database)):
    """
    Obtiene la lista única de comerciales del CSV cargado
    """
    try:
        logger.info("🔍 Obteniendo comerciales del CSV...")
        
        # Verificar que hay datos
        total_records = db.execute(text("SELECT COUNT(*) FROM client_data")).scalar()
        if total_records == 0:
            return {
                "success": False,
                "message": "No hay datos cargados en el sistema",
                "comerciales": []
            }
        
        # Query para obtener comerciales únicos
        comerciales_query = text("""
            SELECT DISTINCT comercial
            FROM client_data 
            WHERE comercial IS NOT NULL 
            AND TRIM(comercial) != ''
            AND comercial != 'N/A'
            AND comercial != 'Sin asignar'
            ORDER BY comercial
        """)
        
        result = db.execute(comerciales_query).fetchall()
        
        # Procesar lista de comerciales
        comerciales = [row.comercial for row in result if row.comercial]
        
        logger.info(f"✅ Encontrados {len(comerciales)} comerciales únicos")
        logger.info(f"📋 Comerciales: {comerciales[:5]}{'...' if len(comerciales) > 5 else ''}")
        
        return {
            "success": True,
            "comerciales": comerciales,
            "total_comerciales": len(comerciales),
            "total_records": total_records,
            "message": f"Se encontraron {len(comerciales)} comerciales únicos"
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo comerciales: {str(e)}")
        return {
            "success": False,
            "error": f"Error procesando comerciales: {str(e)}",
            "comerciales": []
        }


        # AGREGAR ESTE ENDPOINT AL ARCHIVO main.py del backend
# (después de los otros endpoints existentes)

@app.get("/analytics/comerciales")
async def get_comerciales_from_csv(db: Session = Depends(get_database)):
    """
    Obtiene la lista única de comerciales del CSV cargado
    """
    try:
        logger.info("🔍 Obteniendo comerciales del CSV...")
        
        # Verificar que hay datos
        total_records = db.execute(text("SELECT COUNT(*) FROM client_data")).scalar()
        if total_records == 0:
            return {
                "success": False,
                "message": "No hay datos cargados en el sistema",
                "comerciales": []
            }
        
        # Query para obtener comerciales únicos
        comerciales_query = text("""
            SELECT DISTINCT comercial
            FROM client_data 
            WHERE comercial IS NOT NULL 
            AND TRIM(comercial) != ''
            AND comercial != 'N/A'
            AND comercial != 'Sin asignar'
            AND comercial != 'null'
            AND comercial != 'NULL'
            ORDER BY comercial
        """)
        
        result = db.execute(comerciales_query).fetchall()
        
        # Procesar lista de comerciales
        comerciales = [row.comercial for row in result if row.comercial]
        
        logger.info(f"✅ Encontrados {len(comerciales)} comerciales únicos")
        logger.info(f"📋 Comerciales: {comerciales[:5]}{'...' if len(comerciales) > 5 else ''}")
        
        return {
            "success": True,
            "comerciales": comerciales,
            "total_comerciales": len(comerciales),
            "total_records": total_records,
            "message": f"Se encontraron {len(comerciales)} comerciales únicos"
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo comerciales: {str(e)}")
        return {
            "success": False,
            "error": f"Error procesando comerciales: {str(e)}",
            "comerciales": []
        }


@app.get("/clients/analytics/sales-by-type-detailed")
async def get_sales_by_type_detailed(db: Session = Depends(get_database)):
    return await get_sales_by_type_detailed_robust(db)

@app.get("/clients/analytics/acquisition-trend")
async def get_acquisition_trend(db: Session = Depends(get_database)):
    return await get_acquisition_trend_fixed_final(db)

@app.get("/clients/analytics/client-type-analysis")
async def get_client_type_analysis(db: Session = Depends(get_database)):
    return await get_client_type_analysis_postgresql(db)

@app.get("/debug/test-acquisition")
async def debug_test_acquisition_endpoint(db: Session = Depends(get_database)):
    return await debug_test_acquisition(db)

# Para desarrollo local
# if __name__ == "__main__":
#     import uvicorn
#     import os
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run(app, host="0.0.0.0", port=port)