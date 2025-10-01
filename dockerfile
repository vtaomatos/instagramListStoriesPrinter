# Dockerfile para Instagram List Stories Printer
FROM python:3.11-slim

# Evitar prompts interativos e manter o container limpo
ENV DEBIAN_FRONTEND=noninteractive

# Atualiza e instala dependências do Chromium e libs necessárias
RUN apt-get update && apt-get install -y \
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

# Definir variáveis de ambiente para Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV PIP_NO_CACHE_DIR=1

# Diretório de trabalho
WORKDIR /usr/src/app

# Copiar requirements.txt e instalar dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar todo o código do projeto
COPY . .

# Comando padrão ao iniciar o container
CMD ["python", "pipeline.py"]
