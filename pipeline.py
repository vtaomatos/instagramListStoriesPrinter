import time
from datetime import datetime
import sys
import json
import signal  # 🆕
from logar_instagram import login_instagram
from selenium import webdriver
from busca_coordenadas import main as buscarCoordenadasMain
from captura_stories import capturar_stories
from transcreve_flyers import main as trascreveFlyersMain
from corta_imagens import main as cortaImagensMain
from grava_banco import main as gravaBancoMain
from selenium.webdriver.chrome.options import Options
import shutil
import os
import requests

sys.stdout.reconfigure(encoding='utf-8')

driver = None  # 🆕 referência global

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# 🆕 HANDLER DE ENCERRAMENTO SEGURO
def shutdown_handler(sig, frame):
    log("🛑 Ctrl+C detectado. Encerrando robô com segurança...")
    global driver
    if driver:
        try:
            driver.quit()
            log("🧹 Sessão Selenium encerrada com sucesso.")
        except Exception as e:
            log(f"⚠️ Erro ao encerrar sessão Selenium: {e}")
    sys.exit(0)

# 🆕 REGISTRA OS SINAIS
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


def carregar_contas_do_glossario(caminho="glossario.json"):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            glossario = json.load(f)

        localizacao = next((item for item in glossario["data"] if item["id"] == "glossario_localizacao"), None)
        if not localizacao:
            log("⚠️ Nenhuma seção 'glossario_localizacao' encontrada no glossário.")
            return []

        contas = [obj["instagram"] for obj in localizacao.get("conteudo", []) if "instagram" in obj]
        log(f"✅ {len(contas)} contas carregadas do glossário.")
        return contas

    except Exception as e:
        log(f"⚠️ Erro ao carregar contas do glossário: {e}")
        return []


EXEC_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
log(f"📦 Iniciando pipeline completo... ({EXEC_ID})")

# Inicia o navegador
log("🌐 Abrindo navegador...")

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# 🔐 PROFILE PERSISTENTE
options.add_argument("--user-data-dir=/home/seluser/chrome-profile")

driver = webdriver.Remote(
    command_executor="http://selenium-chrome:4444/wd/hub",
    options=options
)
driver.set_window_size(1920, 1080)

try:
    # Etapa: Buscar coordenadas
    inicio_etapa = time.time()
    log("🔍 Buscando novos locais para adicionar ao radar...")
    buscarCoordenadasMain()
    log(f"✅ Coordenadas buscadas em {time.time() - inicio_etapa:.1f}s")

    CONTAS = carregar_contas_do_glossario()

    # Etapa: Login Instagram
    inicio_etapa = time.time()
    log("🔐 Realizando login no Instagram...")
    if not login_instagram(driver):
        log("❌ Falha no login. Encerrando pipeline.")
        sys.exit(1)
    log(f"✅ Login efetuado em {time.time() - inicio_etapa:.1f}s")

    # Etapas por conta
    for conta in CONTAS:
        log(f"\n🧩 Iniciando pipeline da conta: {conta}\n")

        # Captura stories
        inicio_etapa = time.time()
        log("📸 Capturando stories...")
        if not capturar_stories(conta, EXEC_ID, driver):
            log("⚠️ NÃO CAPTUROU STORIES")
            continue
        log(f"✅ Stories capturados em {time.time() - inicio_etapa:.1f}s")

        # Corta imagens
        inicio_etapa = time.time()
        log("✂️ Cortando imagens...")
        if not cortaImagensMain(EXEC_ID, conta):
            log("⚠️ NÃO CORTOU IMAGENS")
            continue
        log(f"✅ Imagens cortadas em {time.time() - inicio_etapa:.1f}s")

        # Transcreve flyers
        inicio_etapa = time.time()
        log("📝 Transcrevendo textos dos flyers...")
        if not trascreveFlyersMain(EXEC_ID, conta):
            log("⚠️ NÃO TRANSCREVEU FLYERS")
            continue
        log(f"✅ Flyers transcritos em {time.time() - inicio_etapa:.1f}s")

        # Grava no banco
        inicio_etapa = time.time()
        log("💾 Gravando dados no banco de dados...")
        if not gravaBancoMain(EXEC_ID, conta):
            log("⚠️ NÃO GRAVOU NO BANCO")
            continue
        log(f"✅ Dados gravados em {time.time() - inicio_etapa:.1f}s")

        log(f"\n✅ Finalizado para a conta: {conta}\n{'─'*60}")

finally:
    log("Finalizada execução: " + EXEC_ID)

    if driver:
        driver.quit()
        log("🧹 Sessão Selenium encerrada.")
    
    log("Apagando arquivos temporários...")
    #apagar pasta de migrations
    #apagar pasta de stories_capturados
    #Deixar apenas os 6 logs mais recentes na pasta de logs

    shutil.rmtree(f"./stories_capturados/{EXEC_ID}/", ignore_errors=True)
    shutil.rmtree(f"./migrations_sql/", ignore_errors=True)
    
    logs = sorted(
        [f for f in os.listdir("./logs/") if f.startswith("pipeline_")],
        key=lambda x: os.path.getmtime(os.path.join("./logs/", x))
    )

    # Deixar apenas os 6 logs mais recentes na pasta de logs
    for log_file in logs[:-6]:
        os.remove(os.path.join("./logs/", log_file))

    
    #Chama link de conversao de base64 para imagens no servidor;
    requests.post("https://radareventos.com.br/imgconverter.php")

log("\n🎉 Pipeline finalizado com sucesso!")
