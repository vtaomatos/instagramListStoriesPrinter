import os
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "use_pure": True
}

MIGRATIONS_DIR = "./migrations_sql"

# Conecta ao banco
conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# Cria a tabela de controle, se necessário
cursor.execute("""
CREATE TABLE IF NOT EXISTS migrations_sql (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    executed_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# Pega os arquivos ordenados por nome
arquivos = sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql"))

for arquivo in arquivos:
    caminho = os.path.join(MIGRATIONS_DIR, arquivo)

    # Pula se já foi executado
    cursor.execute("SELECT 1 FROM migrations_sql WHERE filename = %s", (arquivo,))
    if cursor.fetchone():
        print(f"⏩ Já executado: {arquivo}")
        continue

    print(f"🚀 Executando: {arquivo}")
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            buffer = ""
            for linha in f:
                linha = linha.strip()

                # Ignora comentários e linhas vazias
                if not linha or linha.startswith("--"):
                    continue

                buffer += linha + " "

                # Quando encontrar ;, é o fim da query
                if ";" in linha:
                    try:
                        cursor.execute(buffer.strip())
                    except Exception as e:
                        print(f"❌ Erro ao executar:\n{buffer.strip()}\n→ {e}")
                        raise
                    buffer = ""

        conn.commit()
        # Marca como executado
        cursor.execute("INSERT INTO migrations_sql (filename) VALUES (%s)", (arquivo,))
        conn.commit()
        print(f"✅ Finalizado: {arquivo}")
    except Exception as e:
        print(f"❌ Erro geral em {arquivo}: {e}")
        conn.rollback()

cursor.close()
conn.close()
