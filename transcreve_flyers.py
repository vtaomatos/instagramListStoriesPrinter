import os
import json
import base64
import re
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import sys
from collections import defaultdict
import unicodedata
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")

sys.stdout.reconfigure(encoding='utf-8')


#TODO:
# - Adicionar mais logs [OK]
# - Adicionar o glossário de artistas e casas de eventos como variavel [OK]
# - Adicionar imagem em base64 no banco; [OK]
# - Ocultar os elementos do story que atrapalham a leitura do flyer; [OK]
# - Gravar os objetos JSON retornados em um arquivo separado para análise de duplicados; [OK]
# - Identificar as imagens duplicadas; [Evitar duplicação de imagens a partir de horario de postagem x captura dos stories da conta] [OK]
# - Identificar os eventos duplicados;
# - Unir as informações de eventos duplicados como informações complementares de um mesmo evento;
# - Criar script para gravar os inserts no banco de dados; [OK]
# - Alterar banco de dados para aceitar o campo de imagem em base64; [OK]
# - Alterar o consumo do banco de dados para usar o campo de imagem em base64 ou o caminho do arquivo; [OK]
# - Migrar o PHP de servidor; [OK]

load_dotenv()

API_KEY = os.getenv("API_KEY_OPENAI")
DIRETORIO_IMAGENS = os.getenv("ROOT_DIR", "./stories_capturados")
ARQUIVO_SAIDA = os.getenv("ARQUIVO_SQL_SAIDA", "inserts_eventos.sql")
ARQUIVO_JSON_SAIDA = os.getenv("ARQUIVO_JSON_SAIDA", "eventos.json")
TAMANHO_LOTE = int(os.getenv("TAMANHO_LOTE", 5))
DIERTORIO_GLOSSARIO = os.getenv("GLOSSARIO", "./glossario.json")
DIR_MIGRATIONS_SQL = os.getenv("DIR_MIGRATIONS_SQL", "./migrations_sql")

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
str_enderecos_coordenadas_default = " \n ".join([
    f"{item['instagram']} => {item['endereco']} (Lat: {item['latitude']}, Lng: {item['longitude']})"
    for item in enderecos_coordenadas
])

print("str_palavras_certas:", str_palavras_certas)
print("str_palavras_erradas:", str_palavras_erradas)
print("str_enderecos_coordenadas:", str_enderecos_coordenadas_default)

client = OpenAI(api_key=API_KEY)


