#!/usr/bin/env python3
"""
Script para configurar y verificar la conexión a la base de datos
"""
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings

def test_postgresql_connection():
    """Verificar que PostgreSQL esté corriendo"""
    try:
        # Conectar a PostgreSQL (sin especificar base de datos)
        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            password="ben10ultimatealien",
            port=5432
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("✅ Conexión a PostgreSQL exitosa")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        return None

def create_database_if_not_exists():
    """Crear la base de datos si no existe"""
    conn = test_postgresql_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar si la base de datos existe
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'anders_db'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute('CREATE DATABASE anders_db')
            print("✅ Base de datos 'anders_db' creada exitosamente")
        else:
            print("ℹ️  Base de datos 'anders_db' ya existe")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error creando base de datos: {e}")
        return False

def test_database_connection():
    """Verificar conexión a la base de datos específica"""
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print("✅ Conexión a anders_db exitosa")
            print(f"ℹ️  Versión PostgreSQL: {version}")
            return True
    except OperationalError as e:
        print(f"❌ Error conectando a anders_db: {e}")
        return False

def create_tables():
    """Crear las tablas necesarias"""
    try:
        from models import create_tables
        create_tables()
        return True
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def add_sample_authorized_email():
    """Agregar un email autorizado de ejemplo"""
    try:
        from models import SessionLocal, AuthorizedEmail
        
        db = SessionLocal()
        
        # Verificar si ya existe
        existing = db.query(AuthorizedEmail).filter(
            AuthorizedEmail.email == "admin@example.com"
        ).first()
        if existing:
            print("ℹ️  Email autorizado de ejemplo ya existe")
            db.close()
            return True
        
        # Crear email autorizado de ejemplo
        sample_email = AuthorizedEmail(
            email="admin@example.com",
            added_by="system"
        )
        db.add(sample_email)
        db.commit()
        
        print("✅ Email autorizado de ejemplo agregado: admin@example.com")
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error agregando email autorizado de ejemplo: {e}")
        return False

def main():
    """Función principal de setup"""
    print("🚀 Iniciando configuración de base de datos...\n")
    
    # Paso 1: Verificar PostgreSQL
    print("1. Verificando conexión a PostgreSQL...")
    if not test_postgresql_connection():
        print("❌ No se pudo conectar a PostgreSQL. Verifica que esté corriendo.")
        return
    
    # Paso 2: Crear base de datos
    print("\n2. Verificando/creando base de datos...")
    if not create_database_if_not_exists():
        print("❌ No se pudo crear la base de datos.")
        return
    
    # Paso 3: Verificar conexión a la base de datos específica
    print("\n3. Verificando conexión a anders_db...")
    if not test_database_connection():
        print("❌ No se pudo conectar a la base de datos anders_db.")
        return
    
    # Paso 4: Crear tablas
    print("\n4. Creando tablas...")
    if not create_tables():
        print("❌ No se pudieron crear las tablas.")
        return
    
    # Paso 5: Agregar datos de ejemplo
    print("\n5. Agregando datos de ejemplo...")
    if not add_sample_authorized_email():
        print("❌ No se pudo agregar el email autorizado de ejemplo.")
        return
    
    print("\n🎉 ¡Configuración completada exitosamente!")
    print("\nPuedes iniciar el servidor con:")
    print("uvicorn main:app --reload")
    print("\nY acceder a la documentación en:")
    print("http://localhost:8000/docs")

if __name__ == "__main__":
    main()