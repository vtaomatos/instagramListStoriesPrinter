# Dockerfile para Instagram List Stories Printer
FROM python:3.11-slim

# Evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive

# Diretório de trabalho
WORKDIR /usr/src/app

# Instalar dependências de sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    chromium \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgbm1 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libxinerama1 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libdrm2 \
    curl \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Variáveis de ambiente para Selenium/Chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_PATH=/usr/bin/chromium
ENV PIP_NO_CACHE_DIR=1

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
# Usar psycopg2-binary no requirements.txt para evitar erros de compilação
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar todo o código do projeto
COPY . .

# Comando padrão ao iniciar o container
CMD ["python", "pipeline.py"]
