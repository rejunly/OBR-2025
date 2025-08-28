import RPi.GPIO as GPIO
import time

# --- Pinos GPIO para o Sensor Ultrassônico ---
# Altere estes pinos se você os conectou em outro lugar
GPIO_TRIGGER = 23
GPIO_ECHO = 24

def setup_sensor():
    """Configura os pinos GPIO para o sensor. Chame isso uma vez no início."""
    try:
        # A configuração do modo BCM já é feita pelo motor_control,
        # mas é bom garantir.
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
        # Não levanta exceção para não parar o programa principal se o sensor falhar
        pass

def get_distance():
    """Mede e retorna a distância em centímetros."""
    try:
        # Envia um pulso de 10us para o trigger para iniciar a medição
        GPIO.output(GPIO_TRIGGER, True)
        time.sleep(0.00001)
        GPIO.output(GPIO_TRIGGER, False)

        start_time = time.time()
        stop_time = time.time()
        timeout = start_time + 0.1 # Timeout de 0.1s para evitar travamentos

        # Grava o último tempo de pulso baixo (início da espera pelo eco)
        while GPIO.input(GPIO_ECHO) == 0 and start_time < timeout:
            start_time = time.time()

        # Grava o tempo de chegada do pulso de eco
        while GPIO.input(GPIO_ECHO) == 1 and stop_time < timeout:
            stop_time = time.time()

        # Calcula a duração do pulso
        time_elapsed = stop_time - start_time
        # Multiplica pela velocidade do som (34300 cm/s)
        # e divide por 2, porque o som vai e volta
        distance = (time_elapsed * 34300) / 2

        # Retorna uma distância grande se o valor for irreal (erro de leitura)
        return distance if distance > 0 and distance < 400 else 999
    except Exception:
        # Em caso de qualquer erro, retorna uma distância segura (grande)
        return 999

def cleanup_sensor():
    """Limpa os pinos do sensor."""
    # O GPIO.cleanup() geral no motor_control já cuida disso.
    pass
