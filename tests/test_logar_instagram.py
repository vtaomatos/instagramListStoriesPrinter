# tests/test_logar_instagram.py
import pytest
from unittest.mock import MagicMock, patch
import logar_instagram as li

# --- Teste ja_esta_logado True ---
def test_ja_esta_logado_true():
    driver = MagicMock()
    driver.find_element.return_value = True  # Simula que encontrou elemento
    assert li.ja_esta_logado(driver) is True
    assert driver.find_element.called

# --- Teste ja_esta_logado False ---
def test_ja_esta_logado_false():
    driver = MagicMock()
    driver.find_element.side_effect = Exception("Not found")
    assert li.ja_esta_logado(driver) is False

# --- Teste login_instagram com sessão já ativa ---
@patch("logar_instagram.ja_esta_logado", return_value=True)
@patch("time.sleep", return_value=None)
def test_login_instagram_sessao_ativa(mock_sleep, mock_ja_logado):
    driver = MagicMock()
    assert li.login_instagram(driver) is True

# --- Teste login_instagram manual timeout expira e falha login automático ---
@patch("logar_instagram.ja_esta_logado", return_value=False)
@patch("time.sleep", return_value=None)
@patch("logar_instagram.USUARIO", "teste_user")
@patch("logar_instagram.SENHA", "teste_pass")
def test_login_instagram_falha(mock_sleep, mock_ja_esta_logado):
    driver = MagicMock()
    driver.current_url = "login"  # continua na página de login
    assert li.login_instagram(driver, manual_timeout=1, automatic_timeout=1) is False

# --- Teste login_instagram automático bem-sucedido ---
@patch("logar_instagram.ja_esta_logado", side_effect=[False, True])
@patch("time.sleep", return_value=None)
@patch("logar_instagram.USUARIO", "teste_user")
@patch("logar_instagram.SENHA", "teste_pass")
def test_login_instagram_automatico(mock_sleep, mock_ja_logado):
    driver = MagicMock()
    driver.current_url = "login"
    driver.find_element.return_value = MagicMock()  # input username/password
    assert li.login_instagram(driver, manual_timeout=0, automatic_timeout=1) is True
