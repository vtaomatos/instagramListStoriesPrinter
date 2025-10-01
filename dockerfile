# Base: Python 3.11
FROM python:3.11-slim

# Define diretório de trabalho dentro do container
WORKDIR /usr/src/app

# Instala gcc e bibliotecas do PostgreSQL
RUN apt-get update && apt-get install -y gcc libpq-dev

# Copia dependências
COPY requirements.txt ./

# antes do pip install -r requirements.txt
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
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
    && rm -rf /var/lib/apt/lists/*

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o projeto
COPY . .

# Define variável de ambiente (pode usar seu .env depois)
ENV PYTHONUNBUFFERED=1

# Comando padrão (pode ser sobrescrito pelo docker-compose ou entrypoint)
CMD ["python", "pipeline.py"]
