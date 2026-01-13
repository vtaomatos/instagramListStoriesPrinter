#!/bin/bash
# Garante que qualquer erro seja registrado, mas não mata o container

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOGFILE="/app/logs/pipeline_$TIMESTAMP.log"

echo "===== INICIANDO PIPELINE $TIMESTAMP =====" >> $LOGFILE
python /app/pipeline.py >> $LOGFILE 2>&1
STATUS=$?

if [ $STATUS -ne 0 ]; then
    echo "⚠️ Pipeline finalizou com erro (exit $STATUS) em $TIMESTAMP" >> $LOGFILE
else
    echo "✅ Pipeline finalizado com sucesso em $TIMESTAMP" >> $LOGFILE
fi
