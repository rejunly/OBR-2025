import RPi.GPIO as GPIO
import time

# Sequência de passos (half-step) para o motor 28BYJ-48
SEQ = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]

# Define os pinos de cada motor (ordem: IN1, IN2, IN3, IN4)
MOTORES = {
    "frente_esq": [17, 18, 27, 22],
    "frente_dir": [23, 24, 25, 5],
    "tras_esq":   [6, 12, 13, 19],
    "tras_dir":   [16, 20, 21, 26]
}

# Setup
GPIO.setmode(GPIO.BCM)
for pinos in MOTORES.values():
    for pino in pinos:
        GPIO.setup(pino, GPIO.OUT)
        GPIO.output(pino, 0)

# Função que gira um motor por X tempo
def girar_motor(pinos, sentido="horario", tempo=5, delay=0.002):
    fim = time.time() + tempo
    seq = SEQ if sentido == "horario" else SEQ[::-1]
    while time.time() < fim:
        for passo in seq:
            for pino, val in zip(pinos, passo):
                GPIO.output(pino, val)
            time.sleep(delay)

# Movimento geral para 4 motores
def mover_todos(sentido_dict, tempo=5):
    # sentido_dict: {"frente_esq": "horario", ...}
    inicio = time.time()
    while time.time() - inicio < tempo:
        for i in range(len(SEQ)):
            for nome_motor, pinos in MOTORES.items():
                passo = SEQ[i] if sentido_dict[nome_motor] == "horario" else SEQ[::-1][i]
                for pino, val in zip(pinos, passo):
                    GPIO.output(pino, val)
            time.sleep(0.002)

# Funções de movimento
def frente():
    sentido = {
        "frente_esq": "anti",
        "tras_esq": "horario",
        "frente_dir": "horario",
        "tras_dir": "horario"
    }
    mover_todos(sentido)

def tras():
    sentido = {
        "frente_esq": "horario",
        "tras_esq": "horario",
        "frente_dir": "anti",
        "tras_dir": "anti"
    }
    mover_todos(sentido)

def esquerda():
    sentido = {
        "frente_esq": "anti",
        "tras_esq": "anti",
        "frente_dir": "horario",
        "tras_dir": "horario"
    }
    mover_todos(sentido)

def direita():
    sentido = {
        "frente_esq": "horario",
        "tras_esq": "horario",
        "frente_dir": "anti",
        "tras_dir": "anti"
    }
    mover_todos(sentido)

def parar():
    for pinos in MOTORES.values():
        for pino in pinos:
            GPIO.output(pino, 0)

def retorno():
    tras()

def desviar(): ##ajustar nos testes
    # Parar para não bater no obstáculo
    parar()
    time.sleep(0.5)

    # Reverter um pouco para se afastar
    tras()
    time.sleep(0.5)
    parar()
    time.sleep(0.5)

    # Virar para o lado, iniciar movimento de desvio
    direita() #setar lado
    time.sleep(1) #ajustar para angulo
    parar()
    time.sleep(0.5)

    # Avançar um pouco
    frente()
    time.sleep(1)
    parar()
    time.sleep(0.5)

    # Virar para o outro lado para tentar encontrar a linha novamente
    esquerda()
    time.sleep(1) #ajustar para angulo
    parar()
    time.sleep(0.5)


def movimentar(comando):
    if comando == "Seguir em frente":
        frente()
    elif comando in ["Curva à esquerda", "Curva verde à esquerda"]:
        esquerda()
    elif comando in ["Curva à direita", "Curva verde à direita"]:
        direita()
    elif "parar" in comando:
        parar()
    elif "cinza" in comando:
        retorno()
    else:
        parar()

# Teste manual
if __name__ == "__main__":
    try:
        frente()
        time.sleep(5)
        direita()
        time.sleep(5)
        esquerda()
        time.sleep(5)
        tras()
        time.sleep(5)
        parar()
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()


