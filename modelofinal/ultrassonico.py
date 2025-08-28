# obstacle_avoider.py

import RPi.GPIO as GPIO
import time

# --- Pinos GPIO para o Sensor Ultrassônico ---
# Certifique-se de que estes pinos correspondem à sua ligação física
GPIO_TRIGGER = 23
GPIO_ECHO = 24

def setup_sensor():
    """
    Configura os pinos GPIO para o sensor. Chame isso uma vez no início do programa.
    """
    try:
        # Usamos o mesmo modo de pino do motor_control para evitar conflitos
        # GPIO.setmode(GPIO.BCM) 
        GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
        GPIO.setup(GPIO_ECHO, GPIO.IN)
        print("Módulo de Obstáculos: Sensor ultrassônico configurado.")
    except Exception as e:
        print(f"Módulo de Obstáculos: Erro no setup do sensor: {e}")
        # Não precisa limpar aqui, o motor_control fará a limpeza geral
        
def get_distance():
    """
    Mede e retorna a distância de um objeto em centímetros.
    Retorna um valor alto (ex: 999) se a leitura falhar.
    """
    # Envia um pulso de 10us para o Trigger
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    start_time = time.time()
    stop_time = time.time()

    # Grava o último tempo de pulso baixo
    timeout_start = time.time()
    while GPIO.input(GPIO_ECHO) == 0:
        start_time = time.time()
        # Timeout para evitar loop infinito se o sensor desconectar
        if time.time() - timeout_start > 0.1:
            return 999 

    # Grava o tempo de chegada do pulso de retorno
    timeout_start = time.time()
    while GPIO.input(GPIO_ECHO) == 1:
        stop_time = time.time()
        if time.time() - timeout_start > 0.1:
            return 999

    # Calcula a distância
    time_elapsed = stop_time - start_time
    # Velocidade do som (34300 cm/s) dividida por 2 (ida e volta)
    distance = (time_elapsed * 34300) / 2

    return distance
