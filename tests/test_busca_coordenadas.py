# tests/test_busca_coordenadas.py
import pytest
from unittest.mock import patch, mock_open, MagicMock
import busca_coordenadas as bc

# --- Testes da função buscar_info_por_nome ---
@patch("busca_coordenadas.requests.get")
def test_buscar_info_por_nome_sucesso(mock_get):
    # Mockando resposta da API
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "candidates": [{
            "formatted_address": "Rua Exemplo, 123, Santos SP",
            "geometry": {"location": {"lat": -23.95, "lng": -46.33}}
        }]
    }
    mock_get.return_value = mock_resp

    resultado = bc.buscar_info_por_nome("Local Exemplo")
    assert resultado["endereco"] == "Rua Exemplo, 123, Santos SP"
    assert resultado["latitude"] == -23.95
    assert resultado["longitude"] == -46.33

@patch("busca_coordenadas.requests.get")
def test_buscar_info_por_nome_nao_encontrado(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"candidates": []}
    mock_get.return_value = mock_resp

    resultado = bc.buscar_info_por_nome("Local Inexistente")
    assert resultado is None

@patch("busca_coordenadas.requests.get")
def test_buscar_info_por_nome_erro(mock_get):
    mock_get.side_effect = Exception("Erro de rede")
    resultado = bc.buscar_info_por_nome("Qualquer")
    assert resultado is None

# --- Testes de arquivos ---
def test_carregar_lista_instagrams():
    mock_data = "@local1\n@local2\n\n"
    with patch("builtins.open", mock_open(read_data=mock_data)):
        resultado = bc.carregar_lista_instagrams()
        assert resultado == ["local1", "local2"]

def test_salvar_lista_nao_encontrados():
    mock_file = mock_open()
    with patch("builtins.open", mock_file):
        bc.salvar_lista_nao_encontrados(["local1", "local2"])
        mock_file().write.assert_any_call("local1\n")
        mock_file().write.assert_any_call("local2\n")

def test_atualizar_glossario():
    glossario_inicial = {
        "data": [{"id": "glossario_localizacao", "conteudo": []}]
    }
    locais = [{"instagram": "local1", "endereco": "endereco1"}]

    m_open = mock_open(read_data='{"data":[{"id":"glossario_localizacao","conteudo":[]}] }')
    with patch("builtins.open", m_open):
        bc.atualizar_glossario(locais)
        # Checa se json.dump foi chamado (escrevendo arquivo)
        assert m_open().write.called
