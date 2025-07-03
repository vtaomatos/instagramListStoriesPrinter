import os
import json
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv
import base64
import re


# Carrega variáveis do .env
load_dotenv()

# Variáveis do .env
API_KEY = os.getenv("API_KEY_OPENAI")
DIRETORIO_IMAGENS = os.getenv("DIRETORIO_IMAGENS", "./flyer")
ARQUIVO_SAIDA = os.getenv("ARQUIVO_SQL_SAIDA", "inserts_eventos.sql")
TAMANHO_LOTE = int(os.getenv("TAMANHO_LOTE", 5))

# Inicializa API
client = OpenAI(api_key=API_KEY)

PROMPT = """
Você agora vai ler e descrever eventos muito bem.
Quero que você receba essa lista de imagens, retiradas de stories de casas de eventos e semelhantes.
Leia essas imagens que provavelmente serão flyers de eventos.
Gere um objeto com uma lista de objetos json com as seguintes informações de cada evento a partir das imagens. Ex. {data:[{ id: 1, titulo: o nome da programação, data_evento: AAAA-MM-DD HH-II-SS, tipo_conteudo: "html" ou "imagem", flyer_html: pagina <html> para o evento, flyer_imagem: ./flyer/"story_...".png, instagram: o @ do lugar, geralmente o perfil que está na imagem., linkInstagram: link do perfil da casa no instagram, descricao: "descrição bem feita sobre o evento para que posteriormente as pessoas possam encontrar o que procuram. Tente colocar aqui informações de estilo de musica e banda, descontos e promoçoes, datas e horarios, se possivel a descrever o clima do lugar e dos artistas.", endereco:"endereço bem pesquisado da casa.", latitude: coordenada exata do endereço bem pesquisado da casa, longitude: coordenada exata do endereço do endereço bem pesquisado da casa}]}.
Observações importantes:
Seja preciso na leitura dos eventos, caso necessário busque informações de endereço da casa na internet, também pegar as coordenadas corretas sempre que possível. Nomes de artistas locais na região ou instagram se necessário ou possível.
Coloque a data do evento. Caso seja um evento que se repete crie 4 eventos calculando as datas.
Vou colocar aqui um glossário de palavras que podem ajudar na interpretação do nome de artistas, casas, estilos musicas e outros termos que podem aparecer escritos parcial, incorreta ou incompreensivelmente.
Trindah, Gabriel Antero, Cantor Ph, Meu Lugar, Renanzinho 77, Só resenha, Mulher vip, Leozinho, Dj Babu, Ex é Ex.
Retorne nada além do objeto solicitado. Caso necessário traga informações vazias.
"""

def carregar_imagens_em_lotes(diretorio, tamanho_lote):
    imagens = sorted([os.path.join(diretorio, f) for f in os.listdir(diretorio)
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
    for i in range(0, len(imagens), tamanho_lote):
        yield imagens[i:i + tamanho_lote]

def gerar_insert_sql(evento):
    campos = [
        "titulo", "data_evento", "tipo_conteudo", "flyer_html", "flyer_imagem",
        "instagram", "linkInstagram", "latitude", "longitude", "descricao", "endereco"
    ]
    valores = [evento.get(c, "") for c in campos]
    valores_escapados = [
        f"'{str(v).replace('\'', '\'\'')}'" if isinstance(v, str) else str(v or 'null') for v in valores
    ]
    return f"INSERT INTO eventos ({', '.join(campos)}) VALUES ({', '.join(valores_escapados)});"

def salvar_inserts(inserts):
    timestamp = datetime.now().strftime("-- Inserção em %Y-%m-%d %H:%M:%S --")
    with open(ARQUIVO_SAIDA, "a", encoding="utf-8") as f:
        f.write(f"\n\n{timestamp}\n")
        f.write("\n".join(inserts))
        f.write("\n")

def processar_lote(imagens_lote):
    image_parts = []
    for img in imagens_lote:
        with open(img, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
            mime_type = "image/png" if img.lower().endswith("png") else "image/jpeg"
            image_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{b64}"
                }
            })

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
        return [gerar_insert_sql(e) for e in eventos]
    except Exception as e:
        print("❌ Erro ao processar JSON:", e)
        print("Conteúdo retornado:", conteudo)
        return []
    
def main():
    for lote in carregar_imagens_em_lotes(DIRETORIO_IMAGENS, TAMANHO_LOTE):
        inserts = processar_lote(lote)
        if inserts:
            salvar_inserts(inserts)
            print(f"✅ {len(inserts)} eventos inseridos do lote de {len(lote)} imagens.")
        else:
            print("⚠️ Nenhum evento encontrado no lote.")

if __name__ == "__main__":
    main()
