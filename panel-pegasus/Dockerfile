# Usar imagen base de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para mysqlclient
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Gunicorn para producción
RUN pip install gunicorn

# Copiar todo el proyecto
COPY . .

# Crear el archivo correos.txt si no existe (para evitar errores)
RUN touch correos.txt

# Exponer el puerto 8000
EXPOSE 8000

# Comando para ejecutar con Gunicorn (PRODUCCIÓN)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "main:app"]