def gerar_prompt(str_palavras_certas, str_palavras_erradas, str_enderecos_coordenadas):
    prompt = """
    Você receberá imagens extraídas de stories do Instagram de casas de eventos. Elas contêm ou não flyers com informações sobre festas, artistas e programações que normalmente são postados semanalmente. Para cada evento, retorne um objeto JSON com os seguintes campos:
    {data: [{id, titulo, data_evento ((talvez ano atual)AAAA-(talvez mês atual)MM-DD HH:MM:SS), data_fim_evento ((talvez ano atual)AAAA-(talvez mês atual)MM-DD HH:MM:SS, tipo_conteudo ("imagem" ou "html"), flyer_html, flyer_imagem ("./flyer/story_N.png"), instagram, linkInstagram (geralmente https://www.instagram.com/{instagram}/), descricao (com gênero musical, promoções, artistas, vibe, horário), endereco (completo e pesquisado), latitude, longitude, categoria (enum:'MUSICA','FESTA','SHOW','BAR','BALADA','ARTE','CULTURA','RELIGIOSO','GEEK','EDUCACAO','WORKSHOP','PALESTRA','ATIVIDADE FISICA','ESPORTE','OUTROS','NAO IDENTIFICADO'), tags(objeto JSON contendo apenas listas ou valores curtos, sem frases, sem texto corrido, com palavras normalizadas (lowercase, sem acento), seguindo este padrão: tipo_evento (ex: baile, show, festa, workshop), estilos (ex: black, rnb, funk, eletronica), publico (ex: 18+, livre), periodo (ex: noturno, diurno), dias (ex: sexta, sabado), caracteristicas (ex: open bar, gratuito, ao vivo), cidade, bairro, artistas (nomes próprios), recorrente (true ou false)}]}.
    Extraia todas as informações com máxima precisão. Se necessário, pesquise na internet o endereço e Instagram do evento ou casa do evento. A data e hora do evento são obrigatórias. Se for um evento recorrente (por exemplo, toda quarta-feira, todo sabado, etc), gere quatro ocorrências com datas reais futuras, espaçadas semanalmente. Use exatamente o nome do arquivo recebido (como "story_1.png") para preencher o campo flyer_imagem.
    No campo descricao, escreva um texto atrativo e informativo com os estilos musicais, nomes de artistas ou DJs, promoções como "open bar", "mulher VIP", horário, clima do evento e o tipo de público. Retorne apenas o JSON solicitado, sem nenhuma informação extra. Se algum dado estiver ilegível ou ausente, retorne o campo como null ou string vazia.
    Use este glossário para interpretar nomes comuns de artistas, casas ou apelidos, mesmo que estejam com abreviações ou erros: {palavras certas:""" + str_palavras_certas + """, palavras erradas:""" + str_palavras_erradas + """}.
    Glossário de instagram correto, endereços e coordenadas: {enderecos coordenadas:""" + str_enderecos_coordenadas + """}.
    Para melhor precisão nas datas, saiba que o horario agora é: """ + datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S") + """ e que você usar a hora em que foi postado o story caso queira calcular imagens que contenham o texto "hoje", "amanhã" ou algo assim. Entender eventos que foram ontem.
    Os campos de titulo e data_evento são obrigatórios, se possível.
    Retorne nada além de um json válido solicitado. Caso necessário traga informações vazias.
    """
    print("Prompt gerado:", prompt)
    return prompt

def extrair_numero(nome_arquivo):
    # Tenta extrair número de algo como story_1.png
    try:
        return int(re.search(r"story_(\d+)", nome_arquivo).group(1))
    except:
        return float("inf")  # empurra arquivos sem número pro final

    datas_transcritas = []
    if os.path.exists("migrations_sql"):
        for nome in os.listdir("migrations_sql"):
            if nome.endswith(".sql"):
                try:
                    data_str = nome.split("_inserts")[0]  # Ex: 20250714_081606
                    data_dt = datetime.strptime(data_str, "%Y%m%d_%H%M%S")
                    datas_transcritas.append(data_dt)
                except Exception as e:
                    print(f"⚠️ Ignorando nome de arquivo malformado: {nome} - Erro: {e}")
    else:
        print("⚠️ Pasta 'migrations_sql' não encontrada. Considerando todas as execuções.")

    data_mais_recente_sql = max(datas_transcritas) if datas_transcritas else datetime.min
    print(f"📅 Data mais recente de transcrição: {data_mais_recente_sql}")
    return data_mais_recente_sql

import os

def filtrar_imagens_validas(diretorio_base, exec_id, conta):
    imagens_por_conta = {}

    caminho_conta = os.path.join(diretorio_base, exec_id, conta)
    if not os.path.isdir(caminho_conta):
        print(f"Não é um diretório: {caminho_conta}")
        return False

    imagens = []
    for nome in os.listdir(caminho_conta):
        if nome.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            caminho_imagem = os.path.join(caminho_conta, nome)
            imagens.append(caminho_imagem)

    imagens_ordenadas = sorted(imagens, key=lambda x: extrair_numero(os.path.basename(x)))
    if imagens_ordenadas:
        if conta not in imagens_por_conta:
            imagens_por_conta[conta] = []
        imagens_por_conta[conta].extend(imagens_ordenadas)

    total = sum(len(v) for v in imagens_por_conta.values())
    print(f"✅ {total} imagens encontradas após filtro por data.")
    return imagens_por_conta


def dividir_em_lotes(lista, tamanho_lote):
    for i in range(0, len(lista), tamanho_lote):
        yield lista[i:i + tamanho_lote]

# def gerar_insert_sql(evento):
#     print("🔄 Gerando INSERT SQL para evento:", evento.get("titulo", "Sem título"))
#     campos = [
#         "titulo", "data_evento", "tipo_conteudo", "flyer_html", "flyer_imagem",
#         "instagram", "linkInstagram", "latitude", "longitude", "descricao", "endereco"
#     ]
#     valores = [evento.get(c, "") for c in campos]
#     valores_escapados = []
#     for v in valores:
#         if isinstance(v, str):
#             v_escaped = v.replace("'", "''")  # escape de aspas simples para SQL
#             valores_escapados.append(f"'{v_escaped}'")
#         elif v is None:
#             valores_escapados.append("null")
#         else:
#             valores_escapados.append(str(v))

#     # Adiciona o campo de imagem base64, se existir
#     # se a imagem com endereço flyer_imagem existir, gera o base64 e adiciona ao insert
#     if "flyer_imagem" in evento and os.path.exists(evento["flyer_imagem"]):
#         with open(evento["flyer_imagem"], "rb") as f:
#             imagem_base64 = base64.b64encode(f.read()).decode("utf-8")

#         campos.append("imagem_base64")
#         valores_escapados.append(f"'{imagem_base64}'")

#     insert = f"INSERT INTO eventos ({', '.join(campos)}) VALUES ({', '.join(valores_escapados)});"
#     # print("✅ INSERT gerado:", insert)
#     return insert

def salvar_inserts(inserts, data, slug="inserts_eventos"):
    nome_arquivo = f"{DIR_MIGRATIONS_SQL}/{data}_{slug}.sql"

    # Garante que a pasta exista
    os.makedirs(os.path.dirname(nome_arquivo), exist_ok=True)

    print(f"💾 Salvando INSERTs no arquivo: {nome_arquivo}")

    # Timestamp interno no conteúdo (opcional)
    timestamp = datetime.now(TZ).strftime("-- Inserção em %Y-%m-%d %H:%M:%S --")

    with open(nome_arquivo, "a", encoding="utf-8") as f:
        f.write(f"{timestamp}\n")
        f.write("\n".join(inserts))
        f.write("\n")

    print(f"✅ {len(inserts)} INSERTs salvos com sucesso em {nome_arquivo}")

def salvar_json_eventos(eventos, data, slug="eventos"):
    nome_arquivo = f"eventos_json/{data}_{slug}.json"
    os.makedirs(os.path.dirname(nome_arquivo), exist_ok=True)

    eventos_existentes = []

    # Se o arquivo já existir, carrega os eventos existentes
    if os.path.exists(nome_arquivo):
        try:
            with open(nome_arquivo, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
                eventos_existentes = conteudo.get("data", [])
        except Exception as e:
            print(f"⚠️ Erro ao ler JSON existente: {e}. Continuando com lista vazia.")

    # Junta os eventos novos com os antigos (você pode adaptar para evitar duplicados se quiser)
    todos_eventos = eventos_existentes + eventos

    print("💾 Salvando eventos no arquivo JSON:", nome_arquivo)
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump({"data": todos_eventos}, f, ensure_ascii=False, indent=4)
    print(f"✅ {len(eventos)} novos eventos adicionados. Total: {len(todos_eventos)}")

def gerar_eventos_a_partir_de_imagens(imagens_lote):
    print(f"🔄 Gerando eventos a partir de {len(imagens_lote)} imagens...")

    image_parts = []
    nome_mapa = {}
    instagrams_lote = set()

    for img_path in imagens_lote:
        partes = os.path.normpath(img_path).split(os.sep)
        if len(partes) >= 3:
            instagram = partes[-2]
            instagrams_lote.add(instagram.lower())

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
        nome_mapa[f"story_{idx + 1}{os.path.splitext(img_path)[1]}"] = img_path

    # Filtra o glossário com base nos instagrams presentes no lote
    enderecos_filtrados = [
        item for item in enderecos_coordenadas
        if item["instagram"].lower() in instagrams_lote
    ]

    str_enderecos_coordenadas = " \n ".join([
        f"(instagram: {item['instagram']}, endereco: {item['endereco']}, Lat: {item['latitude']}, Lng: {item['longitude']})"
        for item in enderecos_filtrados
    ])

    messages = [{"type": "text", "text": gerar_prompt(str_palavras_certas, str_palavras_erradas, str_enderecos_coordenadas)}] + image_parts

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

        # Substitui nomes de arquivos retornados
        for evento in eventos:
            nome_flyer = evento.get("flyer_imagem", "")
            basename = os.path.basename(nome_flyer)
            if basename in nome_mapa:
                evento["flyer_imagem"] = nome_mapa[basename]

        return eventos

    except Exception as e:
        print("❌ Erro ao gerar eventos:", e)
        print("Conteúdo retornado:", conteudo)
        return []

def agrupar_eventos_por_instagram(eventos):
    agrupados = defaultdict(list)
    for evento in eventos:
        insta = evento.get("instagram", "").lower()
        if insta:
            agrupados[insta].append(evento)
    return agrupados

def filtrar_eventos_para_melhorar(eventos):
    eventos_filtrados = []
    for evento in eventos:
        falta_data = not evento.get("data_evento")
        falta_local = not (evento.get("endereco") or (evento.get("latitude") and evento.get("longitude")))
        if falta_data or falta_local:
            eventos_filtrados.append(evento)
    return eventos_filtrados

def agrupar_possiveis_duplicados(eventos):
    grupos = defaultdict(list)
    for evento in eventos:
        chave = (evento.get("data_evento", ""), evento.get("endereco", ""))
        grupos[chave].append(evento)
    return [g for g in grupos.values() if len(g) > 1]

def gerar_prompt_unificacao(eventos_problema, demais_eventos_da_conta):
    prompt = """
