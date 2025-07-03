import os
import shutil
import base64
import json
from dotenv import load_dotenv
from openai import OpenAI
import re

# Carrega variáveis de ambiente
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ROOT_DIR = os.getenv("ROOT_DIR", "./imagens")
FLYER_DIR = os.getenv("FLYER_DIR", "./flyer")
LIXO_DIR = os.getenv("LIXO_DIR", "./lixo")
LOTE = int(os.getenv("LOTE", 5))

client = OpenAI(api_key=OPENAI_API_KEY)

def listar_imagens(diretorio):
    extensoes = ('.jpg', '.jpeg', '.png', '.webp')
    imagens = []
    for raiz, _, arquivos in os.walk(diretorio):
        for nome in arquivos:
            if nome.lower().endswith(extensoes):
                imagens.append(os.path.join(raiz, nome))
    return imagens

def encode_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def enviar_para_chatgpt(imagens):
    prompt = (
        "Você agora vai ler e descrever eventos muito bem.\n"
        "Quero que você receba essa lista de imagens, retiradas de stories de casas de eventos e semelhantes. "
        "Leia essas imagens e determine se a imagem se trata claramente de um flyer de evento, com informações mínimas sobre eventos e programação ou não (se for qualquer outra coisa).\n"
        "Gere um retorno vinculando imagens com um booleano onde true é flyer de divulgação de evento e false não, ponha nesse objeto também uma descrição bem breve do que encontrou na imagem.\n"
        "ex: {data:[{imagem: 'story_1.extensao', isFlyer: true, descricao: '...'}]}\n"
        "O retorno deve ser um JSON válido com a seguinte estrutura:\n"
        "Não retorne nada além disso, apenas o JSON com as informações.\n"
        "Se não encontrar nada, retorne equivalente a null ou vazio no campo que for necessário\n")

    mensagens = [
        {"role": "system", "content": "Você é um assistente que analisa imagens de eventos para identificar se são flyers."},
        {"role": "user", "content": [{"type": "text", "text": prompt}] + [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{encode_image_base64(img)}"
                }
            } for img in imagens
        ]}
    ]

    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=mensagens,
        max_tokens=1000
    )

    conteudo = resposta.choices[0].message.content.strip()

    try:
        conteudo_limpo = re.sub(r"^```(?:json)?\n|\n```$", "", conteudo.strip())
        return json.loads(conteudo_limpo)
    except json.JSONDecodeError:
        print("⚠️ Falha ao interpretar o JSON. Retorno recebido:")
        print(conteudo)
        return []

def mover_arquivo(caminho, destino):
    os.makedirs(destino, exist_ok=True)
    destino_path = os.path.join(destino, os.path.basename(caminho))
    shutil.move(caminho, destino_path)

def processar_lote(imagens, flyer_dir, lixo_dir):
    resultados = enviar_para_chatgpt(imagens)
    if not resultados:
        print("❌ Nenhum resultado retornado. Pulando lote.")
        return

    dados = resultados.get("data", [])
    if not dados:
        print("❌ Nenhuma imagem válida retornada no campo 'data'.")
        return

    for r in dados:
        nome = r.get("imagem")
        is_flyer = r.get("isFlyer", False)
        descricao = r.get("descricao", "")
        caminho_original = next(
            (img for img in imagens if os.path.basename(os.path.normpath(img)).lower() == nome.lower()),
            None
        )

        if not caminho_original:
            print(f"⚠️ Imagem '{nome}' não encontrada no lote.")
            continue

        destino = flyer_dir if is_flyer else lixo_dir
        mover_arquivo(caminho_original, destino)
        print(f"{'✅ FLYER' if is_flyer else '🗑️ LIXO'} - {nome} | {descricao}")

def main():
    imagens = listar_imagens(ROOT_DIR)
    print(f"🔍 {len(imagens)} imagens encontradas. Processando em lotes de {LOTE}...")

    for i in range(0, len(imagens), LOTE):
        lote = imagens[i:i + LOTE]
        processar_lote(lote, FLYER_DIR, LIXO_DIR)

if __name__ == "__main__":
    main()
