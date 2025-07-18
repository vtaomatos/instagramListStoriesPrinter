import os
import sys
import time
from dotenv import load_dotenv
from datetime import datetime
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

USUARIO = os.getenv("INSTAGRAM_USUARIO")
SENHA = os.getenv("INSTAGRAM_SENHA")
EXEC_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

tentativas = 3

def login_instagram(driver):
    for tentativa in range(tentativas):  # tenta até 3 vezes
        print(f"🔐 Tentando login no Instagram... (tentativa {tentativa + 1})")
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)

        try:
            campos = driver.find_elements(By.TAG_NAME, "input")
            campos[0].clear()
            campos[1].clear()
            campos[0].send_keys(USUARIO)
            campos[1].send_keys(SENHA)
            campos[1].submit()
        except Exception as e:
            print(f"⚠️ Erro ao preencher login: {e}")
            continue

        time.sleep(5)
        try:
            driver.find_element(By.XPATH, "//*[self::button or self::div][contains(text(), 'Agora não')]").click()
            print("✅ Logado com sucesso")
            return True
        except:
            print("❌ Login falhou.")

    # se chegou aqui, as duas tentativas falharam
    print("🚫 Não foi possível logar após {tentativas} tentativas. Encerrando.")
    return False
