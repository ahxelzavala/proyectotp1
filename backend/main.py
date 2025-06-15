from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import pandas as pd
import io
from typing import List, Dict, Any
from datetime import datetime
import logging

# Importar modelos y configuración
from models import get_database, ClientData, AuthorizedEmail
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
        db.execute("SELECT 1")
        db.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "error": str(e)}

@app.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_database)
):
    """
    Endpoint para cargar archivo CSV y guardarlo en la base de datos
    """
    try:
        # Verificar que el archivo sea CSV
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400, 
                detail="El archivo debe ser un CSV (.csv)"
            )
        
        logger.info(f"Procesando archivo: {file.filename}")
        
        # Leer el contenido del archivo
        contents = await file.read()
        
        # Crear un objeto StringIO para pandas
        csv_string = contents.decode('utf-8')
        csv_io = io.StringIO(csv_string)
        
        # Leer el CSV con pandas
        try:
            df = pd.read_csv(csv_io)
            logger.info(f"CSV leído exitosamente. Filas: {len(df)}, Columnas: {list(df.columns)}")
        except Exception as e:
            logger.error(f"Error al leer CSV: {str(e)}")
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
        
        # Limpiar nombres de columnas (eliminar espacios)
        df.columns = df.columns.str.strip()
        logger.info(f"Columnas encontradas: {list(df.columns)}")
        
        # Mapear columnas esperadas (versión más flexible)
        column_mapping = {
            'client_name': ['client_name', 'nombre_cliente', 'cliente', 'name', 'nombre'],
            'client_type': ['client_type', 'tipo_cliente', 'tipo', 'type'],
            'executive': ['executive', 'ejecutivo', 'responsable', 'comercial'],
            'product': ['product', 'producto', 'servicio'],
            'value': ['value', 'valor', 'amount', 'monto', 'precio', 'importe'],
            'date': ['date', 'fecha', 'fecha_venta', 'created_at'],
            'description': ['description', 'descripcion', 'desc', 'observaciones', 'comentarios']
        }
        
        # Función para encontrar la columna correcta
        def find_column(possible_names, df_columns):
            df_columns_lower = [col.lower().strip() for col in df_columns]
            for name in possible_names:
                if name.lower() in df_columns_lower:
                    # Retornar el nombre original de la columna
                    idx = df_columns_lower.index(name.lower())
                    return df_columns[idx]
            return None
        
        # Buscar las columnas necesarias una vez
        client_name_col = find_column(column_mapping['client_name'], df.columns)
        client_type_col = find_column(column_mapping['client_type'], df.columns)
        executive_col = find_column(column_mapping['executive'], df.columns)
        product_col = find_column(column_mapping['product'], df.columns)
        value_col = find_column(column_mapping['value'], df.columns)
        date_col = find_column(column_mapping['date'], df.columns)
        description_col = find_column(column_mapping['description'], df.columns)
        
        logger.info(f"Mapeo de columnas: client_name={client_name_col}, client_type={client_type_col}, executive={executive_col}")
        
        # Validar que al menos tengamos la columna de nombre de cliente
        if not client_name_col:
            available_columns = ", ".join(df.columns)
            raise HTTPException(
                status_code=400,
                detail=f"No se encontró una columna válida para el nombre del cliente. Columnas disponibles: {available_columns}. Columnas esperadas: {', '.join(column_mapping['client_name'])}"
            )
        
        # Procesar los datos fila por fila
        processed_records = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Extraer datos con validación mejorada
                client_name = str(row[client_name_col]).strip() if pd.notna(row[client_name_col]) else None
                
                # Validar que client_name no esté vacío
                if not client_name or client_name.lower() in ['nan', 'none', '', 'null']:
                    errors.append(f"Fila {index + 2}: Nombre de cliente vacío o inválido")
                    continue
                
                client_type = str(row[client_type_col]).strip() if client_type_col and pd.notna(row[client_type_col]) else "No especificado"
                executive = str(row[executive_col]).strip() if executive_col and pd.notna(row[executive_col]) else "No asignado"
                product = str(row[product_col]).strip() if product_col and pd.notna(row[product_col]) else "No especificado"
                
                # Procesar valor numérico
                value = 0.0
                if value_col and pd.notna(row[value_col]):
                    try:
                        # Limpiar el valor de caracteres no numéricos comunes
                        value_str = str(row[value_col]).replace(',', '').replace('$', '').replace('€', '').replace(' ', '').strip()
                        value = float(value_str) if value_str else 0.0
                    except (ValueError, TypeError):
                        logger.warning(f"Fila {index + 2}: No se pudo convertir valor '{row[value_col]}' a número")
                        value = 0.0
                
                # Procesar fecha
                date = datetime.utcnow()
                if date_col and pd.notna(row[date_col]):
                    try:
                        date = pd.to_datetime(row[date_col], errors='coerce')
                        if pd.isna(date):
                            date = datetime.utcnow()
                    except:
                        date = datetime.utcnow()
                
                description = str(row[description_col]).strip() if description_col and pd.notna(row[description_col]) and str(row[description_col]).strip() != 'nan' else None
                
                processed_records.append({
                    'client_name': client_name,
                    'client_type': client_type,
                    'executive': executive,
                    'product': product,
                    'value': value,
                    'date': date,
                    'description': description
                })
                
                logger.debug(f"Registro {index + 1} procesado: {client_name}")
                
            except Exception as e:
                error_msg = f"Fila {index + 2}: Error procesando datos - {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue
        
        # Si no hay registros procesados exitosamente
        if not processed_records:
            error_detail = f"No se pudieron procesar registros válidos del CSV."
            if errors:
                error_detail += f" Errores encontrados: {'; '.join(errors[:3])}"
                if len(errors) > 3:
                    error_detail += f" y {len(errors) - 3} errores más..."
            raise HTTPException(status_code=400, detail=error_detail)
        
        logger.info(f"Registros procesados exitosamente: {len(processed_records)}")
        
        # Guardar en la base de datos usando batch insert para mejor rendimiento
        try:
            # Crear objetos ClientData
            client_objects = []
            for record in processed_records:
                client_data = ClientData(**record)
                client_objects.append(client_data)
            
            # Agregar todos los objetos a la sesión
            db.add_all(client_objects)
            
            # Confirmar la transacción
            db.commit()
            
            saved_count = len(client_objects)
            logger.info(f"Guardados {saved_count} registros en la base de datos")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error guardando en base de datos: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error guardando datos en la base de datos: {str(e)}"
            )
        
        # Preparar respuesta detallada
        response_data = {
            "success": True,
            "message": f"Archivo '{file.filename}' procesado exitosamente",
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
                }
            }
        }
        
        # Agregar errores si los hay (limitado a los primeros 10)
        if errors:
            response_data["warnings"] = errors[:10]
            if len(errors) > 10:
                response_data["warnings"].append(f"... y {len(errors) - 10} advertencias más")
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado en upload_csv: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.get("/data")
async def get_data(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_database)
):
    """Obtener datos de clientes con paginación"""
    try:
        # Obtener total de registros
        total = db.query(ClientData).count()
        
        # Obtener registros con paginación
        clients = db.query(ClientData).offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "total": total,
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
        logger.error(f"Error en get_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/summary")
