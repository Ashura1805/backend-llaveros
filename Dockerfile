# Usamos una imagen ligera de Python
FROM python:3.10-slim

# Evita que Python guarde archivos caché y permite ver los logs al instante
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Creamos la carpeta de trabajo
WORKDIR /app

# Instalamos dependencias
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código
COPY . .

# COMANDO FIJO:
# Como tu carpeta interna se llama "backend", apuntamos directo a ella.
CMD gunicorn --bind 0.0.0.0:$PORT backend.wsgi:application