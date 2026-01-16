#!/bin/bash

# 🔹 Garantir PATH completo para o cron
export PATH=/usr/local/bin:/usr/bin:/bin

# 🔹 Caminho absoluto do Python
PYTHON=/usr/local/bin/python3

# 🔹 Timestamp e log
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOGFILE="/app/logs/pipeline_$TIMESTAMP.log"

echo "===== INÍCIO PIPELINE $TIMESTAMP =====" >> "$LOGFILE"

cd /app || {
  echo "❌ Falha ao acessar /app" >> "$LOGFILE"
  exit 1
}

# Debug ambiente
echo "Python usado: $PYTHON" >> "$LOGFILE"
$PYTHON --version >> "$LOGFILE" 2>&1

# Executa o pipeline
$PYTHON pipeline.py >> "$LOGFILE" 2>&1
STATUS=$?

if [ $STATUS -ne 0 ]; then
  echo "⚠️ Pipeline finalizou com ERRO (exit $STATUS)" >> "$LOGFILE"
else
  echo "✅ Pipeline finalizado com SUCESSO" >> "$LOGFILE"
fi

echo "===== FIM PIPELINE =====" >> "$LOGFILE"
