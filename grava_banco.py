import os
import mysql.connector
from dotenv import load_dotenv
import sys

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

def main(exec_id, conta, migrations_dir="./migrations_sql"):
    config = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "use_pure": True
    }

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

    # Caminho do arquivo específico da conta dentro do exec_id
    caminho_arquivo = os.path.join(migrations_dir, f"{exec_id}_{conta}.sql")

    if not os.path.isfile(caminho_arquivo):
        print(f"⚠️ Arquivo não encontrado: {caminho_arquivo}")
        return False

    # Verifica se já foi executado
    if os.name == "nt":
        nome_arquivo_para_registro = caminho_arquivo.replace("\\", "/")
    else:
        nome_arquivo_para_registro = caminho_arquivo

    cursor.execute("SELECT 1 FROM migrations_sql WHERE filename = %s", (nome_arquivo_para_registro,))
    if cursor.fetchone():
        print(f"⏩ Já executado: {caminho_arquivo}")
        return False

    print(f"🚀 Executando: {caminho_arquivo}")
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
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
        cursor.execute("INSERT INTO migrations_sql (filename) VALUES (%s)", (nome_arquivo_para_registro,))
        conn.commit()
        print(f"✅ Finalizado: {caminho_arquivo}")
        return True
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
