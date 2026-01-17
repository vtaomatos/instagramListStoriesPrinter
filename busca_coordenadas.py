import requests
import json
import time
import os
from dotenv import load_dotenv
import sys

sys.stdout.reconfigure(encoding='utf-8')

# === Config ===
ARQUIVO_LOCAIS = "novos_lugares.txt"
ARQUIVO_GLOSSARIO = "glossario.json"
GOOGLE_API_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
CIDADE_PADRAO = "Santos SP"  # Pode alterar aqui
DELAY_ENTRE_REQUISICOES = 0.3

# === Inicialização ===
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def buscar_info_por_nome(nome_local):
    """Consulta a API do Google Places"""
    try:
        response = requests.get(GOOGLE_API_URL, params={
            "input": nome_local,
            "inputtype": "textquery",
            "fields": "formatted_address,geometry",
            "key": GOOGLE_API_KEY
        })
        data = response.json()
        if not data.get("candidates"):
            return None

        candidato = data["candidates"][0]
        return {
            "endereco": candidato["formatted_address"],
            "latitude": candidato["geometry"]["location"]["lat"],
            "longitude": candidato["geometry"]["location"]["lng"]
        }
    except Exception as e:
        print(f"⚠️ Erro ao buscar {nome_local}: {e}")
        return None

def carregar_lista_instagrams():
    with open(ARQUIVO_LOCAIS, "r", encoding="utf-8") as f:
        return [linha.strip().lstrip("@") for linha in f if linha.strip()]

def salvar_lista_nao_encontrados(nao_encontrados):
    with open(ARQUIVO_LOCAIS, "w", encoding="utf-8") as f:
        for item in nao_encontrados:
            f.write(item + "\n")

def atualizar_glossario(locais_validos):
    with open(ARQUIVO_GLOSSARIO, "r", encoding="utf-8") as f:
        glossario = json.load(f)

    for item in glossario["data"]:
        if item["id"] == "glossario_localizacao":
            item["conteudo"].extend(locais_validos)
            break

    with open(ARQUIVO_GLOSSARIO, "w", encoding="utf-8") as f:
        json.dump(glossario, f, ensure_ascii=False, indent=2)

def main():
    instagrams = carregar_lista_instagrams()
    encontrados = []
    nao_encontrados = []

    for nome in instagrams:
        print(f"🔍 Buscando localização de @{nome}...")
        termo_busca = f"{nome}"
        info = buscar_info_por_nome(termo_busca)

        if info:
            print(f"✅ Encontrado: {info['endereco']}")
            encontrados.append({
                "instagram": nome,
                "endereco": info["endereco"],
                "latitude": info["latitude"],
                "longitude": info["longitude"]
            })
        else:
            print(f"❌ Não encontrado: {nome}")
            nao_encontrados.append(nome)

        time.sleep(DELAY_ENTRE_REQUISICOES)

    if encontrados:
        print(f"\n📥 Adicionando {len(encontrados)} localizações no glossário...")
        atualizar_glossario(encontrados)
    else:
        print("\n⚠️ Nenhuma nova localização encontrada.")

    print(f"\n📤 Salvando {len(nao_encontrados)} itens não encontrados em {ARQUIVO_LOCAIS}...")
    salvar_lista_nao_encontrados(nao_encontrados)

if __name__ == "__main__":
    main()
