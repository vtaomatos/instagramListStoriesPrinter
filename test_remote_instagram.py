from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

SELENIUM_REMOTE_URL = "http://selenium-chrome:4444/wd/hub"

options = Options()
options.add_argument("--disable-notifications")
options.add_argument("--disable-infobars")
options.add_argument("--start-maximized")

print("🔗 Conectando ao Selenium remoto...")
driver = webdriver.Remote(
    command_executor=SELENIUM_REMOTE_URL,
    options=options
)

try:
    print("🌐 Abrindo Instagram...")
    driver.get("https://www.instagram.com/")
    time.sleep(5)

    print("⏳ Aguardando possível login manual...")
    print("👉 Faça login pelo VNC se necessário.")
    input("⏸️  Pressione ENTER aqui no terminal quando terminar o login...")

    time.sleep(3)

    print("🔍 Verificando se está logado...")

    # Um indicador simples de login:
    # Campo de pesquisa só aparece quando logado
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Pesquisar']"))
        )
        print("✅ Login detectado com sucesso!")
    except:
        print("⚠️ Não consegui confirmar login automaticamente.")
        print("   Talvez o layout tenha mudado ou não esteja logado.")

    print("👀 Navegador permanecerá aberto.")
    input("🛑 Pressione ENTER para encerrar o teste e fechar o navegador...")

finally:
    print("🧹 Encerrando sessão...")
    driver.quit()
