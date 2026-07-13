FROM nikolaik/python-nodejs:python3.11-nodejs20-slim

WORKDIR /app

# Instalar dependencias del sistema y de Python
RUN apt-get update && apt-get install -y make g++ python3 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
RUN pip install --no-cache-dir build && pip install -e .

# Instalar dependencias de Node
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# Copiar el resto del código
COPY . .

# Exponer el puerto (asumiendo que server.js usa el puerto 3000 por defecto)
EXPOSE 3000

# Comando de ignición por defecto
CMD ["node", "server.js"]
