# backend/ml_service.py (Versión simplificada para evitar errores)
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self):
        self.model = None
        self.model_metadata = None
        self.feature_names = []
        self.is_loaded = False
        self.demo_mode = True
        
        # Intentar cargar modelo
        self._initialize()
    
    def _initialize(self):
        """Inicializar el servicio ML"""
        try:
            # Verificar si existen archivos de modelo
            model_paths = [
                Path("ml_models/xgboost_model_v1.pkl"),
                Path("ml_models/xgboost_model_v1.json"),
            ]
            metadata_path = Path("ml_models/model_metadata.json")
            
            # Si no hay archivos, activar modo demo
            if not any(p.exists() for p in model_paths) or not metadata_path.exists():
                logger.info("🔄 Activando modo DEMO - archivos de modelo no encontrados")
                self._activate_demo_mode()
                return
            
            # Intentar cargar metadatos
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        self.model_metadata = json.load(f)
                    logger.info("✅ Metadatos ML cargados")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando metadatos: {e}")
            
            # Para esta versión simplificada, usar modo demo con metadatos reales
            self._activate_demo_mode()
            
        except Exception as e:
            logger.error(f"❌ Error inicializando ML Service: {e}")
            self._activate_demo_mode()
    
    def _activate_demo_mode(self):
        """Activar modo demo con predicciones simuladas"""
        self.demo_mode = True
        self.is_loaded = True
        
        if not self.model_metadata:
            self.model_metadata = {
                "model_version": "DEMO-1.0",
                "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "threshold": 0.4,
                "metrics": {
                    "accuracy": 0.7824,
                    "precision": 0.5972,
                    "recall": 0.7673,
                    "f1_score": 0.6717,
                    "roc_auc": 0.8462
                },
                "feature_names": [
                    "venta", "costo", "mb", "cantidad", "rentabilidad",
                    "ratio_costo_venta", "margen_unitario", 
                    "tipo_de_cliente_encoded", "categoria_encoded"
                ],
                "model_type": "DEMO Mode",
                "demo_mode": True
            }
        
        self.feature_names = self.model_metadata.get('feature_names', [])
        logger.info("✅ Modo DEMO ML activado")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Obtener información del modelo"""
        if not self.is_loaded:
            return {
                "loaded": False,
                "error": "Modelo no cargado"
            }
        
        info = {
            "loaded": True,
            "model_version": self.model_metadata.get('model_version', 'Unknown'),
            "training_date": self.model_metadata.get('training_date', 'Unknown'),
            "threshold": self.model_metadata.get('threshold', 0.4),
            "metrics": self.model_metadata.get('metrics', {}),
            "feature_count": len(self.feature_names),
            "feature_names": self.feature_names,
            "model_type": self.model_metadata.get('model_type', 'Demo Mode'),
            "demo_mode": self.demo_mode
        }
        
        if self.demo_mode:
            info["warning"] = "Ejecutándose en modo DEMO con predicciones simuladas"
        
        return info
    
    def predict_cross_sell(self, client_data: List[Dict], threshold: Optional[float] = None) -> List[Dict]:
        """Realizar predicciones de venta cruzada (modo demo)"""
        if not self.is_loaded:
            raise Exception("Modelo no está cargado")
        
        try:
            if threshold is None:
                threshold = self.model_metadata.get('threshold', 0.4)
            
            # Generar predicciones demo
            results = []
            for i, client_info in enumerate(client_data):
                
                # Lógica de negocio simple para demo
                prob = self._calculate_demo_probability(client_info)
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
                    "venta_actual": client_info.get('venta', 0),
                    "categoria": client_info.get('categoria', 'N/A'),
                    "tipo_cliente": client_info.get('tipo_de_cliente', 'N/A'),
                    "comercial": client_info.get('comercial', 'N/A'),
                    "prediction_date": datetime.now().isoformat(),
                    "model_version": self.model_metadata.get('model_version', '1.0'),
                    "demo_mode": self.demo_mode
                }
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error en predicción: {str(e)}")
            raise
    
    def _calculate_demo_probability(self, client_info: Dict) -> float:
        """Calcular probabilidad demo basada en reglas de negocio"""
        try:
            # Base probability
            prob = 0.3
            
            # Factores de venta
            venta = float(client_info.get('venta', 0))
            if venta > 10000:
                prob += 0.25
            elif venta > 5000:
                prob += 0.15
            elif venta > 1000:
                prob += 0.1
            
            # Factores de margen
            mb = float(client_info.get('mb', 0))
            if mb > 0 and venta > 0:
                rentabilidad = mb / venta
                if rentabilidad > 0.3:
                    prob += 0.2
                elif rentabilidad > 0.15:
                    prob += 0.1
            
            # Factores de tipo de cliente
            tipo = client_info.get('tipo_de_cliente', '').upper()
            if 'EMPRESA' in tipo:
                prob += 0.15
            elif 'GOBIERNO' in tipo:
                prob += 0.2
            elif 'PARTICULAR' in tipo:
                prob += 0.05
            
            # Factores de categoría
            categoria = client_info.get('categoria', '').upper()
            if 'ELECTRICO' in categoria:
                prob += 0.1
            elif 'MECANICO' in categoria:
                prob += 0.08
            elif 'HERRAMIENTA' in categoria:
                prob += 0.12
            
            # Añadir variabilidad controlada
            import random
            seed_value = hash(str(client_info.get('cliente', ''))) % 1000000
            random.seed(seed_value)
            noise = random.uniform(-0.05, 0.05)
            prob += noise
            
            # Mantener en rango válido
            return max(0.05, min(0.95, prob))
            
        except Exception as e:
            logger.warning(f"Error calculando probabilidad demo: {e}")
            return 0.3
    
    def get_feature_importance(self) -> List[Dict]:
        """Obtener importancia de features (demo)"""
        if not self.is_loaded:
            return []
        
        # Importancia simulada realista
        demo_importance = [
            {"feature": "venta", "importance": 0.25, "importance_percentage": 25.0},
            {"feature": "rentabilidad", "importance": 0.20, "importance_percentage": 20.0},
            {"feature": "mb", "importance": 0.15, "importance_percentage": 15.0},
            {"feature": "tipo_de_cliente_encoded", "importance": 0.12, "importance_percentage": 12.0},
            {"feature": "categoria_encoded", "importance": 0.10, "importance_percentage": 10.0},
            {"feature": "cantidad", "importance": 0.08, "importance_percentage": 8.0},
            {"feature": "margen_unitario", "importance": 0.05, "importance_percentage": 5.0},
            {"feature": "ratio_costo_venta", "importance": 0.03, "importance_percentage": 3.0},
            {"feature": "costo", "importance": 0.02, "importance_percentage": 2.0}
        ]
        return demo_importance

# Instancia global del servicio ML
ml_service = MLService()