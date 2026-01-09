import os
import shutil
import base64
import json
from dotenv import load_dotenv
from openai import OpenAI
import re
import sys
import ast


sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FLYER_DIR = os.getenv("FLYER_DIR", "./flyer")
LIXO_DIR = os.getenv("LIXO_DIR", "./lixo")
LOTE = int(os.getenv("LOTE", 5))


client = OpenAI(api_key=OPENAI_API_KEY)

def listar_imagens(diretorio):
    extensoes = ('.jpg', '.jpeg', '.png', '.webp')
    imagens = []
    for raiz, _, arquivos in os.walk(diretorio):
        print(raiz,_,arquivos,diretorio)
        for nome in arquivos:
            print(nome, imagens)
            if nome.lower().endswith(extensoes):
                imagens.append(os.path.join(raiz, nome))
    return imagens

def encode_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def enviar_para_chatgpt(imagens):
    mapa, imagens_base64 = construir_mapa_de_imagens(imagens)

    prompt = (
        "Você agora vai ler e descrever eventos muito bem.\n"
        "Você receberá imagens com nomes fictícios como 'story_1', 'story_2' etc.\n"
        "Considere esses nomes ao retornar os resultados.\n\n"
        "Gere **exclusivamente** um JSON **válido** com a seguinte estrutura:\n"
        '{ "data": [ { "imagem": "story_1", "isFlyer": true, "descricao": "..." } ] }\n'
        "⚠️ Use **aspas duplas** em todas as chaves e valores string, conforme o padrão JSON.\n"
        "❌ Não inclua ```json ou nenhum texto fora do JSON.\n"
    )


    mensagens = [
        {"role": "system", "content": "Você é um assistente que analisa imagens de eventos para identificar se são flyers."},
        {"role": "user", "content": [{"type": "text", "text": prompt}] + imagens_base64}
    ]

    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=mensagens,
        max_tokens=1000
    )

    conteudo = resposta.choices[0].message.content.strip()
    try:
        conteudo_limpo = re.sub(r"^```(?:json)?\n|\n```$", "", conteudo.strip())
        dados = json.loads(conteudo_limpo)
        return dados, mapa
    except json.JSONDecodeError:
        try:
            print("⚠️ JSON inválido, tentando com ast.literal_eval...")
            dados = ast.literal_eval(conteudo_limpo)
            return dados, mapa
        except Exception:
            print("❌ Falha total ao interpretar JSON. Conteúdo bruto:")
            print(conteudo)
            return {}, mapa


def mover_arquivo(caminho, destino_base, exec_id):
    nome_instagram = "desconhecido"

    # ✅ Caminho multiplataforma
    caminho_normalizado = os.path.normpath(caminho)
    partes = caminho_normalizado.split(os.sep)

    try:
        idx = partes.index("stories_capturados")
        nome_instagram = partes[idx + 2]
    except (ValueError, IndexError):
        print(f"⚠️ Caminho inesperado: não foi possível extrair o nome da conta de '{caminho}'")

    destino = os.path.join(destino_base, exec_id, nome_instagram)
    os.makedirs(destino, exist_ok=True)

    arquivos_existentes = [
        f for f in os.listdir(destino)
        if f.startswith("story_") and os.path.splitext(f)[1].lower() in [".png", ".jpg", ".jpeg", ".webp"]
    ]

    numeros = []
    for nome in arquivos_existentes:
        try:
            numero = int(nome.split("_")[1].split(".")[0])
            numeros.append(numero)
        except:
            continue

    proximo_numero = max(numeros) + 1 if numeros else 1
    extensao = os.path.splitext(caminho)[1].lower()
    novo_nome = f"story_{proximo_numero}{extensao}"
    destino_path = os.path.join(destino, novo_nome)

    shutil.copy(caminho, destino_path)
    print(f"✅ Arquivo copiado como {novo_nome} para {destino}")
    

def construir_mapa_de_imagens(imagens):
    mapa = {}
    partes = []
    for i, caminho in enumerate(imagens, start=1):
        nome_temp = f"story_{i}"
        base64_img = encode_image_base64(caminho)
        extensao = os.path.splitext(caminho)[1].lower().replace(".", "")
        mapa[nome_temp] = caminho
        partes.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/{extensao};base64,{base64_img}"
            }
        })
    return mapa, partes


def processar_lote(imagens, flyer_dir, lixo_dir):
    resultados, mapa = enviar_para_chatgpt(imagens)
    if not resultados:
        print("❌ Nenhum resultado retornado. Pulando lote.")
        return

    dados = resultados.get("data", [])
    if not dados:
        print("❌ Nenhuma imagem válida retornada no campo 'data'.")
        return

    for r in dados:
        nome_temp = r.get("imagem")
        is_flyer = r.get("isFlyer", False)
        descricao = r.get("descricao", "")
        caminho_original = mapa.get(nome_temp)

        if not caminho_original:
            print(f"⚠️ Nome temporário '{nome_temp}' não encontrado no mapa.")
            continue

        destino = flyer_dir if is_flyer else lixo_dir
        mover_arquivo(caminho_original, destino)
        print(f"{'✅ FLYER' if is_flyer else '🗑️ LIXO'} - {os.path.basename(caminho_original)} | {descricao}")


def main():
    imagens = listar_imagens(ROOT_DIR)
    print(f"🔍 {len(imagens)} imagens encontradas. Processando em lotes de {LOTE}...")

    for i in range(0, len(imagens), LOTE):
        lote = imagens[i:i + LOTE]
        processar_lote(lote, FLYER_DIR, LIXO_DIR)

if __name__ == "__main__":
    main()
