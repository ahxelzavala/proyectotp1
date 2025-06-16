# ===== AGREGAR ESTOS IMPORTS AL INICIO DE main.py =====
from ml_service import ml_service
from pydantic import BaseModel
from typing import Optional

# ===== MODELOS PYDANTIC PARA ML =====
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

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import pandas as pd
import io
from typing import List, Dict, Any
from datetime import datetime
import logging
import traceback

# Importar modelos y configuración
from models import get_database, ClientData, AuthorizedEmail, create_tables, test_database_connection, migrate_add_new_columns
from config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sistema de Análisis Anders",
    description="API para importar y analizar datos CSV completos",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/analytics/summary")
async def get_summary_analytics(db: Session = Depends(get_database)):
    """Obtener analytics resumido"""
    try:
        # Estadísticas básicas
        total_records = db.query(ClientData).count()
        total_venta = db.query(func.sum(ClientData.venta)).scalar() or 0
        
        # Top clientes
        top_clientes = db.query(
            ClientData.cliente,
            func.sum(ClientData.venta).label('total_venta'),
            func.count(ClientData.id).label('total_facturas')
        ).filter(
            ClientData.cliente.isnot(None)
        ).group_by(
            ClientData.cliente
        ).order_by(
            func.sum(ClientData.venta).desc()
        ).limit(10).all()
        
        # Top comerciales
        top_comerciales = db.query(
            ClientData.comercial,
            func.sum(ClientData.venta).label('total_venta'),
            func.count(ClientData.id).label('total_facturas')
        ).filter(
            ClientData.comercial.isnot(None)
        ).group_by(
            ClientData.comercial
        ).order_by(
            func.sum(ClientData.venta).desc()
        ).limit(5).all()
        
        # Top categorías
        top_categorias = db.query(
            ClientData.categoria,
            func.sum(ClientData.venta).label('total_venta'),
            func.count(ClientData.id).label('total_facturas')
        ).filter(
            ClientData.categoria.isnot(None)
        ).group_by(
            ClientData.categoria
        ).order_by(
            func.sum(ClientData.venta).desc()
        ).limit(10).all()
        
        return {
            "success": True,
            "summary": {
                "total_records": total_records,
                "total_venta": float(total_venta),
                "average_venta": float(total_venta / total_records) if total_records > 0 else 0
            },
            "top_clientes": [
                {
                    "cliente": row.cliente,
                    "total_venta": float(row.total_venta or 0),
                    "total_facturas": row.total_facturas
                }
                for row in top_clientes
            ],
            "top_comerciales": [
                {
                    "comercial": row.comercial,
                    "total_venta": float(row.total_venta or 0),
                    "total_facturas": row.total_facturas
                }
                for row in top_comerciales
            ],
            "top_categorias": [
                {
                    "categoria": row.categoria,
                    "total_venta": float(row.total_venta or 0),
                    "total_facturas": row.total_facturas
                }
                for row in top_categorias
            ]
        }
        
    except Exception as e:
        logger.error(f"Error en analytics: {str(e)}")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ===== AGREGAR ESTOS ENDPOINTS AL FINAL DE main.py =====

