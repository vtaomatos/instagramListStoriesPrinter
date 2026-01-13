#!/bin/bash

echo "🚀 Iniciando ambiente gráfico..."

# Display virtual
Xvfb :99 -screen 0 1366x768x24 &

sleep 2

# Window manager
fluxbox &

sleep 2

# VNC (sem senha por enquanto)
x11vnc -display :99 -nopw -forever -shared -rfbport 5900 &

sleep 2

echo "🖥️ VNC pronto na porta 5900"

# Agora roda o robô
python pipeline.py
