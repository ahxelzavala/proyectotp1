FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar todo el código
COPY . .

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

# Comando de inicio
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1