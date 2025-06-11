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
        
        # Leer el contenido del archivo
        contents = await file.read()
        
        # Crear un objeto StringIO para pandas
        csv_string = contents.decode('utf-8')
        csv_io = io.StringIO(csv_string)
        
        # Leer el CSV con pandas
        try:
            df = pd.read_csv(csv_io)
        except Exception as e:
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
        
        # Mapear columnas esperadas
        column_mapping = {
            'client_name': ['client_name', 'nombre_cliente', 'cliente', 'name'],
            'client_type': ['client_type', 'tipo_cliente', 'tipo', 'type'],
            'executive': ['executive', 'ejecutivo', 'responsable'],
            'product': ['product', 'producto'],
            'value': ['value', 'valor', 'amount', 'monto'],
            'date': ['date', 'fecha'],
            'description': ['description', 'descripcion', 'desc']
        }
        
        # Función para encontrar la columna correcta
        def find_column(possible_names, df_columns):
            df_columns_lower = [col.lower() for col in df_columns]
            for name in possible_names:
                if name.lower() in df_columns_lower:
                    # Retornar el nombre original de la columna
                    idx = df_columns_lower.index(name.lower())
                    return df_columns[idx]
            return None
        
        # Crear un diccionario con los datos procesados
        processed_records = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Buscar las columnas necesarias
                client_name_col = find_column(column_mapping['client_name'], df.columns)
                client_type_col = find_column(column_mapping['client_type'], df.columns)
                executive_col = find_column(column_mapping['executive'], df.columns)
                product_col = find_column(column_mapping['product'], df.columns)
                value_col = find_column(column_mapping['value'], df.columns)
                date_col = find_column(column_mapping['date'], df.columns)
                description_col = find_column(column_mapping['description'], df.columns)
                
                # Validar campos obligatorios
                if not client_name_col:
                    errors.append(f"Fila {index + 1}: No se encontró columna de nombre de cliente")
                    continue
                
                # Extraer datos
                client_name = str(row[client_name_col]) if pd.notna(row[client_name_col]) else None
                client_type = str(row[client_type_col]) if client_type_col and pd.notna(row[client_type_col]) else "No especificado"
                executive = str(row[executive_col]) if executive_col and pd.notna(row[executive_col]) else "No asignado"
                product = str(row[product_col]) if product_col and pd.notna(row[product_col]) else "No especificado"
                
                # Procesar valor
                value = 0.0
                if value_col and pd.notna(row[value_col]):
                    try:
                        value = float(str(row[value_col]).replace(',', '').replace('$', ''))
                    except ValueError:
                        value = 0.0
                
                # Procesar fecha
                date = datetime.utcnow()
                if date_col and pd.notna(row[date_col]):
                    try:
                        date = pd.to_datetime(row[date_col])
                    except:
                        date = datetime.utcnow()
                
                description = str(row[description_col]) if description_col and pd.notna(row[description_col]) else None
                
                # Validar que client_name no esté vacío
                if not client_name or client_name.lower() in ['nan', 'none', '']:
                    errors.append(f"Fila {index + 1}: Nombre de cliente vacío")
                    continue
                
                processed_records.append({
                    'client_name': client_name,
                    'client_type': client_type,
                    'executive': executive,
                    'product': product,
                    'value': value,
                    'date': date,
                    'description': description
                })
                
            except Exception as e:
                errors.append(f"Fila {index + 1}: Error procesando datos - {str(e)}")
                continue
        
        # Si no hay registros procesados exitosamente
        if not processed_records:
            raise HTTPException(
                status_code=400,
                detail=f"No se pudieron procesar registros. Errores: {'; '.join(errors[:5])}"
            )
        
        # Guardar en la base de datos
        saved_count = 0
        db_errors = []
        
        for record in processed_records:
            try:
                client_data = ClientData(**record)
                db.add(client_data)
                saved_count += 1
            except Exception as e:
                db_errors.append(f"Error guardando registro: {str(e)}")
        
        # Confirmar transacción
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error guardando en base de datos: {str(e)}"
            )
        
        # Preparar respuesta
        response_data = {
            "success": True,
            "message": f"Archivo procesado exitosamente",
            "details": {
                "filename": file.filename,
                "total_rows": len(df),
                "processed_rows": len(processed_records),
                "saved_rows": saved_count,
                "errors_count": len(errors) + len(db_errors)
            }
        }
        
        # Agregar errores si los hay
        if errors or db_errors:
            response_data["errors"] = errors + db_errors
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.get("/data")
async def get_data(db: Session = Depends(get_database)):
    """Obtener todos los datos de clientes"""
    try:
        clients = db.query(ClientData).all()
        return {
            "success": True,
            "count": len(clients),
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
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/data/clear")
async def clear_data(db: Session = Depends(get_database)):
    """Limpiar todos los datos de clientes"""
    try:
        deleted_count = db.query(ClientData).delete()
        db.commit()
        return {
            "success": True,
            "message": f"Se eliminaron {deleted_count} registros"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)