Unifique os eventos duplicados, e complete as informações faltantes de forma coerente se possível.
Considere os seguintes eventos problemáticos: {eventos_problema}
Dentre os seguintes eventos da mesma conta: {demais_eventos_da_conta}
Responda apenas com um JSON válido: {"data": [todos os eventos]}.
Nada além do JSON.
"""
    return prompt

def solicitar_unificacao_ao_gpt(eventos_problema, demais_eventos_da_conta):
    prompt_text = gerar_prompt_unificacao(eventos_problema, demais_eventos_da_conta)

    # Monta os blocos de conteúdo (text + imagens)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text}
            ]
        }
    ]

    # Adiciona os blocos de imagem ao conteúdo da mensagem
    for evento in eventos_problema:
        img_path = evento.get("flyer_imagem")
        if img_path and os.path.exists(img_path):
            with open(img_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            mime_type = "image/png" if img_path.lower().endswith("png") else "image/jpeg"
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{b64}"
                }
            })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=3000
        )
        conteudo = response.choices[0].message.content
        print("📤 Resposta bruta do GPT:")
        print(conteudo)  # <-- AJUDA A ENCONTRAR O ERRO EXATO

        conteudo_limpo = re.sub(r"^```(?:json)?\n|\n```$", "", conteudo.strip())
        dados = json.loads(conteudo_limpo)

        return dados.get("data", [])
    except Exception as e:
        print("❌ Erro ao interpretar resposta do GPT:", e)
        print("⚠️ Falha ao processar os eventos com base64. Verifique se os arquivos existem.")
        return []

def preparar_eventos_para_insert(eventos):
    for evento in eventos:
        # Preenche instagram e linkInstagram
        if "flyer_imagem" in evento:
            caminho = evento["flyer_imagem"]
            partes = os.path.normpath(caminho).split(os.sep)
            if len(partes) >= 3:
                evento["instagram"] = partes[-2]
                evento["linkInstagram"] = f"https://www.instagram.com/{evento['instagram']}/"

            #Garante que o caminho da imagem seja salvo com a pasta na raiz
            if caminho.startswith("."):
                caminho = caminho[1:]
            evento["flyer_imagem"] = caminho


        # Enriquecer com coordenadas se faltarem
        instagram_evento = evento.get("instagram", "").lower()
        if instagram_evento:
            coord = next((item for item in enderecos_coordenadas if item["instagram"].lower() == instagram_evento), None)
            if coord:
                if not evento.get("latitude"):
                    evento["latitude"] = coord.get("latitude")
                if not evento.get("longitude"):
                    evento["longitude"] = coord.get("longitude")
                if not evento.get("endereco"):
                    evento["endereco"] = coord.get("endereco")

    inserts = [gerar_insert_sql(e) for e in eventos]
    return inserts

def normalizar(texto):
    if not texto:
        return ""

    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def gerar_search_index(evento):
    partes = []

    for campo in ["titulo", "descricao", "categoria", "endereco"]:
        if evento.get(campo):
            partes.append(evento[campo])

    tags = evento.get("tags")
    if not isinstance(tags, dict):
        tags = {}

    if isinstance(tags, dict):
        def extrair(v):
            if isinstance(v, dict):
                for x in v.values():
                    extrair(x)
            elif isinstance(v, list):
                for x in v:
                    extrair(x)
            elif isinstance(v, str):
                partes.append(v)

        extrair(tags)

    return normalizar(" ".join(sorted(set(partes))))

def gerar_insert_sql(evento):
    print("🔄 Gerando INSERT SQL para evento:", evento.get("titulo", "Sem título"))

    CATEGORIAS_VALIDAS = {
        'MUSICA','FESTA','SHOW','BAR','BALADA','ARTE','CULTURA','RELIGIOSO','GEEK','EDUCACAO','WORKSHOP','PALESTRA','ATIVIDADE FISICA','ESPORTE','OUTROS','NAO IDENTIFICADO'
    }

    if evento.get("categoria") not in CATEGORIAS_VALIDAS:
        evento["categoria"] = "NAO IDENTIFICADO"


    # Gera índice semântico
    search_index = gerar_search_index(evento)

    campos = [
        "titulo",
        "data_evento",
        "data_fim_evento",
        "tipo_conteudo",
        "flyer_html",
        "flyer_imagem",
        "instagram",
        "linkInstagram",
        "latitude",
        "longitude",
        "descricao",
        "endereco",
        "categoria",
        "tags",
        "search_index"
    ]

    valores_escapados = []

    for campo in campos:
        valor = evento.get(campo)

        # Campo JSON (tags)
        if campo == "tags":
            if valor is None:
                valores_escapados.append("null")
            else:
                json_str = json.dumps(valor, ensure_ascii=False)
                json_str = json_str.replace("'", "''")
                valores_escapados.append(f"'{json_str}'")

        # Campo search_index
        elif campo == "search_index":
            valores_escapados.append(f"'{search_index}'")            

        # Strings
        elif isinstance(valor, str):
            v = valor.replace("'", "''")
            valores_escapados.append(f"'{v}'")

        # Nulos
        elif valor is None:
            valores_escapados.append("null")

        # Datas, números etc
        else:
            valores_escapados.append(str(valor))

    

    # Imagem base64 opcional
    if evento.get("flyer_imagem") and os.path.exists("./" + evento["flyer_imagem"]):
        with open("./" + evento["flyer_imagem"], "rb") as f:
            imagem_base64 = base64.b64encode(f.read()).decode("utf-8")

        campos.append("imagem_base64")
        valores_escapados.append(f"'{imagem_base64}'")
    else:
        print(f"⚠️ Imagem para base64 não encontrada: {evento.get('flyer_imagem')}")


    insert = f"""
    INSERT INTO eventos ({', '.join(campos)})
    VALUES ({', '.join(valores_escapados)});
    """.strip()

    return insert


def main(exec_id, conta_desejada):
    imagens_por_conta = filtrar_imagens_validas(DIRETORIO_IMAGENS, exec_id, conta_desejada)
    data_execucao = exec_id
    todos_eventos = []

    if not imagens_por_conta:
        print(f"Nenhuma imagem a conta: {conta_desejada}")
        return False

    imagens = imagens_por_conta.get(conta_desejada)

    if not imagens:
        print(f"Nenhuma imagem encontrada para a conta: {conta_desejada}")
        return False

    print(f"\n📦 Processando conta: {conta_desejada} ({len(imagens)} imagens)")

    for lote in dividir_em_lotes(imagens, TAMANHO_LOTE):
        eventos = gerar_eventos_a_partir_de_imagens(lote)

        if eventos:
            todos_eventos.extend(eventos)
        else:
            print("⚠️ Nenhum evento encontrado no lote.")

    print(f"\n📊 Total de eventos brutos encontrados: {len(todos_eventos)}")

    eventos_final = todos_eventos

    print(f"\n📊 Total de eventos: {len(eventos_final)}")

    if eventos_final:
        inserts = preparar_eventos_para_insert(eventos_final)
        salvar_inserts(inserts, data_execucao, conta_desejada)
        print(f"✅ {len(inserts)} INSERTs salvos no total.")
    else:
        print("⚠️ Nenhum evento final encontrado para salvar.")
        return False
    
    return True

if __name__ == "__main__":
    main()
