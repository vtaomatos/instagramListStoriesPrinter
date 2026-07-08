import os
import sys
import time
from dotenv import load_dotenv
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

USUARIO = os.getenv("INSTAGRAM_USUARIO")
SENHA = os.getenv("INSTAGRAM_SENHA")
EXEC_ID = datetime.now(TZ).strftime("%Y%m%d_%H%M%S")

MANUAL_TIMEOUT = 300  # tempo em segundos para login manual
AUTOMATIC_TIMEOUT = 60  # timeout para tentativa automática


def ja_esta_logado(driver):
    """Verifica se a sessão do Instagram já está ativa."""
    time.sleep(5)

    elementos_logado = [
        "//a[contains(@href, '/accounts/edit')]",
        "//svg[@aria-label='Página inicial']",
        "//a[contains(@href, '/direct')]"
    ]

    for xpath in elementos_logado:
        try:
            driver.find_element(By.XPATH, xpath)
            print("✅ Sessão do Instagram já está ativa")
            return True
        except:
            pass
    return False


def login_instagram(driver, manual_timeout=MANUAL_TIMEOUT, automatic_timeout=AUTOMATIC_TIMEOUT):
    """
    Fluxo híbrido de login:
    1. Se já logado → retorna True
    2. Login manual com timeout
    3. Tentativa automática com usuário/senha do .env
    """
    driver.get("https://www.instagram.com/")
    time.sleep(3)

    if ja_esta_logado(driver):
        return True

    print("🔐 Sessão não detectada. Abrindo página de login...")

    # Etapa 1: login manual
    print(f"⏳ Aguarde login manual (até {manual_timeout//60} minutos)...")
    start_manual = time.time()
    while time.time() - start_manual < manual_timeout:
        time.sleep(60)
        if not "login" in driver.current_url and ja_esta_logado(driver): # Pagina de login sendo aberta na função ja_esta_logado.
            print("✅ Login manual detectado!")
            return True

    print("⚠️ Tempo de login manual expirou. Tentando login automático...")

    # Etapa 2: login automático
    try:
        time.sleep(3)

        user_input = driver.find_element(By.NAME, "email")
        pass_input = driver.find_element(By.NAME, "pass")

        user_input.clear()
        user_input.send_keys(USUARIO)
        pass_input.clear()
        pass_input.send_keys(SENHA)
        pass_input.send_keys(Keys.ENTER)

        # Aguarda o login automático completar
        start_auto = time.time()
        while time.time() - start_auto < automatic_timeout:
            if ja_esta_logado(driver):
                print("✅ Login automático bem-sucedido!")
                return True
            time.sleep(2)

        print("❌ Login automático falhou. Encerrando execução...")
        return False

    except Exception as e:
        print(f"❌ Erro no login automático: {e}")
        return False
