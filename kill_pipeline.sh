#!/bin/bash

# Nome do processo que queremos matar
PROCESSO="pipeline.py"

# Encontra os PIDs
PIDS=$(pgrep -f $PROCESSO)

if [ -z "$PIDS" ]; then
    echo "❌ Nenhum processo $PROCESSO rodando."
    exit 0
fi

echo "⚠️ Matando processo(s) $PROCESSO com PID(s): $PIDS"

# Mata cada PID
for PID in $PIDS; do
    kill $PID
    echo "🛑 PID $PID encerrado"
done

echo "✅ Todos os processos $PROCESSO foram encerrados."
