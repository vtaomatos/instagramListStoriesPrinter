import os
import time
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import sys

sys.stdout.reconfigure(encoding='utf-8')


load_dotenv()

USUARIO = os.getenv("INSTAGRAM_USUARIO")
SENHA = os.getenv("INSTAGRAM_SENHA")
CONTAS = [
    "meulugar.bar", 
    "mobydicksantos", 
    "donnag.santos",
    "donnaguilherminabar",
    "ativahouse",
    "toatoabarc7",
    "bartusantos",
    "x9_pioneira",
    "cristoearesposta",
    "cemporcentovida"
    ]
TEMPO_POR_STORY = 1

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
# driver.set_window_position(960, 0)  # metade direita da tela
# driver.set_window_size(960, 1080)

def login_instagram():
    print("🔐 Logando no Instagram...")
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)

    campos = driver.find_elements(By.TAG_NAME, "input")
    campos[0].send_keys(USUARIO)
    campos[1].send_keys(SENHA)
    campos[1].submit()

    time.sleep(7)
    try:
        driver.find_element(By.XPATH, "//button[contains(text(),'Agora não')]").click()
    except:
        pass
    print("✅ Logado")


def abrir_stories(conta):
    print(f"\n📲 Acessando stories de @{conta}...")
    driver.get(f"https://www.instagram.com/stories/{conta}/")
    time.sleep(3)

def verificar_se_story_abriu(conta):
    try:
        sections = driver.find_elements(By.XPATH, "//section")
        if len(sections) == 1:
            print(f"\n ✅ Acessado stories @{conta}...")
            return True
        
        else:
            print(f"⚠️ Nenhum story encontrado para @{conta}.")
        
    except NoSuchElementException:
        print(f"⚠️ Nenhum story encontrado para @{conta}.")
        
    return False


def ver_story():
    print("👀 passando pelo botão 'ver stories'...")
    try:
        botao_ver = driver.find_element(By.XPATH, "//div[contains(text(),'Ver story') or contains(text(),'Watch story')]")
        botao_ver.click()
        print("🖱️ Botão 'Ver story' clicado")
        time.sleep(2)
    except:
        pass

    print("✅ Passamos pelo botão 'ver stories'...")


def voltar_ao_primeiro_story(max_tentativas=50, delay=0.5):

    for _ in range(max_tentativas):
        try:
            seta_voltar = driver.find_element(By.XPATH,'//section//*[contains(text(), "Voltar") or contains(text(), "Back")]/ancestor::div[2]')
            seta_voltar.click()
            time.sleep(delay)
        except NoSuchElementException:
            print("✅ Primeiro story alcançado.")
            break
        except Exception as e:
            print(f"⚠️ Erro inesperado: {e}")
            break

def baixar_imagem(src, caminho):
    try:
        resposta = requests.get(src, stream=True)
        if resposta.status_code == 200:
            with open(caminho, "wb") as f:
                for bloco in resposta.iter_content(1024):
                    f.write(bloco)
            return True
    except Exception as e:
        print(f"Erro ao baixar imagem: {e}")
    return False

def pausar_story():
    time.sleep(1)
    
    print("⏸️ pausando story...")
    try:
        botao_pausar = driver.find_element(By.XPATH,'//section//*[contains(text(), "Pausar") or contains(text(), "Pause")]/ancestor::div[2]')
        botao_pausar.click()

        print("⏸️ Story pausado.")
    except Exception as e:
        print("⚠️ Não foi possível pausar o story:", e)


def capturar_stories(conta):
    
    abrir_stories(conta)
    ver_story()

    if not verificar_se_story_abriu(conta):
        return
    
    pausar_story()
    voltar_ao_primeiro_story()

    pasta = f"./stories_capturados/{conta}"
    os.makedirs(pasta, exist_ok=True)
    
    story_index = 1
    while True:
        try:
            time.sleep(1)

            print(f"📸 Capturando story {story_index}...")
            driver.save_screenshot(f"{pasta}/story_{story_index}.png")
            print(f"📸 Screenshot do story {pasta}/story_{story_index}.png salva.")

        except (TimeoutException, NoSuchElementException):
            print(f"⚠️ Não foi possível tirar screenchshot ou salvar a imagem {pasta}/story_{story_index}.png, pulando.")

        # Tenta ir para o próximo story
        try:
            seta_direita = driver.find_element(By.XPATH,'//section//*[contains(text(), "Avançar") or contains(text(), "Next")]/ancestor::div[2]')
            seta_direita.click()
            story_index += 1
            time.sleep(TEMPO_POR_STORY)
        except NoSuchElementException:
            print("🚫 Sem mais stories.")
            break

try:
    login_instagram()
    for conta in CONTAS:
        capturar_stories(conta)
finally:
    driver.quit()
    print("\n✅ Finalizado e navegador fechado.")
