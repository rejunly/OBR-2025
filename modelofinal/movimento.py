# Movimentacao

import RPi.GPIO as GPIO
import time

# === Configuração dos motores (exemplo com dois DRV8825) ===
# Ajuste conforme seus pinos
DIR_ESQUERDA = 16
STEP_ESQUERDA = 18
DIR_DIREITA = 22
STEP_DIREITA = 24

# Inicialização dos pinos
GPIO.setmode(GPIO.BOARD)
GPIO.setup(DIR_ESQUERDA, GPIO.OUT)
GPIO.setup(STEP_ESQUERDA, GPIO.OUT)
GPIO.setup(DIR_DIREITA, GPIO.OUT)
GPIO.setup(STEP_DIREITA, GPIO.OUT)

def passo(dir_pin, step_pin, sentido, passos=10, delay=0.001):
    GPIO.output(dir_pin, GPIO.HIGH if sentido == "frente" else GPIO.LOW)
    for _ in range(passos):
        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(delay)

def frente():
    passo(DIR_ESQUERDA, STEP_ESQUERDA, "frente")
    passo(DIR_DIREITA, STEP_DIREITA, "frente")

def esquerda():
    passo(DIR_ESQUERDA, STEP_ESQUERDA, "tras")
    passo(DIR_DIREITA, STEP_DIREITA, "frente")

def direita():
    passo(DIR_ESQUERDA, STEP_ESQUERDA, "frente")
    passo(DIR_DIREITA, STEP_DIREITA, "tras")

def parar():
    # Para motores de passo, "parar" pode apenas não fazer nada
    pass

def retorno():
    # Gira para trás por um tempo (exemplo de retorno)
    for _ in range(30):
        passo(DIR_ESQUERDA, STEP_ESQUERDA, "tras")
        passo(DIR_DIREITA, STEP_DIREITA, "tras")

# === Função principal de decisão ===
def movimentar(comando):
    if comando == "Seguir em frente":
        frente()
    elif comando in ["Curva à esquerda", "Curva verde à esquerda"]:
        esquerda()
    elif comando in ["Curva à direita", "Curva verde à direita"]:
        direita()
    elif "vermelho" in comando:
        parar()
    elif "cinza" in comando:
        retorno()
    else:
        parar()

if __name__ == "__main__":
    try:
        frente()
        time.sleep(1)
        direita()
        time.sleep(1)
        esquerda()
        time.sleep(1)
        tras()
        time.sleep(1)
        parar()
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
