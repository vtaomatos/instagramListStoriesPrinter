import requests
import time
import os
import sys
import mysql.connector

from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

# =========================================================
# CONFIG
# =========================================================

GOOGLE_API_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"

DELAY_ENTRE_REQUISICOES = 0.3

# =========================================================
# INIT
# =========================================================

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# =========================================================
# MYSQL
# =========================================================

conn = mysql.connector.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

cursor = conn.cursor(dictionary=True)

# =========================================================
# GOOGLE PLACES
# =========================================================

def buscar_info_por_nome(nome_local):
    try:
        response = requests.get(
            GOOGLE_API_URL,
            params={
                "input": nome_local,
                "inputtype": "textquery",
                "fields": "name,formatted_address,geometry",
                "key": GOOGLE_API_KEY
            }
        )

        data = response.json()

        if not data.get("candidates"):
            return None

        candidato = data["candidates"][0]

        return {
            "nome": candidato.get("name", nome_local),
            "endereco": candidato["formatted_address"],
            "latitude": candidato["geometry"]["location"]["lat"],
            "longitude": candidato["geometry"]["location"]["lng"]
        }

    except Exception as e:
        print(f"⚠️ Erro ao buscar {nome_local}: {e}")
        return None


# =========================================================
# BANCO
# =========================================================

def carregar_locais_pendentes():

    query = """
        SELECT
            Id,
            Instagram
        FROM local
        WHERE
            Instagram IS NOT NULL
            AND Instagram <> ''
            AND (
                Endereco IS NULL
                OR Endereco = ''
                OR Latitude IS NULL
                OR Longitude IS NULL
            )
        ORDER BY Id
    """

    cursor.execute(query)

    return cursor.fetchall()


def atualizar_localizacao(
    local_id,
    nome,
    endereco,
    latitude,
    longitude
):

    query = """
        UPDATE local
        SET
            Nome = %s,
            Endereco = %s,
            Latitude = %s,
            Longitude = %s,
            UpdatedAt = NOW()
        WHERE Id = %s
    """

    values = (
        nome,
        endereco,
        latitude,
        longitude,
        local_id
    )

    cursor.execute(query, values)


def inserir_palavra_glossario(palavra):
    query_verifica = """
        SELECT Id
        FROM GlossarioPalavra
        WHERE Palavra = %s
        LIMIT 1
    """

    cursor.execute(query_verifica, (palavra,))

    if cursor.fetchone():
        return

    query_insert = """
        INSERT INTO GlossarioPalavra
        (
            Palavra,
            PalavraCorretaId
        )
        VALUES
        (
            %s,
            NULL
        )
    """

    cursor.execute(query_insert, (palavra,))

# =========================================================
# MAIN
# =========================================================

def main():

    locais_pendentes = carregar_locais_pendentes()

    print(f"📦 {len(locais_pendentes)} locais pendentes.")

    for local in locais_pendentes:

        instagram = local["Instagram"]
        local_id = local["Id"]

        print(f"\n🔍 Buscando @{instagram}...")

        info = buscar_info_por_nome(instagram)

        if not info:
            print(f"❌ Não encontrado.")
            continue

        try:

            atualizar_localizacao(
                local_id=local_id,
                nome=info["nome"],
                endereco=info["endereco"],
                latitude=info["latitude"],
                longitude=info["longitude"]
            )

            inserir_palavra_glossario(instagram)

            conn.commit()

            print("✅ Atualizado com sucesso.")

        except Exception as e:

            conn.rollback()

            print(f"❌ Erro: {e}")

        time.sleep(DELAY_ENTRE_REQUISICOES)
# =========================================================

if __name__ == "__main__":
    main()