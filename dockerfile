# Base: Python 3.11
FROM python:3.11-slim

# Define diretório de trabalho dentro do container
WORKDIR /usr/src/app

# Copia dependências
COPY requirements.txt ./

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o projeto
COPY . .

# Define variável de ambiente (pode usar seu .env depois)
ENV PYTHONUNBUFFERED=1

# Comando padrão (pode ser sobrescrito pelo docker-compose ou entrypoint)
CMD ["python", "main.py"]
