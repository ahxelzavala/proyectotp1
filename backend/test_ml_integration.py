# test_ml_integration.py - Script para verificar la integración del modelo

import sys
import json
import os
from pathlib import Path

def check_model_files():
    """Verificar que los archivos del modelo existan"""
    print("🔍 VERIFICANDO ARCHIVOS DEL MODELO")
    print("=" * 50)
    
    model_file = "xgboost_model.json"
    metadata_file = "model_metadata.json"
    
    checks = []
    
    # Verificar archivo del modelo
    if os.path.exists(model_file):
        size = os.path.getsize(model_file)
        print(f"✅ {model_file} encontrado ({size:,} bytes)")
        checks.append(True)
        
        # Verificar que sea JSON válido
        try:
            with open(model_file, 'r') as f:
                model_data = json.load(f)
            print(f"✅ Estructura JSON válida")
            
            # Verificar componentes clave
            if 'learner' in model_data:
                feature_count = len(model_data['learner']['feature_names'])
                tree_count = model_data['learner']['gradient_booster']['model']['gbtree_model_param']['num_trees']
                print(f"✅ {feature_count} features, {tree_count} árboles")
            else:
                print("⚠️ Estructura del modelo no reconocida")
                
        except json.JSONDecodeError as e:
            print(f"❌ Error JSON: {e}")
            checks.append(False)
    else:
        print(f"❌ {model_file} NO encontrado")
        checks.append(False)
    
    # Verificar metadatos
    if os.path.exists(metadata_file):
        size = os.path.getsize(metadata_file)
        print(f"✅ {metadata_file} encontrado ({size:,} bytes)")
        checks.append(True)
        
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            print(f"✅ Metadatos válidos")
            print(f"   - Versión: {metadata.get('model_version', 'N/A')}")
            print(f"   - Fecha entrenamiento: {metadata.get('training_date', 'N/A')}")
            print(f"   - Threshold: {metadata.get('threshold', 'N/A')}")
            print(f"   - Accuracy: {metadata.get('metrics', {}).get('accuracy', 'N/A')}")
            
        except json.JSONDecodeError as e:
            print(f"❌ Error JSON en metadatos: {e}")
            checks.append(False)
    else:
        print(f"❌ {metadata_file} NO encontrado")
        checks.append(False)
    
    return all(checks)

def check_ml_service():
    """Verificar que ml_service.py funcione"""
    print("\n🔧 VERIFICANDO ML SERVICE")
    print("=" * 50)
    
    try:
        # Intentar importar el servicio
        sys.path.append('.')
        from ml_service import MLService, ml_service
        
        print("✅ ml_service importado correctamente")
        
        # Verificar estado
        info = ml_service.get_model_info()
        print(f"✅ Estado del modelo:")
        print(f"   - Cargado: {info.get('loaded', False)}")
        print(f"   - Modo demo: {info.get('demo_mode', False)}")
        print(f"   - Features: {info.get('feature_count', 0)}")
        
        # Test de predicción
        test_data = [{
            "id": 999,
            "cliente": "Cliente Test",
            "venta": 5000.0,
            "costo": 3500.0,
            "mb": 1500.0,
            "cantidad": 10.0,
            "tipo_de_cliente": "Fabricante químicos",
            "categoria": "RESINAS"
        }]
        
        predictions = ml_service.predict_cross_sell(test_data)
        if predictions:
            pred = predictions[0]
            print(f"✅ Predicción test:")
            print(f"   - Cliente: {pred['cliente']}")
            print(f"   - Predicción: {pred['prediction']}")
            print(f"   - Probabilidad: {pred['probability']:.3f}")
            print(f"   - Modo demo: {pred.get('demo_mode', False)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importando ml_service: {e}")
        return False
    except Exception as e:
        print(f"❌ Error en ml_service: {e}")
        return False

def check_fastapi_integration():
    """Verificar integración con FastAPI"""
    print("\n🌐 VERIFICANDO INTEGRACIÓN FASTAPI")
    print("=" * 50)
    
    try:
        # Leer main.py y verificar endpoints ML
        if os.path.exists('main.py'):
            with open('main.py', 'r', encoding='utf-8') as f:
                main_content = f.read()
            
            ml_endpoints = [
                '/ml/status',
                '/ml/cross-sell-recommendations', 
                '/ml/model-performance',
                '/ml/predict-cross-sell'
            ]
            
            found_endpoints = []
            for endpoint in ml_endpoints:
                if endpoint in main_content:
                    found_endpoints.append(endpoint)
                    print(f"✅ Endpoint {endpoint} encontrado")
                else:
                    print(f"❌ Endpoint {endpoint} NO encontrado")
            
            # Verificar importaciones
            if 'from ml_service import ml_service' in main_content:
                print("✅ Importación de ml_service encontrada")
            else:
                print("❌ Importación de ml_service NO encontrada")
            
            # Verificar modelos Pydantic
            if 'PredictionRequest' in main_content:
                print("✅ Modelos Pydantic encontrados")
            else:
                print("❌ Modelos Pydantic NO encontrados")
            
            return len(found_endpoints) >= 3
            
        else:
            print("❌ main.py no encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando FastAPI: {e}")
        return False

def check_dependencies():
    """Verificar dependencias necesarias"""
    print("\n📦 VERIFICANDO DEPENDENCIAS")
    print("=" * 50)
    
    required_packages = [
        'xgboost',
        'pandas', 
        'numpy',
        'fastapi',
        'pydantic'
    ]
    
    available = []
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} disponible")
            available.append(package)
        except ImportError:
            print(f"❌ {package} NO disponible")