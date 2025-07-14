import os
import time
import json
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import sys
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
import pytz

sys.stdout.reconfigure(encoding='utf-8')


load_dotenv()

USUARIO = os.getenv("INSTAGRAM_USUARIO")
SENHA = os.getenv("INSTAGRAM_SENHA")
ROOT_DIR = os.getenv("ROOT_DIR", "./stories_capturados")
EXEC_ID = datetime.now().strftime("%Y%m%d_%H%M%S")


import os
from datetime import datetime
import pytz

def maior_horario_execucao(conta):
    try:
        # Filtra apenas as pastas que têm uma subpasta com o nome da conta
        pastas_validas = [
            pasta for pasta in os.listdir(ROOT_DIR)
            if os.path.isdir(os.path.join(ROOT_DIR, pasta, conta))
        ]

        if not pastas_validas:
            print(f"⚠️ Nenhuma execução anterior encontrada para a conta '{conta}'.")
            return None

        # Converte o nome da pasta em datetime e pega a mais recente
        maior_pasta = max(
            pastas_validas,
            key=lambda x: datetime.strptime(x, "%Y%m%d_%H%M%S")
        )

        tz = pytz.timezone("America/Sao_Paulo")
        horario_dt = tz.localize(datetime.strptime(maior_pasta, "%Y%m%d_%H%M%S"))

        print(f"🕒 Maior horário de execução da conta '{conta}': {horario_dt}")
        return horario_dt
    except Exception as e:
        print(f"⚠️ Erro ao buscar a maior execução da conta '{conta}': {e}")
        return None

def carregar_contas_do_glossario(caminho="glossario.json"):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            glossario = json.load(f)

        localizacao = next((item for item in glossario["data"] if item["id"] == "glossario_localizacao"), None)
        if not localizacao:
            print("⚠️ Nenhuma seção 'glossario_localizacao' encontrada no glossário.")
            return []

        contas = [obj["instagram"] for obj in localizacao.get("conteudo", []) if "instagram" in obj]
        print(f"✅ {len(contas)} contas carregadas do glossário.")
        return contas

    except Exception as e:
        print(f"⚠️ Erro ao carregar contas do glossário: {e}")
        return []

CONTAS = carregar_contas_do_glossario()

TEMPO_POR_STORY = .5

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
# driver.set_window_position(960, 0)  # metade direita da tela
# driver.set_window_size(960, 1080)


def pegar_horario_story():
    try:
        horario_element = driver.find_element(By.XPATH, "//time")
        horario = horario_element.get_attribute("datetime")
        if horario:
            print(f"🕒 Horário do story: \n {horario}")
            return horario
        else:
            print("⚠️ Horário do story não encontrado.")
            return None
    except NoSuchElementException:
        print("⚠️ Elemento de horário não encontrado.")
        return None
    

def login_instagram():
    for tentativa in range(2):  # tenta até 2 vezes
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
            return  # login deu certo, sai da função
        except:
            print("❌ Login falhou.")

    # se chegou aqui, as duas tentativas falharam
    print("🚫 Não foi possível logar após 2 tentativas. Encerrando.")
    sys.exit(1)  # encerra o programa com erro


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

def pausar_story():
    time.sleep(1)
    
    print("⏸️ pausando story...")
    try:
        botao_pausar = driver.find_element(By.XPATH,'//section//*[contains(text(), "Pausar") or contains(text(), "Pause")]/ancestor::div[2]')
        botao_pausar.click()

        print("⏸️ Story pausado.")
    except Exception as e:
        print("⚠️ Não foi possível pausar o story:", e)


def ocultar_labels_topo():
    print("🔍 Ocultando labels do topo...")
    try:
        div_labels_top = driver.find_element(By.XPATH, '//section//*[contains(text(), "Menu")]/ancestor::div[5]')
        driver.execute_script("arguments[0].style.display='none';", div_labels_top)
        print("✅ Labels do topo ocultadas.")
    except NoSuchElementException:
        print("⚠️ Não foi possível ocultar as labels do topo, talvez já estejam ocultas.")
    except Exception as e:
        print("⚠️ Erro ao ocultar as labels do topo:", e)