async def get_data_summary(db: Session = Depends(get_database)):
    """Obtener resumen de los datos"""
    try:
        total_records = db.query(ClientData).count()
        total_value = db.query(ClientData).with_entities(
            db.func.sum(ClientData.value)
        ).scalar() or 0
        
        # Obtener algunos ejemplos
        sample_clients = db.query(ClientData).limit(5).all()
        
        return {
            "success": True,
            "summary": {
                "total_records": total_records,
                "total_value": float(total_value),
                "sample_data": [
                    {
                        "id": client.id,
                        "client_name": client.client_name,
                        "client_type": client.client_type,
                        "value": client.value
                    }
                    for client in sample_clients
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error en get_data_summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/data/clear")
async def clear_data(db: Session = Depends(get_database)):
    """Limpiar todos los datos de clientes"""
    try:
        deleted_count = db.query(ClientData).delete()
        db.commit()
        logger.info(f"Eliminados {deleted_count} registros")
        return {
            "success": True,
            "message": f"Se eliminaron {deleted_count} registros"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error en clear_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints adicionales que podrían estar siendo llamados por el frontend

@app.get("/client-data")
async def get_client_data(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_database)
):
    """Alias para /data - Obtener datos de clientes"""
    return await get_data(limit, offset, db)

@app.get("/authorized-emails")
async def get_authorized_emails(db: Session = Depends(get_database)):
    """Obtener lista de emails autorizados"""
    try:
        emails = db.query(AuthorizedEmail).all()
        return {
            "success": True,
            "count": len(emails),
            "data": [
                {
                    "id": email.id,
                    "email": email.email,
                    "added_by": email.added_by,
                    "added_at": email.added_at.isoformat() if email.added_at else None
                }
                for email in emails
            ]
        }
    except Exception as e:
        logger.error(f"Error en get_authorized_emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/authorized-emails")
async def add_authorized_email(
    email_data: dict,
    db: Session = Depends(get_database)
):
    """Agregar un email autorizado"""
    try:
        email = email_data.get("email")
        added_by = email_data.get("added_by", "admin")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email es requerido")
        
        # Verificar si ya existe
        existing = db.query(AuthorizedEmail).filter(
            AuthorizedEmail.email == email
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Email ya existe")
        
        # Crear nuevo email autorizado
        new_email = AuthorizedEmail(
            email=email,
            added_by=added_by
        )
        
        db.add(new_email)
        db.commit()
        
        return {
            "success": True,
            "message": f"Email {email} agregado exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error en add_authorized_email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tables")
async def get_tables_info(db: Session = Depends(get_database)):
    """Obtener información sobre las tablas disponibles"""
    try:
        # Obtener conteo de cada tabla
        client_data_count = db.query(ClientData).count()
        authorized_emails_count = db.query(AuthorizedEmail).count()
        
        return {
            "success": True,
            "tables": {
                "client_data": {
                    "count": client_data_count,
                    "description": "Datos de clientes importados desde CSV"
                },
                "authorized_emails": {
                    "count": authorized_emails_count,
                    "description": "Emails autorizados para acceso al sistema"
                }
            }
        }
    except Exception as e:
        logger.error(f"Error en get_tables_info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/database")
async def debug_database(db: Session = Depends(get_database)):
    """Endpoint de debug para verificar el estado de la base de datos"""
    try:
        # Verificar conexión
        db.execute("SELECT 1")
        
        # Obtener información de las tablas
        client_data_count = db.query(ClientData).count()
        authorized_emails_count = db.query(AuthorizedEmail).count()
        
        # Obtener algunos registros de ejemplo
        sample_clients = db.query(ClientData).limit(3).all()
        
        return {
            "success": True,
            "database_status": "connected",
            "tables": {
                "client_data": {
                    "count": client_data_count,
                    "sample": [
                        {
                            "id": client.id,
                            "client_name": client.client_name,
                            "value": client.value
                        }
                        for client in sample_clients
                    ]
                },
                "authorized_emails": {
                    "count": authorized_emails_count
                }
            }
        }
    except Exception as e:
        logger.error(f"Error en debug_database: {str(e)}")
        return {
            "success": False,
            "database_status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)