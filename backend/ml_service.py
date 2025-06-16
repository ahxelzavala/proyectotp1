# backend/ml_service.py
import joblib
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
        self.feature_names = None
        self.target_encoder = None
        self.is_loaded = False
        
        # Paths to model files
        self.model_path = Path("ml_models/xgboost_model_v1.pkl")
        self.metadata_path = Path("ml_models/model_metadata.json")
        
        # Auto-load model on initialization
        self.load_model()
    
    def load_model(self) -> bool:
        """Cargar el modelo entrenado y sus metadatos"""
        try:
            # Verificar que existan los archivos
            if not self.model_path.exists():
                logger.warning(f"Archivo de modelo no encontrado: {self.model_path}")
                return False
            
            if not self.metadata_path.exists():
                logger.warning(f"Archivo de metadatos no encontrado: {self.metadata_path}")
                return False
            
            # Cargar modelo
            self.model = joblib.load(self.model_path)
            logger.info("✅ Modelo XGBoost cargado exitosamente")
            
            # Cargar metadatos
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.model_metadata = json.load(f)
            
            self.feature_names = self.model_metadata.get('feature_names', [])
            logger.info(f"✅ Metadatos cargados: {len(self.feature_names)} features")
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {str(e)}")
            self.is_loaded = False
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Obtener información del modelo"""
        if not self.is_loaded:
            return {
                "loaded": False,
                "error": "Modelo no cargado"
            }
        
        return {
            "loaded": True,
            "model_version": self.model_metadata.get('model_version', 'Unknown'),
            "training_date": self.model_metadata.get('training_date', 'Unknown'),
            "threshold": self.model_metadata.get('threshold', 0.4),
            "metrics": self.model_metadata.get('metrics', {}),
            "feature_count": len(self.feature_names),
            "feature_names": self.feature_names,
            "model_type": "XGBoost Classifier"
        }
    
    def prepare_features(self, client_data: List[Dict]) -> pd.DataFrame:
        """Preparar features para predicción"""
        try:
            # Convertir a DataFrame
            df = pd.DataFrame(client_data)
            
            # Crear features derivados como en el entrenamiento
            df_features = df.copy()
            
            # 1. Features básicos (mapeo de columnas)
            feature_mapping = {
                'venta': 'venta',
                'costo': 'costo', 
                'mb': 'mb',
                'cantidad': 'cantidad',
                'tipo_de_cliente': 'tipo_de_cliente',
                'categoria': 'categoria',
                'comercial': 'comercial',
                'proveedor': 'proveedor'
            }
            
            # Aplicar mapeo y valores por defecto
            for model_feature, data_column in feature_mapping.items():
                if data_column in df.columns:
                    df_features[model_feature] = df[data_column]
                else:
                    df_features[model_feature] = 0 if model_feature in ['venta', 'costo', 'mb', 'cantidad'] else 'Unknown'
            
            # 2. Features derivados (como en el entrenamiento)
            df_features['rentabilidad'] = np.where(
                df_features['venta'] != 0,
                df_features['mb'] / df_features['venta'],
                0
            )
            
            df_features['ratio_costo_venta'] = np.where(
                df_features['venta'] != 0,
                df_features['costo'] / df_features['venta'],
                0
            )
            
            df_features['margen_unitario'] = np.where(
                df_features['cantidad'] != 0,
                df_features['mb'] / df_features['cantidad'],
                0
            )
            
            # 3. Target encoding simplificado (usar valores promedio)
            # En producción, deberías usar los encoders entrenados
            tipo_cliente_encoding = {
                'EMPRESA': 0.35,
                'PARTICULAR': 0.25,
                'GOBIERNO': 0.45,
                'Unknown': 0.30
            }
            
            categoria_encoding = {
                'ELECTRICOS': 0.40,
                'MECANICOS': 0.30,
                'HERRAMIENTAS': 0.35,
                'Unknown': 0.30
            }
            
            df_features['tipo_de_cliente_encoded'] = df_features['tipo_de_cliente'].map(
                tipo_cliente_encoding
            ).fillna(0.30)
            
            df_features['categoria_encoded'] = df_features['categoria'].map(
                categoria_encoding
            ).fillna(0.30)
            
            # 4. Seleccionar solo las features del modelo
            expected_features = [
                'venta', 'costo', 'mb', 'cantidad', 'rentabilidad', 
                'ratio_costo_venta', 'margen_unitario', 
                'tipo_de_cliente_encoded', 'categoria_encoded'
            ]
            
            # Verificar que todas las features estén presentes
            for feature in expected_features:
                if feature not in df_features.columns:
                    df_features[feature] = 0.0
            
            # Seleccionar y ordenar features
            X = df_features[expected_features].copy()
            
            # Convertir a numérico y manejar NaN
            for col in X.columns:
                X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
            
            logger.info(f"✅ Features preparados: {X.shape}")
            logger.info(f"Features utilizados: {list(X.columns)}")
            
            return X
            
        except Exception as e:
            logger.error(f"❌ Error preparando features: {str(e)}")
            raise
    
    def predict_cross_sell(self, client_data: List[Dict], threshold: Optional[float] = None) -> List[Dict]:
        """Realizar predicciones de venta cruzada"""
        if not self.is_loaded:
            raise Exception("Modelo no está cargado")
        
        try:
            # Usar threshold del modelo si no se especifica
            if threshold is None:
                threshold = self.model_metadata.get('threshold', 0.4)
            
            # Preparar features
            X = self.prepare_features(client_data)
            
            # Realizar predicciones
            probabilities = self.model.predict_proba(X)[:, 1]  # Probabilidad de clase positiva
            predictions = (probabilities >= threshold).astype(int)
            
            # Preparar resultados
            results = []
            for i, (prob, pred) in enumerate(zip(probabilities, predictions)):
                client_info = client_data[i]
                
                # Determinar nivel de prioridad
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
                    
                    # Información adicional del cliente
                    "venta_actual": client_info.get('venta', 0),
                    "categoria": client_info.get('categoria', 'N/A'),
                    "tipo_cliente": client_info.get('tipo_de_cliente', 'N/A'),
                    "comercial": client_info.get('comercial', 'N/A'),
                    
                    # Metadatos de predicción
                    "prediction_date": datetime.now().isoformat(),
                    "model_version": self.model_metadata.get('model_version', '1.0')
                }
                
                results.append(result)
            
            logger.info(f"✅ Predicciones completadas: {len(results)} clientes procesados")
            
            # Estadísticas de la predicción
            positive_predictions = sum(1 for r in results if r['prediction'] == 1)
            avg_probability = np.mean([r['probability'] for r in results])
            
            logger.info(f"📊 Estadísticas: {positive_predictions}/{len(results)} recomendaciones positivas")
            logger.info(f"📊 Probabilidad promedio: {avg_probability:.3f}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error en predicción: {str(e)}")
            raise
    
    def predict_single_client(self, client_data: Dict, threshold: Optional[float] = None) -> Dict:
        """Predicción para un solo cliente"""
        results = self.predict_cross_sell([client_data], threshold)
        return results[0] if results else {}
    
    def get_feature_importance(self) -> List[Dict]:
        """Obtener importancia de features del modelo"""
        if not self.is_loaded:
            return []
        
        try:
            # Obtener importancia de features
            importance = self.model.feature_importances_
            feature_names = self.feature_names
            
            # Si no hay feature_names, usar nombres genéricos
            if not feature_names or len(feature_names) != len(importance):
                feature_names = [f"feature_{i}" for i in range(len(importance))]
            
            # Crear lista ordenada por importancia
            feature_importance = []
            for name, imp in zip(feature_names, importance):
                feature_importance.append({
                    "feature": name,
                    "importance": float(imp),
                    "importance_percentage": round(float(imp) * 100, 2)
                })
            
            # Ordenar por importancia
            feature_importance.sort(key=lambda x: x['importance'], reverse=True)
            
            return feature_importance
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo feature importance: {str(e)}")
            return []

# Instancia global del servicio ML
ml_service = MLService()