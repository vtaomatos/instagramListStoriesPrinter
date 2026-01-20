FROM python:3.12-slim

# Dependências do sistema pro Chrome e utilitários
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libgtk-3-0 \
    libasound2 \
    libxshmfence1 \
    ca-certificates \
    procps \
    --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do robo
COPY . .

# 🔹 Cria diretório de logs (volume-friendly)
RUN mkdir -p /app/logs

# 🔹 Garante permissão de execução dos scripts
RUN chmod +x /app/run_pipeline.sh
RUN chmod +x /app/kill_pipeline.sh

CMD ["python", "pipeline.py"]
