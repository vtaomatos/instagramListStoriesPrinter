import subprocess
import time
from datetime import datetime
import sys
import webbrowser
from logar_instagram import login_instagram
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from busca_coordenadas import main as buscarCoordenadasMain
from captura_stories import capturar_stories
from transcreve_flyers import main as trascreveFlyersMain
from corta_imagens import main as cortaImagensMain
from grava_banco import main as gravaBancoMain

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

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


chrome_options = Options()
chrome_options.binary_location = "/usr/bin/chromium"  # caminho do chromium no container
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--headless")            # roda sem GUI
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager(driver_version="140.0.7339.207").install()), options=chrome_options)
driver.maximize_window()

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
    login_instagram(driver)
    log(f"✅ Login efetuado em {time.time() - inicio_etapa:.1f}s")

    # Etapas por conta
    for conta in CONTAS:
        log(f"\n🧩 Iniciando pipeline da conta: {conta}\n")

        # Captura stories
        inicio_etapa = time.time()
        log("📸 Capturando stories...")
        if not capturar_stories(conta, EXEC_ID, driver):
            print("NÃO CAPTUROU STORIES!!!!")
            continue
        log(f"✅ Stories capturados em {time.time() - inicio_etapa:.1f}s")

        # Corta imagens
        inicio_etapa = time.time()
        log("✂️ Cortando imagens...")
        if not cortaImagensMain(EXEC_ID, conta):
            print("NÃO CORTOU IMAGENS!!!!")
            continue
        log(f"✅ Imagens cortadas em {time.time() - inicio_etapa:.1f}s")

        # Transcreve flyers
        inicio_etapa = time.time()
        log("📝 Transcrevendo textos dos flyers...")
        if not trascreveFlyersMain(EXEC_ID, conta):
            print("NÃO TRANSCREVEU FLYERS!!!!")
            continue
        log(f"✅ Flyers transcritos em {time.time() - inicio_etapa:.1f}s")

        # Grava no banco
        inicio_etapa = time.time()
        log("💾 Gravando dados no banco de dados...")
        if not gravaBancoMain(EXEC_ID, conta):
            print("NÃO GRAVOU NO BANCO!!!!")
            continue
        log(f"✅ Dados gravados em {time.time() - inicio_etapa:.1f}s")

        log(f"\n✅ Finalizado para a conta: {conta}\n{'─'*60}")

finally:
    driver.quit()
    log("🧹 Navegador fechado.")

log("\n🎉 Pipeline finalizado com sucesso!")
log("🌐 Abrindo https://radareventos.com.br/ no navegador...")
webbrowser.open("https://radareventos.com.br")
