import RPi.GPIO as GPIO
import time

# --- Pinos GPIO para o Sensor Ultrassônico ---
# Altere estes pinos se você os conectou em outro lugar
GPIO_TRIGGER = 23
GPIO_ECHO = 24

def setup_sensor():
    """Configura os pinos GPIO para o sensor. Chame isso uma vez no início."""
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        # Define os pinos como entrada (ECHO) ou saída (TRIGGER)
        GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
        GPIO.setup(GPIO_ECHO, GPIO.IN)
        # Garante que o trigger comece em nível baixo
        GPIO.output(GPIO_TRIGGER, False)
        print("Módulo Ultrassônico: Sensor configurado.")
        time.sleep(1) # Aguarda o sensor estabilizar
    except Exception as e:
        print(f"Módulo Ultrassônico: Erro no setup do RPi.GPIO: {e}")
        raise e

def get_distance():
    """Mede e retorna a distância em centímetros."""
    # Envia um pulso de 10us para o trigger para iniciar a medição
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    start_time = time.time()
    stop_time = time.time()

    # Grava o último tempo de pulso baixo (início da espera pelo eco)
    while GPIO.input(GPIO_ECHO) == 0:
        start_time = time.time()

    # Grava o tempo de chegada do pulso de eco
    while GPIO.input(GPIO_ECHO) == 1:
        stop_time = time.time()

    # Calcula a duração do pulso
    time_elapsed = stop_time - start_time
    # Multiplica pela velocidade do som (34300 cm/s)
    # e divide por 2, porque o som vai e volta
    distance = (time_elapsed * 34300) / 2

    return distance

def cleanup_sensor():
    """Limpa os pinos do sensor. (Opcional, pois o motor_control já faz a limpeza geral)."""
    # GPIO.cleanup() já é chamado no motor_control, então esta função é redundante
    # mas mantida por boas práticas de modularização.
    pass
