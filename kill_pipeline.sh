#!/bin/bash
set -e

# Nome do script ou processo Python que queremos matar
PROCESSO="pipeline.py"

echo "🔍 Procurando processos $PROCESSO..."

# Procura PIDs do processo Python
PIDS=$(pgrep -f "$PROCESSO" || true)

if [ -z "$PIDS" ]; then
    echo "❌ Nenhum processo $PROCESSO rodando."
else
    echo "⚠️ Matando processo(s) $PROCESSO com PID(s): $PIDS"
    # Mata cada PID de forma segura
    for PID in $PIDS; do
        kill -TERM "$PID" 2>/dev/null || true
        echo "🛑 PID $PID encerrado"
    done
fi

# Opcional: parar container do robo caso esteja rodando via docker compose
ROBO_CONTAINER=$(docker ps -q --filter "name=robo")
if [ -n "$ROBO_CONTAINER" ]; then
    echo "⚠️ Parando container Docker do robo: $ROBO_CONTAINER"
    docker stop "$ROBO_CONTAINER"
    echo "✅ Container do robo parado"
fi

# Opcional: parar Selenium caso queira resetar tudo
SELENIUM_CONTAINER=$(docker ps -q --filter "name=selenium-chrome")
if [ -n "$SELENIUM_CONTAINER" ]; then
    echo "⚠️ Parando container Selenium: $SELENIUM_CONTAINER"
    docker stop "$SELENIUM_CONTAINER"
    echo "✅ Container Selenium parado"
fi

echo "✅ Todos os processos e containers associados foram encerrados."
