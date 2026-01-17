FROM python:3.12-slim

# Dependências do sistema pro Chrome e utilitários
RUN apt-get update && apt-get install -y \
    cron \
    wget \
    unzip \
    chromium \
    chromium-driver \
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
    bash \
    --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

WORKDIR /app

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do robo
COPY . .

# 🔹 Cria diretório de logs (volume-friendly)
RUN mkdir -p /app/logs

# 🔹 Remove CR do Windows e garante permissão de execução de todos os scripts .sh
RUN find /app -name "*.sh" -exec sed -i 's/\r$//' {} \; -exec chmod +x {} \;

# Copia crontab para dentro do container
COPY crontab /etc/cron.d/robo-cron
RUN chmod 0644 /etc/cron.d/robo-cron && crontab /etc/cron.d/robo-cron

# Comando para rodar cron em foreground
CMD ["cron", "-f"]
