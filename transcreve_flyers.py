import os
import json
import base64
import re
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import time


#TODO:
# - Adicionar mais logs [OK]
# - Adicionar o glossário de artistas e casas de eventos como variavel [OK]
# - Adicionar imagem em base64 no banco; [OK]
# - Ocultar os elementos do story que atrapalham a leitura do flyer;
# - Gravar os objetos JSON retornados em um arquivo separado para análise de duplicados; [OK]
# - Identificar as imagens duplicadas;
# - Identificar os eventos duplicados;
# - Unir as informações de eventos duplicados como informações complementares de um mesmo evento;
# - Criar script para gravar os inserts no banco de dados;
# - Alterar banco de dados para aceitar o campo de imagem em base64; [OK]
# - Alterar o consumo do banco de dados para usar o campo de imagem em base64 ou o caminho do arquivo; [OK]


load_dotenv()

API_KEY = os.getenv("API_KEY_OPENAI")
DIRETORIO_IMAGENS = os.getenv("DIRETORIO_IMAGENS", "./flyer")
ARQUIVO_SAIDA = os.getenv("ARQUIVO_SQL_SAIDA", "inserts_eventos.sql")
ARQUIVO_JSON_SAIDA = os.getenv("ARQUIVO_JSON_SAIDA", "eventos.json")
TAMANHO_LOTE = int(os.getenv("TAMANHO_LOTE", 5))
DIERTORIO_GLOSSARIO = os.getenv("GLOSSARIO", "./glossario.json")
GLOSSARIO = {}

# Carrega o glossário de artistas e casas de eventos
with open(DIERTORIO_GLOSSARIO, "r", encoding="utf-8") as f:
    GLOSSARIO_RAW = json.load(f)

GLOSSARIO_DATA = GLOSSARIO_RAW.get("data", [])

# Busca as listas de palavras certas e erradas
palavras_certas = next((item["conteudo"] for item in GLOSSARIO_DATA if item["id"] == "glossario_palavras_certas"), [])
palavras_erradas = next((item["conteudo"] for item in GLOSSARIO_DATA if item["id"] == "glossario_palavras_erradas"), [])
enderecos_coordenadas = next((item["conteudo"] for item in GLOSSARIO_DATA if item["id"] == "glossario_localizacao"), [])

# Concatenação de strings para inserir no prompt
str_palavras_certas = ", ".join(palavras_certas)
str_palavras_erradas = ", ".join(palavras_erradas)
str_enderecos_coordenadas = "\n".join([
    f"{item['instagram']} => {item['endereco']} (Lat: {item['latitude']}, Lng: {item['longitude']})"
    for item in enderecos_coordenadas
])

print("str_palavras_certas:", str_palavras_certas)
print("str_palavras_erradas:", str_palavras_erradas)
print("str_enderecos_coordenadas:", str_enderecos_coordenadas)

client = OpenAI(api_key=API_KEY)

PROMPT = """
Você receberá imagens extraídas de stories do Instagram de casas de eventos. Elas contêm flyers com informações sobre festas, artistas e programações. Para cada imagem, retorne um objeto JSON com os seguintes campos:
{data: [{id, titulo, data_evento (AAAA-MM-DD HH:MM:SS), tipo_conteudo ("imagem" ou "html"), flyer_html, flyer_imagem ("./flyer/story_N.png"), instagram, linkInstagram, descricao (com gênero musical, promoções, artistas, vibe, horário), endereco (completo e pesquisado), latitude, longitude}]}.
Extraia todas as informações com máxima precisão. Se necessário, pesquise na internet o endereço e Instagram da casa de eventos. A data e hora do evento são obrigatórias. Se for um evento recorrente (por exemplo, toda quarta-feira), gere quatro ocorrências com datas reais futuras, espaçadas semanalmente. Use exatamente o nome do arquivo recebido (como "story_1.png") para preencher o campo flyer_imagem.
No campo descricao, escreva um texto atrativo e informativo com os estilos musicais, nomes de artistas ou DJs, promoções como "open bar", "mulher VIP", horário, clima do evento e o tipo de público. Retorne apenas o JSON solicitado, sem nenhuma informação extra. Se algum dado estiver ilegível ou ausente, retorne o campo como null ou string vazia.
Use este glossário para interpretar nomes comuns de artistas, casas ou apelidos, mesmo que estejam com abreviações ou erros: {palavras certas:""" + str_palavras_certas + """, palavras erradas:""" + str_palavras_erradas + """}.
Glossário de endereços e coordenadas: {enderecos coordenadas:""" + str_enderecos_coordenadas + """}.
Retorne nada além do objeto solicitado. Caso necessário traga informações vazias.
"""

def extrair_numero(nome_arquivo):
    # Tenta extrair número de algo como story_1.png
    try:
        return int(re.search(r"story_(\d+)", nome_arquivo).group(1))
    except:
        return float("inf")  # empurra arquivos sem número pro final


