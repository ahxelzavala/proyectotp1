FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del backend
COPY . .

# Crear directorio para ML models si no existe
RUN mkdir -p ml_models

# Exponer puerto para Cloud Run
EXPOSE 8080

# Comando para ejecutar el backend
CMD ["python", "main.py"]