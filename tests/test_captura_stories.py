# tests/test_captura_stories.py
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import captura_stories as cs

# --- Mock do driver Selenium ---
@pytest.fixture
def driver_mock():
    driver = MagicMock()
    driver.find_element.return_value.get_attribute.return_value = "2026-01-17T12:00:00Z"
    driver.find_elements.return_value = [MagicMock()]
    driver.save_screenshot.return_value = True
    driver.execute_script.return_value = True
    return driver

# --- Testes da função pegar_horario_story ---
def test_pegar_horario_story_sucesso(driver_mock):
    horario = cs.pegar_horario_story(driver_mock)
    assert horario == "2026-01-17T12:00:00Z"

def test_pegar_horario_story_sem_elemento():
    driver = MagicMock()
    driver.find_element.side_effect = cs.NoSuchElementException()
    horario = cs.pegar_horario_story(driver)
    assert horario is None

# --- Teste da função faz_a_captura_do_story ---
@patch("captura_stories.ocultar_labels")
def test_faz_a_captura_do_story(mock_ocultar_labels, driver_mock):
    result = cs.faz_a_captura_do_story("teste_pasta", 1, driver_mock)
    assert result == 2
    driver_mock.save_screenshot.assert_called()

# --- Teste da função avançar_story ---
def test_avancar_story_sucesso(driver_mock):
    assert cs.avançar_story(driver_mock) is True

def test_avancar_story_sem_stories():
    driver = MagicMock()
    driver.find_element.side_effect = cs.NoSuchElementException()
    assert cs.avançar_story(driver) is False

# --- Teste da função checar_se_ja_capturado_pelo_horario ---
def test_checar_story_nao_capturado(driver_mock):
    ultima_execucao = datetime(2026, 1, 17, 11, 0, tzinfo=timezone.utc)
    result = cs.checar_se_ja_capturado_pelo_horario(ultima_execucao, driver_mock)
    assert result is False

def test_checar_story_ja_capturado(driver_mock):
    ultima_execucao = datetime(2026, 1, 17, 13, 0, tzinfo=timezone.utc)
    result = cs.checar_se_ja_capturado_pelo_horario(ultima_execucao, driver_mock)
    assert result is True

# --- Teste da função capturar_stories (pipeline principal) ---
@patch("captura_stories.abrir_stories")
@patch("captura_stories.ver_story")
@patch("captura_stories.verificar_se_story_abriu", return_value=True)
@patch("captura_stories.pausar_story", return_value=True)
@patch("captura_stories.voltar_ao_primeiro_story")
@patch("captura_stories.maior_horario_execucao", return_value=None)
@patch("captura_stories.faz_a_captura_do_story", side_effect=lambda pasta, idx, driver: idx + 1 if idx < 2 else idx)
@patch("captura_stories.avançar_story", side_effect=[True, False])
@patch("os.makedirs")
@patch("time.sleep", return_value=None)
def test_capturar_stories(mock_sleep, mock_makedirs, mock_avancar, mock_faz, mock_maior,
                          mock_voltar, mock_pausar, mock_verificar, mock_ver, mock_abrir, driver_mock):
    result = cs.capturar_stories("conta_exemplo", "exec123", driver_mock)
    assert result is True
