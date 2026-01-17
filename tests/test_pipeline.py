import pytest
from unittest.mock import patch, MagicMock
import pipeline

EXEC_ID = "20260117"


# --- Teste pipeline normal ---
@patch("busca_coordenadas.carregar_lista_instagrams", return_value=["conta1", "conta2"])
@patch("pipeline.webdriver.Remote")
@patch("pipeline.carregar_contas_do_glossario", return_value=["conta1", "conta2"])
@patch("pipeline.gravaBancoMain", return_value=True)
@patch("pipeline.trascreveFlyersMain", return_value=True)
@patch("pipeline.cortaImagensMain", return_value=True)
@patch("pipeline.capturar_stories", return_value=True)
@patch("pipeline.login_instagram", return_value=True)
def test_pipeline_normal(mock_login, mock_capturar_stories, mock_cortaImagens,
                         mock_transcreveFlyers, mock_gravaBanco, mock_carregar_contas,
                         mock_webdriver, carregar_lista_instagrams):
    """
    Testa o pipeline completo chamando pipeline.main() com mocks.
    Garante que login_instagram é chamado e etapas são executadas.
    """
    # Mock do driver Selenium
    driver_mock = MagicMock()
    mock_webdriver.return_value = driver_mock

    # Rodando o pipeline real (com todos os mocks)
    resultado = pipeline.main(exec_id=EXEC_ID, contas=["conta1", "conta2"])
    assert resultado is True
    mock_login.assert_called_once_with(driver_mock)

# --- Smoke test simplificado do pipeline ---
@patch("busca_coordenadas.carregar_lista_instagrams", return_value=["conta1", "conta2"])
@patch("pipeline.login_instagram", return_value=True)
@patch("pipeline.capturar_stories", return_value=True)
@patch("pipeline.cortaImagensMain", return_value=True)
@patch("pipeline.trascreveFlyersMain", return_value=True)
@patch("pipeline.gravaBancoMain", return_value=True)
@patch("pipeline.carregar_contas_do_glossario", return_value=["conta1", "conta2"])
@patch("pipeline.webdriver.Remote")
def test_pipeline_smoke(mock_webdriver, mock_carregar_contas, mock_gravaBanco,
                        mock_transcreveFlyers, mock_cortaImagens, mock_capturar_stories,
                        mock_login, mock_carregar_lista):
    """
    Smoke test para garantir que pipeline.main() roda do início ao fim com mocks.
    """
    driver_mock = MagicMock()
    mock_webdriver.return_value = driver_mock

    resultado = pipeline.main(exec_id=EXEC_ID, contas=["conta1", "conta2"])
    assert resultado is True

