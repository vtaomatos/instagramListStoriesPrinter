from PIL import Image
import os
import glob
import sys

sys.stdout.reconfigure(encoding='utf-8')


def cortar_imagem(caminho_imagem, largura_corte, altura_corte, destino=None):
    img = Image.open(caminho_imagem)
    largura_original, altura_original = img.size

    # Define o ponto central para cortar ao redor
    esquerda = (largura_original - largura_corte) // 2
    topo = (altura_original - altura_corte) // 2
    direita = esquerda + largura_corte
    fundo = topo + altura_corte

    # Corta a imagem
    imagem_cortada = img.crop((esquerda, topo, direita, fundo))

    # Define o destino da imagem
    destino = destino or caminho_imagem
    imagem_cortada.save(destino)
    print(f"✅ Imagem cortada salva em: {destino}")



# Caminho para imagens
imagens = glob.glob("stories_capturados/**/*.png", recursive=True)

for caminho in imagens:
    cortar_imagem(caminho, largura_corte=455, altura_corte=824)