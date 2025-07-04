FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorio para modelos ML
RUN mkdir -p ml_models

# Exponer puerto por defecto
EXPOSE 8080

# Cloud Run pasa PORT como variable de entorno
# Usar script para manejar PORT dinámicamente
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