@app.get("/clients/analytics/segmentation-stacked")
async def get_client_segmentation_stacked(db: Session = Depends(get_database)):
    """
    Gráfico de barras apiladas: Segmentación de clientes por tipo y supercategoría
    Variables: Tipo de Cliente, CATEGORIA, Cantidad
    """
    try:
        # Consulta para obtener segmentación por tipo de cliente y categoría
        query = text("""
            SELECT 
                COALESCE(categoria, 'Sin categoría') as categoria,
                COALESCE(tipo_de_cliente, 'Sin tipo') as tipo_cliente,
                COUNT(DISTINCT cliente) as cantidad_clientes,
                SUM(COALESCE(venta, 0)) as total_ventas
            FROM client_data 
            WHERE cliente IS NOT NULL AND cliente != ''
            GROUP BY categoria, tipo_de_cliente
            ORDER BY total_ventas DESC
            LIMIT 50
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

# ===== REEMPLAZAR COMPLETAMENTE LOS ENDPOINTS EXISTENTES EN main.py CON ESTAS VERSIONES =====
# Eliminar los endpoints antiguos que usan julianday() y strftime() y reemplazarlos con estos:

@app.get("/clients/analytics/segmentation-stacked")
async def get_client_segmentation_stacked(db: Session = Depends(get_database)):
    """
    Gráfico de barras apiladas: Segmentación de clientes por tipo y supercategoría
    Variables: Tipo de Cliente, CATEGORIA, Cantidad
    """
    try:
        # Consulta para obtener segmentación por tipo de cliente y categoría
        query = text("""
            SELECT 
                COALESCE(categoria, 'Sin categoría') as categoria,
                COALESCE(tipo_de_cliente, 'Sin tipo') as tipo_cliente,
                COUNT(DISTINCT cliente) as cantidad_clientes,
                SUM(COALESCE(venta, 0)) as total_ventas
            FROM client_data 
            WHERE cliente IS NOT NULL AND cliente != ''
            GROUP BY categoria, tipo_de_cliente
            ORDER BY total_ventas DESC
            LIMIT 50
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
                COUNT(DISTINCT DATE(fecha::date)) as dias_unicos_compra,
                SUM(COALESCE(cantidad, 0)) as cantidad_total,
                SUM(COALESCE(venta, 0)) as total_ventas,
                MIN(fecha::date) as primera_compra,
                MAX(fecha::date) as ultima_compra,
                CASE 
                    WHEN COUNT(DISTINCT DATE(fecha::date)) > 1 THEN
                        CAST(COUNT(DISTINCT factura) AS FLOAT) / 
                        GREATEST(1, EXTRACT(days FROM (MAX(fecha::date) - MIN(fecha::date))) / 30.0)
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

@app.get("/clients/analytics/acquisition-trend")
async def get_client_acquisition_trend(db: Session = Depends(get_database)):
    """
    Gráfico de líneas: Tendencia de adquisición de nuevos clientes
    Variables: Fecha, Cliente, Tipo de Cliente
    """
    try:
        # Consulta para obtener la primera compra de cada cliente (PostgreSQL)
        query = text("""
            WITH first_purchases AS (
                SELECT 
                    cliente,
                    COALESCE(tipo_de_cliente, 'Sin tipo') as tipo_cliente,
                    MIN(fecha::date) as primera_compra
                FROM client_data 
                WHERE cliente IS NOT NULL AND cliente != '' 
                    AND fecha IS NOT NULL
                GROUP BY cliente, tipo_de_cliente
            ),
            monthly_acquisition AS (
                SELECT 
                    TO_CHAR(primera_compra, 'YYYY-MM') as mes,
                    tipo_cliente,
                    COUNT(*) as nuevos_clientes
                FROM first_purchases
                WHERE primera_compra IS NOT NULL
                GROUP BY TO_CHAR(primera_compra, 'YYYY-MM'), tipo_cliente
                ORDER BY mes DESC
                LIMIT 100
            )
            SELECT 
                mes,
                tipo_cliente,
                nuevos_clientes
            FROM monthly_acquisition
            ORDER BY mes ASC
        """)
        
        result = db.execute(query).fetchall()
        
        data = []
        for row in result:
            data.append({
                "mes": row.mes,
                "tipo_cliente": row.tipo_cliente,
                "nuevos_clientes": row.nuevos_clientes
            })
        
        return {
            "success": True,
            "data": data,
            "chart_type": "line",
            "description": "Tendencia de adquisición de nuevos clientes por mes"
        }
        
    except Exception as e:
        logger.error(f"Error en tendencia de adquisición: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clients/analytics/most-profitable")
async def get_most_profitable_clients(
    limit: int = 20,
    db: Session = Depends(get_database)
):
    """
    Gráfico de barras: Clientes más rentables
    Variables: Cliente, Venta, Costo
    """
    try:
        # Consulta para obtener clientes más rentables (PostgreSQL)
        query = text("""
            SELECT 
                cliente,
                COALESCE(tipo_de_cliente, 'Sin tipo') as tipo_cliente,
                COUNT(DISTINCT factura) as numero_facturas,
                SUM(COALESCE(venta, 0)) as total_ventas,
                SUM(COALESCE(costo, 0)) as total_costo,
                SUM(COALESCE(mb, 0)) as margen_bruto,
                CASE 
                    WHEN SUM(COALESCE(venta, 0)) > 0 THEN
                        ROUND((SUM(COALESCE(mb, 0)) / SUM(COALESCE(venta, 0))) * 100, 2)
                    ELSE 0
                END as rentabilidad_porcentaje,
                AVG(COALESCE(venta, 0)) as venta_promedio
            FROM client_data 
            WHERE cliente IS NOT NULL AND cliente != ''
            GROUP BY cliente, tipo_de_cliente
            HAVING SUM(COALESCE(venta, 0)) > 0
            ORDER BY margen_bruto DESC, total_ventas DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {"limit": limit}).fetchall()
        
        data = []
        for row in result:
            data.append({
                "cliente": row.cliente,
                "tipo_cliente": row.tipo_cliente,
                "numero_facturas": row.numero_facturas,
                "total_ventas": float(row.total_ventas),
                "total_costo": float(row.total_costo),
                "margen_bruto": float(row.margen_bruto),
                "rentabilidad_porcentaje": float(row.rentabilidad_porcentaje),
                "venta_promedio": float(row.venta_promedio)
            })
        
        return {
            "success": True,
            "data": data,
            "chart_type": "horizontal_bar",
            "description": f"Top {limit} clientes más rentables"
        }
        
    except Exception as e:
        logger.error(f"Error en clientes rentables: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clients/analytics/dashboard-summary")
async def get_client_dashboard_summary(db: Session = Depends(get_database)):
    """
    Resumen ejecutivo para el dashboard de clientes
    """
    try:
        # Estadísticas generales (PostgreSQL)
        general_stats_query = text("""
            SELECT 
                COUNT(DISTINCT cliente) as total_clients,
                COUNT(DISTINCT factura) as total_invoices,
                SUM(COALESCE(venta, 0)) as total_sales,
                SUM(COALESCE(mb, 0)) as total_mb,
                AVG(
                    CASE 
                        WHEN COUNT(DISTINCT factura) > 1 THEN
                            CAST(COUNT(DISTINCT factura) AS FLOAT) / 
                            GREATEST(1, EXTRACT(days FROM (MAX(fecha::date) - MIN(fecha::date))) / 30.0)
                        ELSE 0
                    END
                ) as avg_frequency
            FROM (
                SELECT 
                    cliente,
                    factura,
                    fecha,
                    venta,
                    mb,
                    COUNT(DISTINCT factura) OVER (PARTITION BY cliente) as client_invoices,
                    MIN(fecha::date) OVER (PARTITION BY cliente) as first_date,
                    MAX(fecha::date) OVER (PARTITION BY cliente) as last_date
                FROM client_data 
                WHERE cliente IS NOT NULL AND cliente != ''
            ) subq
        """)
        
        general_stats = db.execute(general_stats_query).fetchone()
        
        # Top ejecutivos
        executives_query = text("""
            SELECT 
                COALESCE(comercial, 'Sin asignar') as ejecutivo,
                COUNT(DISTINCT cliente) as num_clientes,
                SUM(COALESCE(venta, 0)) as total_ventas,
                COUNT(DISTINCT factura) as num_facturas
            FROM client_data 
            WHERE comercial IS NOT NULL AND comercial != ''
            GROUP BY comercial
            ORDER BY total_ventas DESC
            LIMIT 8
        """)
        
        executives_result = db.execute(executives_query).fetchall()
        
        # Top categorías
        categories_query = text("""
            SELECT 
                COALESCE(categoria, 'Sin categoría') as categoria,
                COUNT(DISTINCT cliente) as num_clientes,
                SUM(COALESCE(venta, 0)) as total_ventas
            FROM client_data 
            WHERE categoria IS NOT NULL AND categoria != ''
            GROUP BY categoria
            ORDER BY total_ventas DESC
            LIMIT 5
        """)
        
        categories_result = db.execute(categories_query).fetchall()
        
        # Procesar resultados
        executives_data = []
        for row in executives_result:
            executives_data.append({
                "ejecutivo": row.ejecutivo,
                "num_clientes": row.num_clientes,
                "total_ventas": float(row.total_ventas),
                "num_facturas": row.num_facturas
            })
        
        categories_data = []
        for row in categories_result:
            categories_data.append({
                "categoria": row.categoria,
                "num_clientes": row.num_clientes,
                "total_ventas": float(row.total_ventas)
            })
        
        return {
            "success": True,
            "summary": {
                "total_clients": general_stats.total_clients if general_stats else 0,
                "total_invoices": general_stats.total_invoices if general_stats else 0,
                "total_sales": float(general_stats.total_sales) if general_stats and general_stats.total_sales else 0,
                "total_mb": float(general_stats.total_mb) if general_stats and general_stats.total_mb else 0,
                "avg_frequency": float(general_stats.avg_frequency) if general_stats and general_stats.avg_frequency else 0
            },
            "top_executives": executives_data,
            "top_categories": categories_data
        }
        
    except Exception as e:
        logger.error(f"Error en dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint simplificado sin usar tabla clients (ya que no existe)
@app.post("/clients/populate")
async def populate_clients_table(db: Session = Depends(get_database)):
    """
    Poblar la tabla clients desde client_data para PostgreSQL
    """
    try:
        # Verificar si ya existen datos en clients
        existing_count_query = text("SELECT COUNT(*) FROM clients")
        existing_count = db.execute(existing_count_query).scalar()
        
        if existing_count > 0:
            return {
                "success": True,
                "message": f"Tabla clients ya tiene {existing_count} registros",
                "existing_count": existing_count
            }
        
        # Insertar clientes únicos desde client_data (PostgreSQL syntax)
        insert_query = text("""
            INSERT INTO clients (
                client_name, client_type, executive, product, 
                value, date, description
            )
            SELECT DISTINCT
                COALESCE(cliente, 'Sin nombre') as client_name,
                COALESCE(tipo_de_cliente, 'Sin tipo') as client_type,
                COALESCE(comercial, 'Sin ejecutivo') as executive,
                COALESCE(articulo, 'Sin producto') as product,
                COALESCE(venta, 0) as value,
                COALESCE(
                    TO_TIMESTAMP(fecha, 'YYYY-MM-DD'), 
                    CURRENT_TIMESTAMP
                ) as date,
                'Migrado desde client_data - ' || COALESCE(factura, 'Sin factura') as description
            FROM client_data 
            WHERE cliente IS NOT NULL AND cliente != ''
            LIMIT 5000
        """)
        
        result = db.execute(insert_query)
        db.commit()
        
        new_count = result.rowcount
        
        return {
            "success": True,
            "message": f"Se agregaron {new_count} registros a la tabla clients",
            "inserted_count": new_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error poblando tabla clients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clients")
async def get_clients_count(db: Session = Depends(get_database)):
    """
    Verificar conteo de la tabla clients
    """
    try:
        count_query = text("SELECT COUNT(*) FROM clients")
        count = db.execute(count_query).scalar()
        
        return {
            "success": True,
            "total_count": count,
            "message": f"Tabla clients tiene {count} registros"
        }
    except Exception as e:
        logger.error(f"Error verificando tabla clients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/top-sold")
async def get_top_sold_products(db: Session = Depends(get_database)):
    """Obtenemos los productos más vendidos en los últimos 3, 6 y 12 meses"""
    try:
        # Consulta SQL para obtener ventas por producto (últimos 12 meses)
        query = text("""
            SELECT 
                producto,
                SUM(venta) AS total_ventas,
                COUNT(DISTINCT factura) AS total_facturas
            FROM client_data
            WHERE fecha >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY producto
            ORDER BY total_ventas DESC
            LIMIT 10
        """)
        result = db.execute(query).fetchall()
        products_data = [{"producto": row[0], "total_ventas": float(row[1])} for row in result]
        return {"success": True, "data": products_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos de productos: {str(e)}")

        

# ===== ENDPOINTS PARA MÓDULO DE PRODUCTOS =====
# Agregar estos endpoints al final de main.py

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

@app.get("/products/analytics/margin-scatter")
async def get_products_margin_scatter(
    min_sales: float = 1000,
    db: Session = Depends(get_database)
):
    """
    Gráfico de dispersión: Productos según cantidad vendida vs margen de beneficio
    Variables: Articulo, Cantidad, MB, Venta, Costo
    """
    try:
        # Consulta para obtener datos de dispersión de productos
        query = text("""
            SELECT 
                COALESCE(articulo, 'Producto sin nombre') as producto,
                COALESCE(categoria, 'Sin categoría') as categoria,
                COALESCE(proveedor, 'Sin proveedor') as proveedor,
                SUM(COALESCE(cantidad, 0)) as total_cantidad,
                SUM(COALESCE(venta, 0)) as total_ventas,
                SUM(COALESCE(costo, 0)) as total_costo,
                SUM(COALESCE(mb, 0)) as total_margen,
                COUNT(DISTINCT factura) as num_transacciones,
                CASE 
                    WHEN SUM(COALESCE(venta, 0)) > 0 THEN
                        ROUND((SUM(COALESCE(mb, 0)) / SUM(COALESCE(venta, 0))) * 100, 2)
                    ELSE 0
                END as margen_porcentaje,
                CASE
                    WHEN SUM(COALESCE(cantidad, 0)) > 0 THEN
                        SUM(COALESCE(venta, 0)) / SUM(COALESCE(cantidad, 0))
                    ELSE 0
                END as precio_promedio_unitario
            FROM client_data 
            WHERE articulo IS NOT NULL AND articulo != ''
                AND cantidad IS NOT NULL AND cantidad > 0
            GROUP BY articulo, categoria, proveedor
            HAVING SUM(COALESCE(venta, 0)) >= :min_sales
            ORDER BY total_margen DESC
            LIMIT 100
        """)
        
        result = db.execute(query, {"min_sales": min_sales}).fetchall()
        
        data = []
        for row in result:
            data.append({
                "producto": row.producto,
                "categoria": row.categoria,
                "proveedor": row.proveedor,
                "total_cantidad": float(row.total_cantidad),
                "total_ventas": float(row.total_ventas),
                "total_costo": float(row.total_costo),
                "total_margen": float(row.total_margen),
                "margen_porcentaje": float(row.margen_porcentaje),
                "num_transacciones": row.num_transacciones,
                "precio_promedio_unitario": float(row.precio_promedio_unitario)
            })
        
        return {
            "success": True,
            "data": data,
            "chart_type": "scatter",
            "description": f"Relación cantidad vendida vs margen de beneficio (ventas mínimas: ${min_sales:,.2f})"
        }
        
    except Exception as e:
        logger.error(f"Error en dispersión de margen: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/products/analytics/dashboard-summary")
async def get_products_dashboard_summary(db: Session = Depends(get_database)):
    """
    Resumen ejecutivo para el dashboard de productos
    """
    try:
        # Estadísticas generales de productos
        general_stats_query = text("""
            SELECT 
                COUNT(DISTINCT articulo) as total_productos,
                COUNT(DISTINCT categoria) as total_categorias,
                COUNT(DISTINCT proveedor) as total_proveedores,
                SUM(COALESCE(venta, 0)) as ventas_totales,
                SUM(COALESCE(cantidad, 0)) as cantidad_total,
                SUM(COALESCE(mb, 0)) as margen_total,
                COUNT(DISTINCT factura) as total_transacciones,
                CASE 
                    WHEN SUM(COALESCE(venta, 0)) > 0 THEN
                        ROUND((SUM(COALESCE(mb, 0)) / SUM(COALESCE(venta, 0))) * 100, 2)
                    ELSE 0
                END as margen_promedio_porcentaje
            FROM client_data 
            WHERE articulo IS NOT NULL AND articulo != ''
        """)
        
        general_stats = db.execute(general_stats_query).fetchone()
        
        # Top categorías por ventas
        top_categories_query = text("""
            SELECT 
                COALESCE(categoria, 'Sin categoría') as categoria,
                COUNT(DISTINCT articulo) as num_productos,
                SUM(COALESCE(venta, 0)) as total_ventas,
                SUM(COALESCE(cantidad, 0)) as total_cantidad
            FROM client_data 
            WHERE categoria IS NOT NULL AND categoria != ''
            GROUP BY categoria
            ORDER BY total_ventas DESC
            LIMIT 8
        """)
        
        categories_result = db.execute(top_categories_query).fetchall()
        
        # Top proveedores
        top_suppliers_query = text("""
            SELECT 
                COALESCE(proveedor, 'Sin proveedor') as proveedor,
                COUNT(DISTINCT articulo) as num_productos,
                SUM(COALESCE(venta, 0)) as total_ventas,
                COUNT(DISTINCT cliente) as num_clientes
            FROM client_data 
            WHERE proveedor IS NOT NULL AND proveedor != ''
            GROUP BY proveedor
            ORDER BY total_ventas DESC
            LIMIT 6
        """)
        
        suppliers_result = db.execute(top_suppliers_query).fetchall()
        
        # Productos con mejor y peor margen
        margin_analysis_query = text("""
            WITH product_margins AS (
                SELECT 
                    COALESCE(articulo, 'Producto sin nombre') as producto,
                    SUM(COALESCE(venta, 0)) as total_ventas,
                    SUM(COALESCE(mb, 0)) as total_margen,
                    CASE 
                        WHEN SUM(COALESCE(venta, 0)) > 0 THEN
                            ROUND((SUM(COALESCE(mb, 0)) / SUM(COALESCE(venta, 0))) * 100, 2)
                        ELSE 0
                    END as margen_porcentaje
                FROM client_data 
                WHERE articulo IS NOT NULL AND articulo != ''
                GROUP BY articulo
                HAVING SUM(COALESCE(venta, 0)) > 1000  -- Solo productos con ventas significativas
            )
            SELECT 
                'mejor_margen' as tipo,
                producto,
                total_ventas,
                margen_porcentaje
            FROM product_margins
            ORDER BY margen_porcentaje DESC
            LIMIT 3
            
            UNION ALL
            
            SELECT 
                'peor_margen' as tipo,
                producto,
                total_ventas,
                margen_porcentaje
            FROM product_margins
            ORDER BY margen_porcentaje ASC
            LIMIT 3
        """)
        
        margin_result = db.execute(margin_analysis_query).fetchall()
        
        # Procesar resultados
        categories_data = []
        for row in categories_result:
            categories_data.append({
                "categoria": row.categoria,
                "num_productos": row.num_productos,
                "total_ventas": float(row.total_ventas),
                "total_cantidad": float(row.total_cantidad)
            })
        
        suppliers_data = []
        for row in suppliers_result:
            suppliers_data.append({
                "proveedor": row.proveedor,
                "num_productos": row.num_productos,
                "total_ventas": float(row.total_ventas),
                "num_clientes": row.num_clientes
            })
        
        mejor_margen = []
        peor_margen = []
        for row in margin_result:
            product_data = {
                "producto": row.producto,
                "total_ventas": float(row.total_ventas),
                "margen_porcentaje": float(row.margen_porcentaje)
            }
            if row.tipo == 'mejor_margen':
                mejor_margen.append(product_data)
            else:
                peor_margen.append(product_data)
        
        return {
            "success": True,
            "summary": {
                "total_productos": general_stats.total_productos if general_stats else 0,
                "total_categorias": general_stats.total_categorias if general_stats else 0,
                "total_proveedores": general_stats.total_proveedores if general_stats else 0,
                "ventas_totales": float(general_stats.ventas_totales) if general_stats and general_stats.ventas_totales else 0,
                "cantidad_total": float(general_stats.cantidad_total) if general_stats and general_stats.cantidad_total else 0,
                "margen_total": float(general_stats.margen_total) if general_stats and general_stats.margen_total else 0,
                "margen_promedio_porcentaje": float(general_stats.margen_promedio_porcentaje) if general_stats and general_stats.margen_promedio_porcentaje else 0,
                "total_transacciones": general_stats.total_transacciones if general_stats else 0
            },
            "top_categories": categories_data,
            "top_suppliers": suppliers_data,
            "mejor_margen": mejor_margen,
            "peor_margen": peor_margen
        }
        
    except Exception as e:
        logger.error(f"Error en dashboard summary de productos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/analytics/category-performance")
async def get_category_performance(db: Session = Depends(get_database)):
    """
    Análisis de rendimiento por categoría de productos
    Variables: Categoria, Supercategoria, Venta, Margen
    """
    try:
        query = text("""
            SELECT 
                COALESCE(categoria, 'Sin categoría') as categoria,
                COALESCE(supercategoria, 'Sin supercategoría') as supercategoria,
                COUNT(DISTINCT articulo) as num_productos,
                SUM(COALESCE(venta, 0)) as total_ventas,
                SUM(COALESCE(cantidad, 0)) as total_cantidad,
                SUM(COALESCE(mb, 0)) as total_margen,
                COUNT(DISTINCT cliente) as num_clientes,
                COUNT(DISTINCT factura) as num_transacciones,
                CASE 
                    WHEN SUM(COALESCE(venta, 0)) > 0 THEN
                        ROUND((SUM(COALESCE(mb, 0)) / SUM(COALESCE(venta, 0))) * 100, 2)
                    ELSE 0
                END as margen_porcentaje,
                ROUND(AVG(COALESCE(venta, 0)), 2) as venta_promedio
            FROM client_data 
            WHERE categoria IS NOT NULL AND categoria != ''
            GROUP BY categoria, supercategoria
            ORDER BY total_ventas DESC
            LIMIT 20
        """)
        
        result = db.execute(query).fetchall()
        
        data = []
        for row in result:
            data.append({
                "categoria": row.categoria,
                "supercategoria": row.supercategoria,
                "num_productos": row.num_productos,
                "total_ventas": float(row.total_ventas),
                "total_cantidad": float(row.total_cantidad),
                "total_margen": float(row.total_margen),
                "num_clientes": row.num_clientes,
                "num_transacciones": row.num_transacciones,
                "margen_porcentaje": float(row.margen_porcentaje),
                "venta_promedio": float(row.venta_promedio)
            })
        
        return {
            "success": True,
            "data": data,
            "chart_type": "category_performance",
            "description": "Rendimiento por categorías de productos"
        }
        
    except Exception as e:
        logger.error(f"Error en rendimiento por categoría: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINT CORREGIDO PARA REEMPLAZAR EL EXISTENTE =====

@app.get("/products/top-sold")
async def get_top_sold_products(
    period: str = "12m",  # 3m, 6m, 12m
    limit: int = 20,
    db: Session = Depends(get_database)
):
    """
    Productos más vendidos en diferentes períodos
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
        
        # Consulta corregida para PostgreSQL
        query = text("""
            SELECT 
                COALESCE(articulo, 'Producto sin nombre') as producto,
                COALESCE(categoria, 'Sin categoría') as categoria,
                SUM(COALESCE(venta, 0)) as total_ventas,
                SUM(COALESCE(cantidad, 0)) as total_cantidad,
                COUNT(DISTINCT factura) as total_facturas,
                COUNT(DISTINCT cliente) as num_clientes,
                ROUND(AVG(COALESCE(venta, 0)), 2) as venta_promedio
            FROM client_data
            WHERE articulo IS NOT NULL AND articulo != ''
                AND fecha::date >= CURRENT_DATE - INTERVAL ':months months'
            GROUP BY articulo, categoria
            ORDER BY total_ventas DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {"months": months, "limit": limit}).fetchall()
        
        products_data = []
        for row in result:
            products_data.append({
                "producto": row.producto,
                "categoria": row.categoria,
                "total_ventas": float(row.total_ventas),
                "total_cantidad": float(row.total_cantidad),
                "total_facturas": row.total_facturas,
                "num_clientes": row.num_clientes,
                "venta_promedio": float(row.venta_promedio)
            })
        
        return {
            "success": True, 
            "data": products_data,
            "period": f"Últimos {months} meses",
            "description": f"Top {limit} productos más vendidos"
        }
        
    except Exception as e:
        logger.error(f"Error al obtener productos más vendidos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener datos de productos: {str(e)}")


        # ===== AGREGAR SOLO ESTOS ENDPOINTS MÍNIMOS AL FINAL DE main.py =====

@app.get("/products/analytics/rotation-speed")
async def get_rotation_speed(period: str = "12m", limit: int = 10, db: Session = Depends(get_database)):
    """
    Análisis de velocidad de rotación de productos
    """
    try:
        # Filtro de período
        period_filter = ""
        if period == "3m":
            period_filter = "AND TO_DATE(fecha, 'YYYY-MM-DD') >= CURRENT_DATE - INTERVAL '3 months'"
        elif period == "6m":
            period_filter = "AND TO_DATE(fecha, 'YYYY-MM-DD') >= CURRENT_DATE - INTERVAL '6 months'"
        elif period == "12m":
            period_filter = "AND TO_DATE(fecha, 'YYYY-MM-DD') >= CURRENT_DATE - INTERVAL '12 months'"
        
        query = text(f"""
            WITH product_rotation AS (
                SELECT 
                    producto,
                    SUM(COALESCE(cantidad, 0)) as total_cantidad,
                    COUNT(DISTINCT factura) as num_transacciones,
                    SUM(COALESCE(venta, 0)) as total_ventas,
                    COUNT(DISTINCT TO_CHAR(TO_DATE(fecha, 'YYYY-MM-DD'), 'YYYY-MM')) as meses_activos
                FROM client_data 
                WHERE producto IS NOT NULL AND producto != ''
                    AND cantidad IS NOT NULL AND cantidad > 0
                    {period_filter}
                GROUP BY producto
                HAVING SUM(COALESCE(venta, 0)) > 1000
            )
            SELECT 
                producto,
                total_cantidad,
                num_transacciones,
                total_ventas,
                meses_activos,
                CASE 
                    WHEN meses_activos > 0 THEN 
                        ROUND((num_transacciones::float / GREATEST(meses_activos, 1)), 2)
                    ELSE 0
                END as velocidad_rotacion,
                CASE 
                    WHEN (num_transacciones::float / GREATEST(meses_activos, 1)) >= 6 THEN 'Rápida'
                    WHEN (num_transacciones::float / GREATEST(meses_activos, 1)) >= 3 THEN 'Media'
                    ELSE 'Lenta'
                END as categoria
            FROM product_rotation
            ORDER BY velocidad_rotacion DESC
            LIMIT {limit}
        """)
        
        result = db.execute(query).fetchall()
        
        data = []
        for row in result:
            data.append({
                "producto": row.producto,
                "total_cantidad": row.total_cantidad,
                "num_transacciones": row.num_transacciones,
                "total_ventas": float(row.total_ventas),
                "velocidad_rotacion": float(row.velocidad_rotacion),
                "categoria": row.categoria
            })
        
        return {
            "success": True,
            "data": data,
            "chart_type": "rotation_analysis",
            "description": f"Análisis de velocidad de rotación - Top {limit} productos"
        }
        
    except Exception as e:
        logger.error(f"Error en análisis de rotación: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== MODIFICAR ENDPOINTS EXISTENTES PARA SOPORTAR FILTROS DE PERÍODO =====

# Si ya tienes estos endpoints, solo agrega el parámetro period y el filtro correspondiente:

# 1. Modificar comparative-bars existente:
@app.get("/products/analytics/comparative-bars")
async def get_comparative_bars_analysis(period: str = "12m", limit: int = 15, db: Session = Depends(get_database)):
    """
    Análisis comparativo de productos con filtro de período
    """
    try:
        # Agregar filtro de período
        period_filter = ""
        if period == "3m":
            period_filter = "AND TO_DATE(fecha, 'YYYY-MM-DD') >= CURRENT_DATE - INTERVAL '3 months'"
        elif period == "6m":
            period_filter = "AND TO_DATE(fecha, 'YYYY-MM-DD') >= CURRENT_DATE - INTERVAL '6 months'"
        elif period == "12m":
            period_filter = "AND TO_DATE(fecha, 'YYYY-MM-DD') >= CURRENT_DATE - INTERVAL '12 months'"
        
        # Tu query existente + el filtro
        query = text(f"""
            SELECT 
                producto,
                SUM(COALESCE(venta, 0)) as total_ventas,
                SUM(COALESCE(margen_bruto, 0)) as total_margen,
                SUM(COALESCE(cantidad, 0)) as total_cantidad,
                COUNT(DISTINCT factura) as num_facturas,
                AVG(CASE WHEN venta > 0 THEN (margen_bruto / venta * 100) ELSE 0 END) as margen_porcentaje
            FROM client_data
            WHERE producto IS NOT NULL AND producto != ''
                AND venta IS NOT NULL AND venta > 0
                {period_filter}
            GROUP BY producto
            ORDER BY total_ventas DESC
            LIMIT {limit}
        """)
        
        result = db.execute(query).fetchall()
        
        data = []
        for row in result:
            data.append({
                "producto": row.producto,
                "total_ventas": float(row.total_ventas),
                "total_margen": float(row.total_margen or 0),
                "total_cantidad": row.total_cantidad,
                "num_facturas": row.num_facturas,
                "margen_porcentaje": float(row.margen_porcentaje or 0)
            })
        
        return {
            "success": True,
            "data": data,
            "chart_type": "comparative_bars",
            "description": f"Análisis comparativo de productos - {period}",
            "period": period
        }
        
    except Exception as e:
        logger.error(f"Error en análisis comparativo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 2. Modificar trend-lines existente:
@app.get("/products/analytics/trend-lines")
async def get_trend_lines_analysis(top_products: int = 6, period: str = "12m", db: Session = Depends(get_database)):
    """
    Análisis de tendencias de productos con filtro de período
    """
    try:
        # Agregar filtro de período
        period_filter = ""
        if period == "3m":
            period_filter = "AND TO_DATE(fecha, 'YYYY-MM-DD') >= CURRENT_DATE - INTERVAL '3 months'"
        elif period == "6m":
            period_filter = "AND TO_DATE(fecha, 'YYYY-MM-DD') >= CURRENT_DATE - INTERVAL '6 months'"
        elif period == "12m":
            period_filter = "AND TO_DATE(fecha, 'YYYY-MM-DD') >= CURRENT_DATE - INTERVAL '12 months'"
        
        # Tu query existente + el filtro
        query = text(f"""
            WITH top_products_list AS (
                SELECT producto
                FROM client_data
                WHERE producto IS NOT NULL AND producto != ''
                    AND venta IS NOT NULL AND venta > 0
                    {period_filter}
                GROUP BY producto
                ORDER BY SUM(COALESCE(venta, 0)) DESC
                LIMIT {top_products}
            )
            SELECT 
                tp.producto,
                TO_CHAR(TO_DATE(cd.fecha, 'YYYY-MM-DD'), 'YYYY-MM') as mes,
                SUM(COALESCE(cd.venta, 0)) as ventas_mes
            FROM top_products_list tp
            JOIN client_data cd ON tp.producto = cd.producto
            WHERE cd.fecha IS NOT NULL
                AND cd.venta IS NOT NULL AND cd.venta > 0
                {period_filter}
            GROUP BY tp.producto, TO_CHAR(TO_DATE(cd.fecha, 'YYYY-MM-DD'), 'YYYY-MM')
            ORDER BY mes, tp.producto
        """)
        
        result = db.execute(query).fetchall()
        
        data = []
        for row in result:
            data.append({
                "producto": row.producto,
                "mes": row.mes,
                "ventas_mes": float(row.ventas_mes)
            })
        
        return {
            "success": True,
            "data": data,
            "chart_type": "trend_lines",
            "description": f"Tendencias de top {top_products} productos - {period}",
            "period": period
        }
        
    except Exception as e:
        logger.error(f"Error en análisis de tendencias: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 3. Modificar pareto-80-20 existente:
@app.get("/products/analytics/pareto-80-20")
async def get_pareto_analysis(period: str = "12m", db: Session = Depends(get_database)):
    """
    Análisis de Pareto 80/20 con filtro de período
    """
    try:
        # Agregar filtro de período
        period_filter = ""
        if period == "3m":
            period_filter = "AND TO_DATE(fecha, 'YYYY-MM-DD') >= CURRENT_DATE - INTERVAL '3 months'"
        elif period == "6m":
            period_filter = "AND TO_DATE(fecha, 'YYYY-MM-DD') >= CURRENT_DATE - INTERVAL '6 months'"
        elif period == "12m":
            period_filter = "AND TO_DATE(fecha, 'YYYY-MM-DD') >= CURRENT_DATE - INTERVAL '12 months'"
        
        # Tu query existente + el filtro
        query = text(f"""
            WITH product_sales AS (
                SELECT 
                    producto,
                    SUM(COALESCE(venta, 0)) as total_ventas
                FROM client_data
                WHERE producto IS NOT NULL AND producto != ''
                    AND venta IS NOT NULL AND venta > 0
                    {period_filter}
                GROUP BY producto
            ),
            total_sales AS (
                SELECT SUM(total_ventas) as grand_total
                FROM product_sales
            ),
            pareto_analysis AS (
                SELECT 
                    ps.producto,
                    ps.total_ventas,
                    (ps.total_ventas / ts.grand_total * 100) as participacion,
                    SUM(ps.total_ventas / ts.grand_total * 100) OVER (
                        ORDER BY ps.total_ventas DESC 
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) as participacion_acumulada
                FROM product_sales ps
                CROSS JOIN total_sales ts
                ORDER BY ps.total_ventas DESC
            )
            SELECT 
                producto,
                total_ventas,
                ROUND(participacion, 2) as participacion,
                ROUND(participacion_acumulada, 2) as participacion_acumulada
            FROM pareto_analysis
            ORDER BY total_ventas DESC
            LIMIT 20
        """)
        
        result = db.execute(query).fetchall()
        
        data = []
        for row in result:
            data.append({
                "producto": row.producto,
                "total_ventas": float(row.total_ventas),
                "participacion": float(row.participacion),
                "participacion_acumulada": float(row.participacion_acumulada)
            })
        
        return {
            "success": True,
            "data": data,
            "chart_type": "pareto_analysis",
            "description": f"Análisis de Pareto 80/20 - {period}",
            "period": period
        }
        
    except Exception as e:
        logger.error(f"Error en análisis de Pareto: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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

@app.get("/ml/cross-sell-recommendations")
async def get_cross_sell_recommendations(
    limit: int = 50,
    min_probability: float = 0.5,
    db: Session = Depends(get_database)
):
    """Obtener recomendaciones de venta cruzada filtradas"""
    try:
        # Verificar que el modelo esté cargado
        if not ml_service.is_loaded:
            return {
                "success": False,
                "message": "Modelo de ML no disponible",
                "recommendations": []
            }
        
        # Obtener clientes activos (con ventas recientes)
        query = text("""
            SELECT DISTINCT
                id, cliente, venta, costo, mb, cantidad,
                tipo_de_cliente, categoria, comercial, proveedor,
                fecha
            FROM client_data 
            WHERE cliente IS NOT NULL AND cliente != ''
                AND venta IS NOT NULL AND venta > 0
                AND fecha IS NOT NULL
            ORDER BY venta DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {"limit": limit * 2}).fetchall()
        
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
        
        # Realizar predicciones
        all_predictions = ml_service.predict_cross_sell(client_data)
        
        # Filtrar por probabilidad mínima y recomendaciones positivas
        filtered_recommendations = [
            pred for pred in all_predictions 
            if pred['prediction'] == 1 and pred['probability'] >= min_probability
        ]
        
        # Ordenar por probabilidad descendente
        filtered_recommendations.sort(key=lambda x: x['probability'], reverse=True)
        
        # Limitar resultados
        final_recommendations = filtered_recommendations[:limit]
        
        return {
            "success": True,
            "message": f"Se encontraron {len(final_recommendations)} recomendaciones de alta calidad",
            "total_evaluated": len(client_data),
            "total_positive": len([p for p in all_predictions if p['prediction'] == 1]),
            "high_quality_recommendations": len(final_recommendations),
            "min_probability_filter": min_probability,
            "recommendations": final_recommendations
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
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

@app.get("/ml/model-performance")
async def get_model_performance():
    """Obtener métricas de rendimiento del modelo"""
    try:
        if not ml_service.is_loaded:
            return {
                "success": False,
                "message": "Modelo no disponible",
                "performance": {}
            }
        
        model_info = ml_service.get_model_info()
        feature_importance = ml_service.get_feature_importance()
        
        return {
            "success": True,
            "performance": {
                "model_version": model_info.get('model_version', 'Unknown'),
                "training_date": model_info.get('training_date', 'Unknown'),
                "threshold": model_info.get('threshold', 0.4),
                "metrics": model_info.get('metrics', {}),
                "feature_importance": feature_importance[:10]  # Top 10 features
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo performance: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "performance": {}
        }