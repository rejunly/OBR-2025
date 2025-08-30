import RPi.GPIO as GPIO
import time

# --- Pinos GPIO ---
# Motores
IN1_L, IN2_L, EN_L = 21, 20, 12 # Motor Esquerdo
IN1_R, IN2_R, EN_R = 16, 19, 13 # Motor Direito

# Sensor Ultrassônico
PINO_TRIGGER = 3
PINO_ECHO = 2

# --- PARÂMETROS DE CONFIGURAÇÃO ---
# Altere estes valores para calibrar seu robô

# 1. Distância para acionar o desvio (em cm)
DISTANCIA_OBSTACULO = 15.0

# 2. Parâmetros do movimento para FRENTE (Contínuo)
velocidade_inicial = 100.0 # Pico inicial para vencer a inércia
velocidade_cruzeiro = 30.0  # Velocidade estável para frente
tempo_rampa = 0.5          # Tempo (s) para ir da vel. inicial à de cruzeiro

# 3. Parâmetros do GIRO
velocidade_giro_90 = 90.0 # Velocidade (Duty Cycle) usada durante os giros

## --- ALTERAÇÃO 2: TEMPOS DE GIRO INDIVIDUAIS ---
# Tempos para cada um dos 4 giros na manobra de desvio.
# A manobra é: vira dir (1) -> anda -> vira esq (2) -> anda -> vira esq (3) -> anda -> vira dir (4)
tempo_giro_desvio_1 = 0.6  # Duração (s) do 1º giro (Direita)
tempo_giro_desvio_2 = 0.6  # Duração (s) do 2º giro (Esquerda)
tempo_giro_desvio_3 = 0.6  # Duração (s) do 3º giro (Esquerda)
tempo_giro_desvio_4 = 0.6  # Duração (s) do 4º giro (Direita)
## --- FIM DA ALTERAÇÃO 2 ---

# 4. Parâmetros da manobra de DESVIO (Movimento para frente)
velocidade_desvio = 75.0     # Velocidade constante para os avanços no desvio
tempo_desvio_frente_1 = 0.4  # Duração (s) do primeiro avanço
tempo_desvio_frente_2 = 0.4  # Duração (s) do avanço lateral
tempo_desvio_frente_3 = 0.4  # Duração (s) do último avanço

# 5. Parâmetros do movimento para TRÁS
velocidade_re = 70.0      # Velocidade para dar ré
tempo_re = 0.2            # Duração (s) do movimento para trás

# --- Configuração Inicial ---
PWM_FREQ = 100

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Configuração dos pinos do motor
pinos_motor = [IN1_L, IN2_L, EN_L, IN1_R, IN2_R, EN_R]
for pino in pinos_motor:
    GPIO.setup(pino, GPIO.OUT)
    GPIO.output(pino, GPIO.LOW)

# Configuração dos pinos do sensor ultrassônico
GPIO.setup(PINO_TRIGGER, GPIO.OUT)
GPIO.setup(PINO_ECHO, GPIO.IN)

# --- Variáveis Globais ---
pwm_l = None
pwm_r = None

