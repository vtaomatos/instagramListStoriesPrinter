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

def main(exec_id, conta):
    """
    Corta todas as imagens PNG da conta especificada dentro de stories_capturados/{exec_id}/{conta}
    """
    caminho_conta = os.path.join("stories_capturados", exec_id, conta)
    
    if not os.path.exists(caminho_conta):
        print(f"⚠️ Pasta não encontrada: {caminho_conta}")
        return False

    imagens = glob.glob(os.path.join(caminho_conta, "**", "*.png"), recursive=True)

    if not imagens:
        print(f"⚠️ Nenhuma imagem PNG encontrada na pasta: {caminho_conta}")
        return False

    print(f"📂 Encontradas {len(imagens)} imagens da conta '{conta}' em '{exec_id}'")

    for caminho in imagens:
        # cortar_imagem(caminho, largura_corte=455, altura_corte=824)
        cortar_imagem(caminho, largura_corte=245, altura_corte=460)


    return True