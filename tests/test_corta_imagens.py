# tests/test_corta_imagens.py
import pytest
from unittest.mock import patch, MagicMock
import corta_imagens as ci

# --- Teste da função cortar_imagem ---
@patch("corta_imagens.Image.open")
def test_cortar_imagem(mock_open):
    mock_img = MagicMock()
    mock_img.size = (1000, 1000)
    mock_img.crop.return_value = mock_img
    mock_open.return_value = mock_img

    ci.cortar_imagem("dummy.png", largura_corte=200, altura_corte=200, destino="saida.png")
    mock_img.crop.assert_called_once()
    mock_img.save.assert_called_once_with("saida.png")

# --- Teste da função main quando pasta não existe ---
@patch("os.path.exists", return_value=False)
def test_main_pasta_nao_existe(mock_exists):
    resultado = ci.main("exec123", "conta")
    assert resultado is False

# --- Teste da função main quando não há imagens ---
@patch("os.path.exists", return_value=True)
@patch("glob.glob", return_value=[])
def test_main_sem_imagens(mock_glob, mock_exists):
    resultado = ci.main("exec123", "conta")
    assert resultado is False

# --- Teste da função main com imagens ---
@patch("corta_imagens.cortar_imagem")
@patch("os.path.exists", return_value=True)
@patch("glob.glob", return_value=["img1.png", "img2.png"])
def test_main_com_imagens(mock_glob, mock_exists, mock_cortar):
    resultado = ci.main("exec123", "conta")
    assert resultado is True
    assert mock_cortar.call_count == 2
