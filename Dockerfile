FROM python:3.12-slim

# Evita que Python escriba archivos .pyc y fuerza la salida por consola
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instalar dependencias del sistema (necesarias para psycopg2)
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# El comando para arrancar Gunicorn (servidor de producción)
CMD ["gunicorn", "NexoRetail.wsgi:application", "--bind", "0.0.0.0:8000"]