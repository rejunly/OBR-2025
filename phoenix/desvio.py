import RPi.GPIO as GPIO
import time

# --- Pinos GPIO ---
PINO_TRIGGER = 3
PINO_ECHO = 2

# --- Parâmetros de Configuração ---
DISTANCIA_OBSTACULO = 15.0 # em cm

def setup_ultrassonico():
    """Configura os pinos GPIO para o sensor ultrassônico."""
    try:
        # Garante que o modo BCM está sendo usado
        if GPIO.getmode() != GPIO.BCM:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
        
        GPIO.setup(PINO_TRIGGER, GPIO.OUT)
        GPIO.setup(PINO_ECHO, GPIO.IN)
        GPIO.output(PINO_TRIGGER, False)
        print("Módulo Ultrassônico: Sensor configurado.")
        time.sleep(1) # Espera o sensor estabilizar
    except Exception as e:
        print(f"Módulo Ultrassônico: Erro no setup do RPi.GPIO: {e}")
        raise e

def medir_distancia():
    """
    Mede a distância usando o sensor HC-SR04.
    Retorna a distância em cm ou 999 em caso de erro/timeout.
    """
    try:
        # Envia um pulso de 10us para o Trigger
        GPIO.output(PINO_TRIGGER, True)
        time.sleep(0.00001)
        GPIO.output(PINO_TRIGGER, False)

        tempo_inicial = time.time()
        tempo_final = time.time()

        # Espera o Echo subir (início do pulso de retorno)
        timeout_start = time.time()
        while GPIO.input(PINO_ECHO) == 0:
            tempo_inicial = time.time()
            if tempo_inicial - timeout_start > 0.1: # Timeout de 100ms
                return 999

        # Espera o Echo descer (fim do pulso de retorno)
        timeout_end = time.time()
        while GPIO.input(PINO_ECHO) == 1:
            tempo_final = time.time()
            if tempo_final - timeout_end > 0.1: # Timeout de 100ms
                return 999

        duracao_pulso = tempo_final - tempo_inicial
        
        # Fórmula: distância = (tempo * velocidade_do_som) / 2
        distancia = (duracao_pulso * 34300) / 2

        return distancia
    except Exception:
        # Em caso de qualquer erro de runtime, retorna um valor seguro.
        return 999