def ocultar_labels_baixo():
    print("🔍 Ocultando labels de baixo...")
    try:
        try:
            div_labels_baixo = driver.find_element(By.XPATH, '//section//*[contains(text(), "Curtir") or contains(text(), "Like")]/ancestor::div[6]')
        except NoSuchElementException:
            try:
                div_labels_baixo = driver.find_element(By.XPATH, '//section//*[contains(text(), "Direct") or contains(text(), "Share")]/ancestor::div[6]')
            except NoSuchElementException:
                try:
                    div_labels_baixo = driver.find_element(By.XPATH, '//textarea[contains(@placeholder, "Responder a")]/ancestor::div[5]')
                except NoSuchElementException:
                    div_labels_baixo = None
        if not div_labels_baixo: 
            print("⚠️ Não foi possível encontrar as labels de baixo, talvez já estejam ocultas.")
            return
        
        driver.execute_script("arguments[0].style.display='none';", div_labels_baixo)
        print("✅ Labels de baixo ocultadas.")
    except NoSuchElementException:
        print("⚠️ Não foi possível ocultar as labels de baixo, talvez já estejam ocultas.")
    except Exception as e:
        print("⚠️ Erro ao ocultar as labels de baixo:", e)


def ocultar_labels():
    print("🔍 Ocultando todas as labels...")
    ocultar_labels_topo()
    ocultar_labels_baixo()
    print("✅ Todas as labels ocultadas.")  

def checar_se_ja_capturado_pelo_horario(ultima_execucao_captura_conta):
    horario_story = pegar_horario_story()
    horario_story = datetime.fromisoformat(horario_story.replace("Z", "+00:00"))  # UTC

    print("🕒horario_story_convertido: \n", horario_story)
    print("🕒ultima_execucao_captura_conta: \n", ultima_execucao_captura_conta)

    if not ultima_execucao_captura_conta:
        print("⚠️ Não foi possível determinar o horário da última execução.")
        return False
    if not horario_story:
        print("⚠️ Não foi possível obter o horário do story.")
        return False
    if horario_story < ultima_execucao_captura_conta:
        print("⚠️ Story já capturado pelo horário, pulando.")
        return True

    print("✅ Story ainda não capturado pelo horário, prosseguindo.")    
    return False

def avançar_story():
    try:
        seta_direita = driver.find_element(By.XPATH,'//section//*[contains(text(), "Avançar") or contains(text(), "Next")]/ancestor::div[2]')
        seta_direita.click()
        time.sleep(TEMPO_POR_STORY)
        return True
    except NoSuchElementException as e:
        print("🚫 Sem mais stories.")
        return False


def faz_a_captura_do_story(pasta, story_index):
    try:
        time.sleep(1)  # espera um pouco para garantir que o story esteja carregado
        ocultar_labels()            
        print(f"📸 Capturando story {story_index}...")
        driver.save_screenshot(f"{pasta}/story_{story_index}.png")
        print(f"📸 Screenshot do story {pasta}/story_{story_index}.png salva.")
        return story_index + 1
    except (TimeoutException, NoSuchElementException):
        print(f"⚠️ Não foi possível tirar screenchshot ou salvar a imagem {pasta}/story_{story_index}.png, pulando.")
        return story_index

def capturar_stories(conta):
    
    abrir_stories(conta)
    ver_story()

    if not verificar_se_story_abriu(conta):
        return
    
    pausar_story()
    voltar_ao_primeiro_story()

    pasta = f"{ROOT_DIR}/{EXEC_ID}/{conta}"
    os.makedirs(pasta, exist_ok=True)
    
    story_index = 1
    ultima_execucao_captura_conta = maior_horario_execucao(conta)

    while True:
        
        if not checar_se_ja_capturado_pelo_horario(ultima_execucao_captura_conta):                
                story_index = faz_a_captura_do_story(pasta, story_index)
        
        if not avançar_story():
            break

    return True

try:
    login_instagram()
    for conta in CONTAS:
        if not capturar_stories(conta):
            print(f"⚠️ Não foi possível capturar stories de @{conta}, pulando.")
        else:
            print(f"✅ Stories de @{conta} capturados com sucesso.")
            
finally:
    driver.quit()
    print("\n✅ Finalizado e navegador fechado.")
