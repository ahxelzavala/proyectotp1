FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run inyecta la variable PORT
ENV PORT=8080
EXPOSE 8080

# IMPORTANTE: Usar la variable $PORT
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}