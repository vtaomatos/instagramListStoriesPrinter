import os
import mysql.connector
from dotenv import load_dotenv
import sys

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()


def executar_migration(config, exec_id, conta, migrations_dir):
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS migrations_sql (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255) NOT NULL UNIQUE,
            executed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

        caminho_arquivo = os.path.join(migrations_dir, f"{exec_id}_{conta}.sql")

        if not os.path.isfile(caminho_arquivo):
            print(f"⚠️ Arquivo não encontrado: {caminho_arquivo}")
            return False

        nome_arquivo_para_registro = caminho_arquivo.replace("\\", "/")

        cursor.execute(
            "SELECT 1 FROM migrations_sql WHERE filename = %s",
            (nome_arquivo_para_registro,)
        )

        if cursor.fetchone():
            print(f"⏩ Já executado em {config['database']}")
            return True

        print(f"🚀 Executando em {config['database']}")

        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            buffer = ""
            for linha in f:
                linha = linha.strip()

                if not linha or linha.startswith("--"):
                    continue

                buffer += linha + " "

                if ";" in linha:
                    cursor.execute(buffer.strip())
                    buffer = ""

        conn.commit()

        cursor.execute(
            "INSERT INTO migrations_sql (filename) VALUES (%s)",
            (nome_arquivo_para_registro,)
        )
        conn.commit()

        print(f"✅ Finalizado em {config['database']}")
        return True

    except Exception as e:
        print(f"❌ Erro no banco {config.get('database')}: {e}")
        if conn:
            conn.rollback()
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def main(exec_id, conta, migrations_dir="./migrations_sql"):
    config_principal = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "use_pure": True
    }

    config_secundario = {
        "host": os.getenv("DB_HOST_DEV"),
        "user": os.getenv("DB_USER_DEV"),
        "password": os.getenv("DB_PASSWORD_DEV"),
        "database": os.getenv("DB_NAME_DEV"),
        "use_pure": True
    }

    # 1️⃣ Executa no principal
    print("\n=== Executando no banco principal ===")
    sucesso_principal = executar_migration(
        config_principal, exec_id, conta, migrations_dir
    )

    if not sucesso_principal:
        print("🛑 Migration falhou no principal. Secundário não será executado.")
        return False

    # 2️⃣ Só executa no secundário se o principal deu certo
    print("\n=== Executando no banco secundário ===")
    sucesso_secundario = executar_migration(
        config_secundario, exec_id, conta, migrations_dir
    )

    if not sucesso_secundario:
        print("⚠️ Principal executado, mas secundário falhou.")

    return True