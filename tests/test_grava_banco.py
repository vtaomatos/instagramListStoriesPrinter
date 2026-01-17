# tests/test_grava_banco.py
import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import grava_banco as gb

# --- Teste quando arquivo SQL não existe ---
@patch("os.path.isfile", return_value=False)
def test_main_arquivo_nao_existe(mock_isfile):
    resultado = gb.main("exec123", "conta")
    assert resultado is False

# --- Teste quando já executado (cursor.fetchone retorna True) ---
@patch("os.path.isfile", return_value=True)
@patch("mysql.connector.connect")
@patch("builtins.open", new_callable=mock_open, read_data="SELECT 1;")
def test_main_ja_executado(mock_file, mock_connect, mock_isfile):
    # Mock da conexão e cursor do MySQL
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1,)  # Simula já executado

    # Chama a função real
    resultado = gb.main("exec123", "conta")
    assert resultado is False

    # --- Correção: caminho compatível Windows/Linux ---
    expected_filename = os.path.join(".", "migrations_sql", "exec123_conta.sql")
    called = any(
    len(call[0]) > 1 and call[0][1][0].replace("\\", "/").endswith("exec123_conta.sql")
        for call in mock_cursor.execute.call_args_list
    )
    assert called



# --- Teste execução normal ---
@patch("os.path.isfile", return_value=True)
@patch("mysql.connector.connect")
@patch("builtins.open", new_callable=mock_open, read_data="CREATE TABLE teste; INSERT INTO teste VALUES (1);")
def test_main_execucao_normal(mock_file, mock_connect, mock_isfile):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Nunca executado

    resultado = gb.main("exec123", "conta")
    assert resultado is True
    # Deve executar queries do arquivo
    assert mock_cursor.execute.call_count >= 3  # CREATE TABLE + INSERT + INSERT migrations_sql
    mock_conn.commit.assert_called()
