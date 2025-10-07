# Usa una imagen base de Python
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de dependencias
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el proyecto
COPY . .

# Expone el puerto (ajusta según tu aplicación)
EXPOSE 8000

# Comando para ejecutar la aplicación
# Si usas Flask:
CMD ["python", "main.py"]

# O si prefieres usar Flask directamente:
# CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]

# O con Gunicorn (recomendado para producción):
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "main:app"]
