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
from pathlib import Path

# Importar modelos y configuración
from models import get_database, ClientData, AuthorizedEmail, create_tables, test_database_connection, migrate_add_new_columns
from config import settings

# ML Service simplificado para Cloud Run
ML_AVAILABLE = False
print("⚠️ ML Service deshabilitado temporalmente para Cloud Run")

class MockMLService:
    def __init__(self):
        self.is_loaded = True
        self.demo_mode = True

    def get_model_info(self):
        return {
            "loaded": True,
            "model_version": "Demo v1.0",
            "demo_mode": True
        }

    def predict_cross_sell(self, client_data, threshold=None):
        # Predicciones demo simples
        results = []
        for i, client in enumerate(client_data):
            import random
            random.seed(hash(str(client.get('cliente', i))) % 1000)
            prob = 0.3 + (random.random() * 0.4)
            
            results.append({
                "client_id": client.get('id', i),
                "client_name": client.get('cliente', f"Cliente_{i}"),
                "probability": round(prob, 4),
                "prediction": 1 if prob >= 0.5 else 0,
                "recommendation": "Sí" if prob >= 0.5 else "No",
                "priority": "Alta" if prob >= 0.7 else ("Media" if prob >= 0.5 else "Baja"),
                "demo_mode": True
            })
        return results

    def get_feature_importance(self):
        return []

ml_service = MockMLService()

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

@app.get("/ml/status")
async def get_ml_status():
    """Verificar el estado del modelo de ML"""
    try:
        model_info = ml_service.get_model_info()
        return {
            "success": True,
            "model_info": model_info,
            "message": "Modelo en modo demo"
        }
    except Exception as e:
        logger.error(f"Error verificando estado ML: {str(e)}")
        return {
            "success": False,
            "model_info": {"loaded": False},
            "message": f"Error: {str(e)}"
        }

@app.get("/debug/count")
async def debug_count(db: Session = Depends(get_database)):
    """Endpoint de debug para verificar el conteo de registros"""
    try:
        count = db.query(ClientData).count()
        return {
            "count": count, 
            "message": f"Hay {count} registros en la base de datos"
        }
    except Exception as e:
        logger.error(f"Error en debug count: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Puerto para Cloud Run
    port = int(os.environ.get("PORT", 8080))
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
