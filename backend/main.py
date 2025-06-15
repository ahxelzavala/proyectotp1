from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd
import io
from typing import List, Dict, Any
from datetime import datetime
import logging
import traceback

# Importar modelos y configuración
from models import get_database, ClientData, AuthorizedEmail, create_tables, test_database_connection
from config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Sistema de Análisis Anders",
    description="API para importar y analizar datos CSV",
    version="1.0.0"
)

# Configurar CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar base de datos al arrancar la aplicación
@app.on_event("startup")
async def startup_event():
    """Inicializar la base de datos al arrancar"""
    logger.info("Iniciando aplicación...")
    
    # Probar conexión
    if not test_database_connection():
        logger.error("❌ No se pudo conectar a la base de datos")
        raise Exception("Error de conexión a la base de datos")
    
    # Crear tablas
    if not create_tables():
        logger.error("❌ No se pudieron crear las tablas")
        raise Exception("Error creando tablas de la base de datos")
    
    logger.info("✅ Base de datos inicializada correctamente")

@app.get("/")
async def root():
    """Endpoint de bienvenida"""
    return {"message": "Bienvenido al Sistema de Análisis Anders"}

@app.get("/health")
async def health_check():
    """Verificar el estado del servidor"""
    try:
        # Probar conexión a la base de datos
        db = next(get_database())
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "error", "database": "disconnected", "error": str(e)}

