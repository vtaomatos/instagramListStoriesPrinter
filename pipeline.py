# chamar scripts para fazer o fluxo de trabalho
# chamar captura, depois cortar, depois caterogiza e depois transcreve, depois gravar no banco;

import subprocess
import time
from datetime import datetime
import sys
import webbrowser

sys.stdout.reconfigure(encoding='utf-8')


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def executar_etapa(nome, comando):
    log(f"🚀 Iniciando: {nome}")
    inicio = time.time()

    try:
        resultado = subprocess.run(["python", comando], capture_output=True, text=True, encoding="utf-8")
        if resultado.returncode == 0:
            log(f"✅ Finalizado: {nome} em {time.time() - inicio:.1f}s")
        else:
            log(f"❌ Erro na etapa: {nome}")
            print(resultado.stderr)
            exit(1)
    except Exception as e:
        log(f"💥 Falha ao executar '{comando}': {e}")
        exit(1)

# Etapas do pipeline
etapas = [
    ("Adição de possíveis novos locais ao radar", "busca_coordenadas.py"),
    ("Captura de stories", "captura_stories.py"),
    ("Corte das imagens", "corta_imagens.py"),
    ("Classificação dos flyers", "categoriza_stories.py"),
    ("Transcrição dos flyers", "transcreve_flyers.py"),
    ("Gravação no banco", "grava_banco.py")
]

log("📦 Iniciando pipeline completo...\n")

for nome, script in etapas:
    executar_etapa(nome, script)

log("\n🎉 Pipeline finalizado com sucesso!")


log("🌐 Abrindo https://radareventos.com.br/ no navegador...")
webbrowser.open("https://radareventos.com.br/")