def carregar_imagens_em_lotes(diretorio, tamanho_lote):
    print(f"🔍 Carregando imagens do diretório: {diretorio}")
    imagens = sorted([
        os.path.join(diretorio, f) for f in os.listdir(diretorio)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    ], key=lambda x: extrair_numero(os.path.basename(x)))
    for i in range(0, len(imagens), tamanho_lote):
        yield imagens[i:i + tamanho_lote]
    
    print(f"✅ {len(imagens)} imagens carregadas do diretório {diretorio}.")


def gerar_insert_sql(evento):
    print("🔄 Gerando INSERT SQL para evento:", evento.get("titulo", "Sem título"))
    campos = [
        "titulo", "data_evento", "tipo_conteudo", "flyer_html", "flyer_imagem",
        "instagram", "linkInstagram", "latitude", "longitude", "descricao", "endereco"
    ]
    valores = [evento.get(c, "") for c in campos]
    valores_escapados = []
    for v in valores:
        if isinstance(v, str):
            v_escaped = v.replace("'", "''")  # escape de aspas simples para SQL
            valores_escapados.append(f"'{v_escaped}'")
        elif v is None:
            valores_escapados.append("null")
        else:
            valores_escapados.append(str(v))

    # Adiciona o campo de imagem base64, se existir
    # se a imagem com endereço flyer_imagem existir, gera o base64 e adiciona ao insert
    # if "flyer_imagem" in evento and os.path.exists(evento["flyer_imagem"]):
    #     with open(evento["flyer_imagem"], "rb") as f:
    #         imagem_base64 = base64.b64encode(f.read()).decode("utf-8")

    #     campos.append("imagem_base64")
    #     valores_escapados.append(f"'{imagem_base64}'")

    insert = f"INSERT INTO eventos ({', '.join(campos)}) VALUES ({', '.join(valores_escapados)});"
    print("✅ INSERT gerado:", insert)
    return insert


def salvar_inserts(inserts):
    print("💾 Salvando INSERTs no arquivo:", ARQUIVO_SAIDA)
    timestamp = datetime.now().strftime("-- Inserção em %Y-%m-%d %H:%M:%S --")
    with open(ARQUIVO_SAIDA, "a", encoding="utf-8") as f:
        f.write(f"\n\n{timestamp}\n")
        f.write("\n".join(inserts))
        f.write("\n")
    print(f"✅ {len(inserts)} INSERTs salvos com sucesso.")

def salvar_json_eventos(eventos):
    print("💾 Salvando eventos no arquivo JSON:", ARQUIVO_JSON_SAIDA)
    timestamp = datetime.now().strftime("-- Inserção em %Y-%m-%d %H:%M:%S --")
    with open(ARQUIVO_JSON_SAIDA, "a", encoding="utf-8") as f:
        f.write(f"\n\n{timestamp}\n")
        json.dump({"data": eventos}, f, ensure_ascii=False, indent=4)
        f.write("\n")
    print(f"✅ {len(eventos)} eventos salvos no arquivo JSON com sucesso.")

def processar_lote(imagens_lote):
    print(f"🔄 Processando lote de {len(imagens_lote)} imagens...")
    image_parts = []
    nome_mapa = {}  # Mapeia a ordem para o nome real da imagem

    for idx, img_path in enumerate(imagens_lote):
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        mime_type = "image/png" if img_path.lower().endswith("png") else "image/jpeg"
        image_parts.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{b64}"
            }
        })
        nome_mapa[f"story_{idx + 1}{os.path.splitext(img_path)[1]}"] = os.path.basename(img_path)

    messages = [{"type": "text", "text": PROMPT}] + image_parts

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": messages}],
        max_tokens=2000
    )

    conteudo = response.choices[0].message.content.strip()
    try:
        conteudo_limpo = re.sub(r"^```(?:json)?\n|\n```$", "", conteudo.strip())
        json_data = json.loads(conteudo_limpo)
        eventos = json_data.get("data", [])

        # Substitui o nome do arquivo retornado pelo nome real original
        for evento in eventos:
            nome_flyer = evento.get("flyer_imagem", "")
            basename = os.path.basename(nome_flyer)
            if basename in nome_mapa:
                evento["flyer_imagem"] = f"./flyer/{nome_mapa[basename]}"

        inserts = [gerar_insert_sql(e) for e in eventos]
        print(f"✅ {len(eventos)} eventos processados do lote de {len(imagens_lote)} imagens.")
        return inserts, eventos

    except Exception as e:
        print("❌ Erro ao processar JSON:", e)
        print("Conteúdo retornado:", conteudo)
        print("⚠️ Nenhum evento processado.")
        return []

def main():
    for lote in carregar_imagens_em_lotes(DIRETORIO_IMAGENS, TAMANHO_LOTE):
        inserts, eventos = processar_lote(lote)
        if inserts:
            salvar_json_eventos(eventos)
            salvar_inserts(inserts)
            print(f"✅ {len(inserts)} eventos inseridos do lote de {len(lote)} imagens.")
        else:
            print("⚠️ Nenhum evento encontrado no lote.")

if __name__ == "__main__":
    main()