@app.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    replace_data: bool = True,  # ✅ Nuevo parámetro para controlar si reemplazar datos
    db: Session = Depends(get_database)
):
    """
    Endpoint para cargar archivo CSV y guardarlo en la base de datos
    """
    try:
        logger.info(f"Procesando archivo: {file.filename}")
        
        # Verificar que el archivo sea CSV
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400, 
                detail="El archivo debe ser un CSV (.csv)"
            )
        
        # ✅ Si replace_data es True, limpiar datos existentes
        if replace_data:
            try:
                deleted_count = db.query(ClientData).delete()
                db.commit()
                logger.info(f"🗑️ Datos anteriores eliminados: {deleted_count} registros")
            except Exception as e:
                db.rollback()
                logger.error(f"Error eliminando datos anteriores: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error limpiando datos anteriores: {str(e)}")
        
        # Leer el contenido del archivo
        contents = await file.read()
        
        # Crear un objeto StringIO para pandas
        csv_string = contents.decode('utf-8')
        csv_io = io.StringIO(csv_string)
        
        # ✅ Leer el CSV con pandas con configuración mejorada
        try:
            df = pd.read_csv(
                csv_io,
                encoding='utf-8',
                skipinitialspace=True,  # Eliminar espacios al inicio
                na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', 'NONE'],  # Valores considerados como NaN
                keep_default_na=True
            )
            logger.info(f"CSV leído exitosamente. Filas: {len(df)}, Columnas: {len(df.columns)}")
            logger.info(f"Primeras 3 filas del CSV:\n{df.head(3)}")
        except Exception as e:
            logger.error(f"Error leyendo CSV: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Error al leer el archivo CSV: {str(e)}"
            )
        
        # Validar que el DataFrame no esté vacío
        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="El archivo CSV está vacío"
            )
        
        # ✅ Limpiar nombres de columnas más agresivamente
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        logger.info(f"Columnas procesadas: {list(df.columns)}")
        
        # ✅ Mapear columnas esperadas (versión mejorada)
        column_mapping = {
            'client_name': ['client_name', 'nombre_cliente', 'cliente', 'name', 'nombre', 'client', 'customer', 'customer_name'],
            'client_type': ['client_type', 'tipo_cliente', 'tipo', 'type', 'category', 'categoria'],
            'executive': ['executive', 'ejecutivo', 'responsable', 'manager', 'gerente', 'vendedor', 'seller'],
            'product': ['product', 'producto', 'service', 'servicio', 'item'],
            'value': ['value', 'valor', 'amount', 'monto', 'price', 'precio', 'cost', 'costo'],
            'date': ['date', 'fecha', 'timestamp', 'created_at', 'fecha_creacion'],
            'description': ['description', 'descripcion', 'desc', 'notes', 'notas', 'comments', 'comentarios']
        }
        
        # ✅ Función mejorada para encontrar la columna correcta
        def find_column(possible_names, df_columns):
            df_columns_lower = [col.lower().strip() for col in df_columns]
            for name in possible_names:
                name_lower = name.lower().strip()
                # Buscar coincidencia exacta primero
                if name_lower in df_columns_lower:
                    idx = df_columns_lower.index(name_lower)
                    return df_columns[idx]
                # Buscar coincidencia parcial
                for i, col in enumerate(df_columns_lower):
                    if name_lower in col or col in name_lower:
                        return df_columns[i]
            return None
        
        # ✅ Identificar columnas disponibles
        client_name_col = find_column(column_mapping['client_name'], df.columns)
        client_type_col = find_column(column_mapping['client_type'], df.columns)
        executive_col = find_column(column_mapping['executive'], df.columns)
        product_col = find_column(column_mapping['product'], df.columns)
        value_col = find_column(column_mapping['value'], df.columns)
        date_col = find_column(column_mapping['date'], df.columns)
        description_col = find_column(column_mapping['description'], df.columns)
        
        logger.info(f"Mapeo de columnas encontradas:")
        logger.info(f"  - client_name: {client_name_col}")
        logger.info(f"  - client_type: {client_type_col}")
        logger.info(f"  - executive: {executive_col}")
        logger.info(f"  - product: {product_col}")
        logger.info(f"  - value: {value_col}")
        logger.info(f"  - date: {date_col}")
        logger.info(f"  - description: {description_col}")
        
        # ✅ Validar que al menos tengamos client_name
        if not client_name_col:
            available_columns = ", ".join(df.columns)
            raise HTTPException(
                status_code=400,
                detail=f"No se encontró una columna válida para 'client_name'. Columnas disponibles: {available_columns}"
            )
        
        # Crear lista de objetos ClientData para inserción en lote
        processed_records = []
        errors = []
        
        logger.info(f"Procesando {len(df)} filas...")
        
        for index, row in df.iterrows():
            try:
                # ✅ Extraer client_name de manera más robusta
                client_name_raw = row[client_name_col]
                if pd.isna(client_name_raw) or str(client_name_raw).strip() == '' or str(client_name_raw).lower() in ['nan', 'none', 'null']:
                    errors.append(f"Fila {index + 1}: Nombre de cliente vacío o inválido")
                    continue
                
                client_name = str(client_name_raw).strip()
                
                # ✅ Extraer otros campos con manejo mejorado de nulos
                client_type = "No especificado"
                if client_type_col and not pd.isna(row[client_type_col]):
                    client_type = str(row[client_type_col]).strip()
                
                executive = "No asignado"
                if executive_col and not pd.isna(row[executive_col]):
                    executive = str(row[executive_col]).strip()
                
                product = "No especificado"
                if product_col and not pd.isna(row[product_col]):
                    product = str(row[product_col]).strip()
                
                # ✅ Procesar valor numérico de manera más robusta
                value = 0.0
                if value_col and not pd.isna(row[value_col]):
                    try:
                        value_str = str(row[value_col]).replace(',', '').replace('$', '').replace('€', '').replace('£', '').strip()
                        # Remover cualquier carácter no numérico excepto punto y signo negativo
                        import re
                        value_str = re.sub(r'[^\d.-]', '', value_str)
                        if value_str:
                            value = float(value_str)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Fila {index + 1}: No se pudo convertir valor '{row[value_col]}' a número: {e}")
                        value = 0.0
                
                # ✅ Procesar fecha de manera más robusta
                date = datetime.utcnow()
                if date_col and not pd.isna(row[date_col]):
                    try:
                        parsed_date = pd.to_datetime(row[date_col], errors='coerce')
                        if not pd.isna(parsed_date):
                            date = parsed_date.to_pydatetime()
                    except Exception as e:
                        logger.warning(f"Fila {index + 1}: No se pudo parsear fecha '{row[date_col]}': {e}")
                
                description = None
                if description_col and not pd.isna(row[description_col]):
                    description = str(row[description_col]).strip()
                    if description == '' or description.lower() in ['nan', 'none', 'null']:
                        description = None
                
                # ✅ Crear objeto ClientData
                client_data = ClientData(
                    client_name=client_name,
                    client_type=client_type,
                    executive=executive,
                    product=product,
                    value=value,
                    date=date,
                    description=description
                )
                processed_records.append(client_data)
                
                # Log de progreso cada 1000 registros
                if (index + 1) % 1000 == 0:
                    logger.info(f"Procesadas {index + 1} filas...")
                
            except Exception as e:
                logger.error(f"Error procesando fila {index + 1}: {str(e)}")
                errors.append(f"Fila {index + 1}: Error procesando datos - {str(e)}")
                continue
        
        # Si no hay registros procesados exitosamente
        if not processed_records:
            error_message = f"No se pudieron procesar registros. Errores: {'; '.join(errors[:5])}"
            logger.error(error_message)
            raise HTTPException(
                status_code=400,
                detail=error_message
            )
        
        logger.info(f"Registros procesados exitosamente: {len(processed_records)}")
        
        # ✅ INSERCIÓN EN LOTE optimizada
        saved_count = 0
        try:
            # Insertar en lotes más pequeños para mejor rendimiento
            batch_size = 1000
            total_batches = (len(processed_records) + batch_size - 1) // batch_size
            
            for i in range(0, len(processed_records), batch_size):
                batch = processed_records[i:i + batch_size]
                db.add_all(batch)
                db.commit()
                saved_count += len(batch)
                logger.info(f"Lote {(i // batch_size) + 1}/{total_batches} guardado: {len(batch)} registros")
            
            logger.info(f"✅ {saved_count} registros guardados exitosamente en la base de datos")
            
        except Exception as e:
            db.rollback()
            error_msg = f"Error guardando en base de datos: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        
        # ✅ Preparar respuesta con más detalles
        response_data = {
            "success": True,
            "message": f"Archivo procesado exitosamente. {saved_count} registros guardados.",
            "details": {
                "filename": file.filename,
                "total_rows": len(df),
                "processed_rows": len(processed_records),
                "saved_rows": saved_count,
                "errors_count": len(errors),
                "columns_found": {
                    "client_name": client_name_col,
                    "client_type": client_type_col,
                    "executive": executive_col,
                    "product": product_col,
                    "value": value_col,
                    "date": date_col,
                    "description": description_col
                },
                "data_replaced": replace_data
            }
        }
        
        # Agregar errores si los hay (solo los primeros 10)
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
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.get("/client-data")
async def get_client_data(
    limit: int = 1000,  # ✅ Añadir límite por defecto
    offset: int = 0,    # ✅ Añadir offset para paginación
    db: Session = Depends(get_database)
):
    """Obtener datos de clientes con paginación"""
    try:
        # Contar total de registros
        total_count = db.query(ClientData).count()
        
        # Obtener registros con límite y offset
        clients = db.query(ClientData).offset(offset).limit(limit).all()
        
        logger.info(f"Consultando datos: {len(clients)} registros (de {total_count} totales)")
        
        return {
            "success": True,
            "total_count": total_count,
            "count": len(clients),
            "offset": offset,
            "limit": limit,
            "data": [
                {
                    "id": client.id,
                    "client_name": client.client_name,
                    "client_type": client.client_type,
                    "executive": client.executive,
                    "product": client.product,
                    "value": client.value,
                    "date": client.date.isoformat() if client.date else None,
                    "description": client.description
                }
                for client in clients
            ]
        }
    except Exception as e:
        logger.error(f"Error consultando datos: {str(e)}")
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
        
        # También obtener una muestra de los primeros 5 registros
        sample = db.query(ClientData).limit(5).all()
        sample_data = [
            {
                "id": client.id,
                "client_name": client.client_name,
                "client_type": client.client_type,
                "executive": client.executive,
                "product": client.product,
                "value": client.value
            } for client in sample
        ]
        
        return {
            "count": count, 
            "message": f"Hay {count} registros en la base de datos",
            "sample_data": sample_data
        }
    except Exception as e:
        logger.error(f"Error en debug count: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Nuevo endpoint para obtener información sobre las columnas del CSV
@app.get("/debug/columns")
async def debug_columns():
    """Endpoint para mostrar qué columnas esperamos"""
    return {
        "expected_columns": {
            "client_name": ["client_name", "nombre_cliente", "cliente", "name", "nombre", "client", "customer", "customer_name"],
            "client_type": ["client_type", "tipo_cliente", "tipo", "type", "category", "categoria"],
            "executive": ["executive", "ejecutivo", "responsable", "manager", "gerente", "vendedor", "seller"],
            "product": ["product", "producto", "service", "servicio", "item"],
            "value": ["value", "valor", "amount", "monto", "price", "precio", "cost", "costo"],
            "date": ["date", "fecha", "timestamp", "created_at", "fecha_creacion"],
            "description": ["description", "descripcion", "desc", "notes", "notas", "comments", "comentarios"]
        }
    }

# ✅ Endpoint para previsualizar CSV sin guardarlo
@app.post("/preview-csv")
async def preview_csv(file: UploadFile = File(...)):
    """
    Endpoint para previsualizar un CSV sin guardarlo en la base de datos
    """
    try:
        # Verificar que el archivo sea CSV
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400, 
                detail="El archivo debe ser un CSV (.csv)"
            )
        
        # Leer el contenido del archivo
        contents = await file.read()
        csv_string = contents.decode('utf-8')
        csv_io = io.StringIO(csv_string)
        
        # Leer solo las primeras 10 filas para previsualizar
        df = pd.read_csv(
            csv_io,
            encoding='utf-8',
            skipinitialspace=True,
            na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', 'NONE'],
            keep_default_na=True,
            nrows=10  # Solo las primeras 10 filas
        )
        
        # Limpiar nombres de columnas
        original_columns = list(df.columns)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        processed_columns = list(df.columns)
        
        # Mapear columnas
        column_mapping = {
            'client_name': ['client_name', 'nombre_cliente', 'cliente', 'name', 'nombre', 'client', 'customer', 'customer_name'],
            'client_type': ['client_type', 'tipo_cliente', 'tipo', 'type', 'category', 'categoria'],
            'executive': ['executive', 'ejecutivo', 'responsable', 'manager', 'gerente', 'vendedor', 'seller'],
            'product': ['product', 'producto', 'service', 'servicio', 'item'],
            'value': ['value', 'valor', 'amount', 'monto', 'price', 'precio', 'cost', 'costo'],
            'date': ['date', 'fecha', 'timestamp', 'created_at', 'fecha_creacion'],
            'description': ['description', 'descripcion', 'desc', 'notes', 'notas', 'comments', 'comentarios']
        }
        
        def find_column(possible_names, df_columns):
            df_columns_lower = [col.lower().strip() for col in df_columns]
            for name in possible_names:
                name_lower = name.lower().strip()
                if name_lower in df_columns_lower:
                    idx = df_columns_lower.index(name_lower)
                    return df_columns[idx]
                for i, col in enumerate(df_columns_lower):
                    if name_lower in col or col in name_lower:
                        return df_columns[i]
            return None
        
        # Identificar mapeo de columnas
        mapped_columns = {}
        for field, options in column_mapping.items():
            found_col = find_column(options, processed_columns)
            if found_col:
                mapped_columns[field] = found_col
        
        # Convertir las primeras filas a formato JSON serializable
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
            "original_columns": original_columns,
            "processed_columns": processed_columns,
            "mapped_columns": mapped_columns,
            "sample_data": sample_data,
            "total_rows": len(df),
            "message": f"Previsualización del CSV - Primeras {len(df)} filas mostradas"
        }
        
    except Exception as e:
        logger.error(f"Error en preview CSV: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando archivo: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)