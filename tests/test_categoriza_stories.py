# tests/test_categoriza_stories.py
import pytest
from unittest.mock import patch, MagicMock, mock_open
import categoriza_stories as cs

# --- Mock listar_imagens ---
@patch("os.walk")
def test_listar_imagens(mock_walk):
    mock_walk.return_value = [("./flyer", [], ["img1.jpg", "img2.txt"])]
    resultado = cs.listar_imagens("./flyer")
    assert len(resultado) == 1
    assert resultado[0].endswith("img1.jpg")

# --- Mock encode_image_base64 ---
@patch("builtins.open", new_callable=mock_open, read_data=b"12345")
def test_encode_image_base64(mock_file):
    base64_str = cs.encode_image_base64("dummy.png")
    assert base64_str is not None
    mock_file.assert_called_with("dummy.png", "rb")

# --- Mock enviar_para_chatgpt ---
@patch.object(cs, "construir_mapa_de_imagens")
@patch.object(cs, "client")
def test_enviar_para_chatgpt(mock_client, mock_construir):
    mock_client.chat.completions.create.return_value.choices = [MagicMock(message=MagicMock(content='{"data": [{"imagem":"story_1","isFlyer":true,"descricao":"ok"}]}'))]
    mock_construir.return_value = ({"story_1": "caminho"}, [])
    dados, mapa = cs.enviar_para_chatgpt(["img1.png"])
    assert "data" in dados
    assert mapa["story_1"] == "caminho"

# --- Mock mover_arquivo ---
@patch("os.makedirs")
@patch("os.listdir", return_value=["story_1.png"])
@patch("shutil.copy")
def test_mover_arquivo(mock_copy, mock_listdir, mock_makedirs):
    cs.mover_arquivo("stories_capturados/exec123/conta/story_2.png", "./destino", "exec123")
    mock_copy.assert_called()

# --- Mock construir_mapa_de_imagens ---
@patch("categoriza_stories.encode_image_base64", return_value="AAAA")
def test_construir_mapa_de_imagens(mock_encode):
    imagens = ["img1.png", "img2.jpg"]
    mapa, partes = cs.construir_mapa_de_imagens(imagens)
    assert len(mapa) == 2
    assert "story_1" in mapa
    assert partes[0]["type"] == "image_url"

# --- Mock processar_lote ---
@patch("categoriza_stories.enviar_para_chatgpt", return_value=({"data":[{"imagem":"story_1","isFlyer":True,"descricao":"ok"}]}, {"story_1":"caminho"}))
@patch("categoriza_stories.mover_arquivo")
def test_processar_lote(mock_mover, mock_enviar):
    cs.processar_lote(["img1.png"], "./flyer", "./lixo")
    mock_mover.assert_called()

# --- Test main ---
@patch("categoriza_stories.listar_imagens", return_value=["img1.png","img2.png"])
@patch("categoriza_stories.processar_lote")
def test_main(mock_processar, mock_listar):
    cs.main()
    mock_processar.assert_called()
