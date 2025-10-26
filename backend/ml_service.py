# backend/ml_service.py (Versión corregida para usar modelo real)
import pandas as pd
import numpy as np
import xgboost as xgb
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
        self.demo_mode = False  # Cambiar default a False
        
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
            
            # Cargar metadatos primero
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        self.model_metadata = json.load(f)
                    logger.info("✅ Metadatos ML cargados")
                    
                    # Obtener nombres de features
                    self.feature_names = self.model_metadata.get('feature_names', [])
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando metadatos: {e}")
                    self._activate_demo_mode()
                    return
            else:
                logger.warning("⚠️ Archivo de metadatos no encontrado")
                self._activate_demo_mode()
                return
            
            # Intentar cargar modelo XGBoost
            model_loaded = False
            
            # Primero intentar .json
            json_path = Path("ml_models/xgboost_model_v1.json")
            if json_path.exists():
                try:
                    self.model = xgb.XGBClassifier()
                    self.model.load_model(str(json_path))
                    model_loaded = True
                    logger.info("✅ Modelo XGBoost cargado desde JSON")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando modelo JSON: {e}")
            
            # Si no funciona JSON, intentar .pkl
            if not model_loaded:
                pkl_path = Path("ml_models/xgboost_model_v1.pkl")
                if pkl_path.exists():
                    try:
                        import pickle
                        with open(pkl_path, 'rb') as f:
                            self.model = pickle.load(f)
                        model_loaded = True
                        logger.info("✅ Modelo XGBoost cargado desde PKL")
                    except Exception as e:
                        logger.warning(f"⚠️ Error cargando modelo PKL: {e}")
            
            if model_loaded:
                self.is_loaded = True
                self.demo_mode = False
                logger.info("🎯 Modelo REAL cargado y listo para predicciones")
            else:
                logger.warning("⚠️ No se pudo cargar modelo real, activando modo DEMO")
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
                "threshold": 0.5,  # Usar el threshold de los metadatos reales
                "metrics": {
                    "accuracy": 0.8008,
                    "precision": 0.6861,
                    "recall": 0.5729,
                    "f1_score": 0.6244,
                    "roc_auc": 0.8466
                },
                "feature_names": [
                    "Tipo de Cliente", "SUPERCATEGORIA_DISPERSANTES", "SUPERCATEGORIA_ENDURECEDORES / CURING AGENTS",
                    "SUPERCATEGORIA_LABORATORIO", "SUPERCATEGORIA_MODIFICADORES REOLÓGICOS", "SUPERCATEGORIA_OTROS",
                    "SUPERCATEGORIA_PIGMENTOS / EFECTOS", "SUPERCATEGORIA_PLASTIFICANTES", "SUPERCATEGORIA_PRESERVANTES",
                    "SUPERCATEGORIA_RESINAS / AGLUTINANTES", "SUPERCATEGORIA_SOLVENTES", "SKU", "Codigo", "Tipo_Cliente",
                    "CATEGORIA", "Cantidad", "P. Venta", "C. Unit", "Venta", "Costo", "MB"
                ],
                "model_type": "DEMO Mode",
                "demo_mode": True
            }
        
        self.feature_names = self.model_metadata.get('feature_names', [])
        logger.info("✅ Modo DEMO ML activado")
    
    def predict_cross_sell(self, client_data: List[Dict], threshold: Optional[float] = None) -> List[Dict]:
        """Realizar predicciones de venta cruzada"""
        if not self.is_loaded:
            raise Exception("Modelo no está cargado")
        
        try:
            if threshold is None:
                threshold = self.model_metadata.get('threshold', 0.5)
            
            results = []
            
            for i, client_info in enumerate(client_data):
                if self.demo_mode:
                    # Usar lógica demo
                    prob = self._calculate_demo_probability(client_info)
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
    
    def _predict_with_real_model(self, client_info: Dict) -> float:
        """Hacer predicción con el modelo XGBoost real"""
        try:
            # Preparar datos según los feature_names del modelo
            feature_data = []
            
            # Mapear datos del cliente a las features esperadas
            for feature_name in self.feature_names:
                if feature_name in client_info:
                    feature_data.append(client_info[feature_name])
                else:
                    # Valor por defecto para features faltantes
                    feature_data.append(0.0)
            
            # Convertir a formato que espera XGBoost
            X = np.array([feature_data])
            
            # Obtener probabilidad (para clasificación binaria)
            if hasattr(self.model, 'predict_proba'):
                prob = self.model.predict_proba(X)[0][1]  # Probabilidad de clase positiva
            else:
                # Si es un booster directo
                prob = self.model.predict(X)[0]
            
            return float(prob)
            
        except Exception as e:
            logger.error(f"❌ Error en predicción real: {e}")
            # Fallback a demo si hay error
            return self._calculate_demo_probability(client_info)
    
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
            "threshold": self.model_metadata.get('threshold', 0.5),
            "metrics": self.model_metadata.get('metrics', {}),
            "feature_count": len(self.feature_names),
            "feature_names": self.feature_names,
            "model_type": "XGBoost Classifier" if not self.demo_mode else "Demo Mode",
            "demo_mode": self.demo_mode
        }
        
        if self.demo_mode:
            info["warning"] = "Ejecutándose en modo DEMO con predicciones simuladas"
        else:
            info["success"] = "Usando modelo XGBoost REAL"
        
        return info
    
    def get_feature_importance(self) -> List[Dict]:
        """Obtener importancia de features"""
        if not self.is_loaded:
            return []
        
        if self.demo_mode or not hasattr(self.model, 'feature_importances_'):
            # Importancia simulada
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
        else:
            # Importancia real del modelo
            importances = self.model.feature_importances_
            feature_importance = []
            
            for i, importance in enumerate(importances):
                if i < len(self.feature_names):
                    feature_importance.append({
                        "feature": self.feature_names[i],
                        "importance": float(importance),
                        "importance_percentage": float(importance * 100)
                    })
            
            # Ordenar por importancia descendente
            feature_importance.sort(key=lambda x: x['importance'], reverse=True)
            return feature_importance

# Instancia global del servicio ML
ml_service = MLService()