# Usa una imagen ligera de Python
FROM python:3.11-slim

# Crea un directorio de trabajo
WORKDIR /app

# Copia requirements.txt primero para instalar dependencias
COPY requirements.txt .

# Instala dependencias sin caché
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código al contenedor
COPY . .

# Variable de entorno para el puerto
ENV PORT=8000

# Comando que Render ejecutará para levantar FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