try:
    # --- Inicializa os objetos PWM ---
    pwm_l = GPIO.PWM(EN_L, PWM_FREQ)
    pwm_r = GPIO.PWM(EN_R, PWM_FREQ)
    pwm_l.start(0)
    pwm_r.start(0)

    # --- Funções de Controle ---
    def parar_motores():
        """Para completamente os motores e zera o PWM."""
        GPIO.output(IN1_L, GPIO.LOW); GPIO.output(IN2_L, GPIO.LOW)
        GPIO.output(IN1_R, GPIO.LOW); GPIO.output(IN2_R, GPIO.LOW)
        pwm_l.ChangeDutyCycle(0)
        pwm_r.ChangeDutyCycle(0)

    def executar_rampa(vel_inicial, vel_final, duracao):
        """Executa uma rampa de velocidade suave de um valor inicial para um final."""
        passos = 20
        intervalo = duracao / passos
        delta_vel = vel_inicial - vel_final
        for i in range(passos + 1):
            vel_atual = vel_inicial - (delta_vel * (i / passos))
            pwm_l.ChangeDutyCycle(vel_atual)
            pwm_r.ChangeDutyCycle(vel_atual)
            time.sleep(intervalo)
        pwm_l.ChangeDutyCycle(vel_final)
        pwm_r.ChangeDutyCycle(vel_final)

    def iniciar_movimento_frente():
        """Inicia o movimento para frente com rampa e o mantém."""
        print(f"Iniciando movimento para frente...")
        GPIO.output(IN1_L, GPIO.HIGH); GPIO.output(IN2_L, GPIO.LOW)
        GPIO.output(IN1_R, GPIO.HIGH); GPIO.output(IN2_R, GPIO.LOW)
        executar_rampa(velocidade_inicial, velocidade_cruzeiro, tempo_rampa)
        print(f"Movendo a {velocidade_cruzeiro}%...")
    
    def mover_frente_fixo(duracao):
        """Move o robô para frente com VELOCIDADE FIXA por um tempo determinado."""
        print(f"Movendo para frente (desvio) por {duracao}s a {velocidade_desvio}%...")
        GPIO.output(IN1_L, GPIO.HIGH); GPIO.output(IN2_L, GPIO.LOW)
        GPIO.output(IN1_R, GPIO.HIGH); GPIO.output(IN2_R, GPIO.LOW)
        pwm_l.ChangeDutyCycle(velocidade_desvio)
        pwm_r.ChangeDutyCycle(velocidade_desvio)
        time.sleep(duracao)
        parar_motores()

    def mover_para_tras():
        """Move o robô para trás por um tempo determinado."""
        print(f"Recuando por {tempo_re}s...")
        GPIO.output(IN1_L, GPIO.LOW); GPIO.output(IN2_L, GPIO.HIGH)
        GPIO.output(IN1_R, GPIO.LOW); GPIO.output(IN2_R, GPIO.HIGH)
        pwm_l.ChangeDutyCycle(velocidade_re)
        pwm_r.ChangeDutyCycle(velocidade_re)
        time.sleep(tempo_re)
        parar_motores()

    ## --- ALTERAÇÃO 2: FUNÇÕES DE GIRO PARAMETRIZADAS ---
    def virar_direita(duracao):
        """Executa um giro para a direita pela 'duracao' em segundos."""
        print(f"Girando para a direita por {duracao}s...")
        GPIO.output(IN1_L, GPIO.HIGH); GPIO.output(IN2_L, GPIO.LOW)
        GPIO.output(IN1_R, GPIO.LOW); GPIO.output(IN2_R, GPIO.HIGH)
        pwm_l.ChangeDutyCycle(velocidade_giro_90)
        pwm_r.ChangeDutyCycle(velocidade_giro_90)
        time.sleep(duracao)
        parar_motores()

    def virar_esquerda(duracao):
        """Executa um giro para a esquerda pela 'duracao' em segundos."""
        print(f"Girando para a esquerda por {duracao}s...")
        GPIO.output(IN1_L, GPIO.LOW); GPIO.output(IN2_L, GPIO.HIGH)
        GPIO.output(IN1_R, GPIO.HIGH); GPIO.output(IN2_R, GPIO.LOW)
        pwm_l.ChangeDutyCycle(velocidade_giro_90)
        pwm_r.ChangeDutyCycle(velocidade_giro_90)
        time.sleep(duracao)
        parar_motores()
    ## --- FIM DA ALTERAÇÃO 2 ---

    def medir_distancia():
        """Mede a distância usando o sensor HC-SR04."""
        GPIO.output(PINO_TRIGGER, True)
        time.sleep(0.00001)
        GPIO.output(PINO_TRIGGER, False)
        
        tempo_inicial = time.time()
        tempo_final = time.time()

        timeout_start = time.time()
        while GPIO.input(PINO_ECHO) == 0:
            tempo_inicial = time.time()
            if tempo_inicial - timeout_start > 0.1: return 999 

        timeout_end = time.time()
        while GPIO.input(PINO_ECHO) == 1:
            tempo_final = time.time()
            if tempo_final - timeout_end > 0.1:
                parar_motores()
                return 999

        duracao_pulso = tempo_final - tempo_inicial
        distancia = (duracao_pulso * 34300) / 2
        return distancia

    # --- Loop Principal Autônomo ---
    print("Robô iniciado. Pressione Ctrl+C para parar.")
    time.sleep(1)
    
    movendo = False

    while True:
        dist = medir_distancia()
        print(f"Distância: {dist:.2f} cm")

        if dist <= DISTANCIA_OBSTACULO:
            print("--- OBSTÁCULO DETECTADO! ---")
            parar_motores()
            movendo = False
            time.sleep(0.5)

            mover_para_tras()
            time.sleep(0.2) 

            ## --- ALTERAÇÃO 2: CHAMADAS DE GIRO COM TEMPOS INDIVIDUAIS ---
            print("Iniciando manobra de desvio...")
            
            # 1. Primeiro giro (Direita) e avanço
            virar_direita(tempo_giro_desvio_1)
            time.sleep(0.2)
            mover_frente_fixo(tempo_desvio_frente_1)
            time.sleep(0.2)
            
            # 2. Segundo giro (Esquerda) e avanço lateral
            virar_esquerda(tempo_giro_desvio_2)
            time.sleep(0.2)
            mover_frente_fixo(tempo_desvio_frente_2)
            time.sleep(0.2)
            
            # 3. Terceiro giro (Esquerda) para realinhar e avançar
            virar_esquerda(tempo_giro_desvio_3)
            time.sleep(0.2)
            mover_frente_fixo(tempo_desvio_frente_3)
            time.sleep(0.2)
            
            # 4. Quarto giro (Direita) para finalizar a manobra
            virar_direita(tempo_giro_desvio_4)
            
            print("Manobra concluída. Retomando movimento.")
            time.sleep(0.5)
            ## --- FIM DA ALTERAÇÃO 2 ---

        else:
            if not movendo:
                iniciar_movimento_frente()
                movendo = True
        
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nPrograma interrompido pelo usuário (Ctrl+C).")

finally:
    print("Parando motores e limpando os pinos GPIO.")
    if pwm_l: pwm_l.stop()
    if pwm_r: pwm_r.stop()
    parar_motores() 
    GPIO.cleanup()
