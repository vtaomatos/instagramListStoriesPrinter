#!/bin/bash
set -e

LOCK="/tmp/robo-eventos.lock"
exec 9>$LOCK || exit 1
flock -n 9 || exit 0

LOGDIR="/root/robo-eventos/logs"
mkdir -p "$LOGDIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOGFILE="$LOGDIR/pipeline_$TIMESTAMP.log"

echo "===== INÍCIO $TIMESTAMP =====" | tee -a "$LOGFILE"

cd /root/robo-eventos || exit 1

echo "[INFO] Build do robô (se necessário)" | tee -a "$LOGFILE"
docker compose build robo >> "$LOGFILE" 2>&1

echo "[INFO] Subindo Selenium" | tee -a "$LOGFILE"
docker compose up -d selenium-chrome >> "$LOGFILE" 2>&1

echo "[INFO] Aguardando Selenium ficar saudável..." | tee -a "$LOGFILE"

MAX_WAIT=60
WAITED=0

while true; do
  STATUS=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}starting{{end}}' selenium-chrome 2>/dev/null || echo "starting")

  if [ "$STATUS" = "healthy" ]; then
    echo "[INFO] Selenium pronto" | tee -a "$LOGFILE"
    break
  fi

  if [ "$WAITED" -ge "$MAX_WAIT" ]; then
    echo "[ERROR] Timeout aguardando Selenium" | tee -a "$LOGFILE"
    docker logs selenium-chrome --tail 50 | tee -a "$LOGFILE"
    docker compose down
    exit 1
  fi

  sleep 2
  WAITED=$((WAITED + 2))
done

echo "[INFO] Executando pipeline" | tee -a "$LOGFILE"

# ✅ JOB DESCARTÁVEL (correto para cron)
docker compose up --abort-on-container-exit robo 2>&1 | tee -a "$LOGFILE"

echo "[INFO] Pipeline finalizado, derrubando containers" | tee -a "$LOGFILE"
docker compose down >> "$LOGFILE" 2>&1

echo "===== FIM =====" | tee -a "$LOGFILE"
