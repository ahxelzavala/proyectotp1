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