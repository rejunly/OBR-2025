import RPi.GPIO as GPIO
import time

# ... (Toda a configuração de Pinos, PID, Velocidade, etc., permanece a mesma) ...
# --- Pinos GPIO ---
IN1_L, IN2_L, EN_L = 21, 20, 12
IN1_R, IN2_R, EN_R = 16, 19, 13
# --- Parâmetros PID ---
KP, KI, KD = 0.4, 0.0, 0.05
# --- Parâmetros de Velocidade ---
BASE_SPEED = 15
INTERSECTION_SPEED = 15
TURN_SPEED = 15
# --- Variáveis de Estado ---
last_error, integral = 0, 0
INTEGRAL_LIMIT = 200
pwm_L, pwm_R = None, None
last_action_time = 0
ACTION_DELAY_SECONDS = 0.5

# <<< NOVAS CONSTANTES PARA O DESVIO DE OBSTÁCULO >>>
# Calibre estes valores!
OBSTACLE_MANEUVER_SPEED = 20 # Velocidade durante a manobra de desvio
OBSTACLE_REVERSE_DURATION = 0.3  # Tempo para recuar
OBSTACLE_TURN_DURATION = 0.5     # Tempo para girar 90 graus
OBSTACLE_FORWARD_DURATION = 0.8  # Tempo para andar ao lado do obstáculo
OBSTACLE_SEARCH_DURATION = 0.5   # Tempo para avançar procurando a linha

# ... (Funções de baixo e médio nível: setup_motors, set_motor_speed, stop_all_motors,
#  full_stop_and_cleanup, _calculate_pid, _follow_line_pid, _turn, _move_forward
#  permanecem as mesmas da versão anterior) ...

# (Cole aqui as funções inalteradas da sua versão anterior para economizar espaço)
def setup_motors():
    global pwm_L, pwm_R
    try:
        GPIO.setmode(GPIO.BCM); GPIO.setwarnings(False)
        GPIO.setup([IN1_L, IN2_L, EN_L, IN1_R, IN2_R, EN_R], GPIO.OUT)
        pwm_L = GPIO.PWM(EN_L, 1000); pwm_R = GPIO.PWM(EN_R, 1000)
        pwm_L.start(0); pwm_R.start(0)
        print("Módulo de Controle: Motores configurados.")
    except Exception as e: print(f"Módulo de Controle: Erro no setup: {e}"); raise e
def set_motor_speed(motor, speed):
    speed = max(-100, min(100, speed))
    if speed > 0:
        if motor == 'L': GPIO.output(IN1_L, GPIO.HIGH); GPIO.output(IN2_L, GPIO.LOW); pwm_L.ChangeDutyCycle(speed)
        elif motor == 'R': GPIO.output(IN1_R, GPIO.HIGH); GPIO.output(IN2_R, GPIO.LOW); pwm_R.ChangeDutyCycle(speed)
    elif speed < 0:
        if motor == 'L': GPIO.output(IN1_L, GPIO.LOW); GPIO.output(IN2_L, GPIO.HIGH); pwm_L.ChangeDutyCycle(abs(speed))
        elif motor == 'R': GPIO.output(IN1_R, GPIO.LOW); GPIO.output(IN2_R, GPIO.HIGH); pwm_R.ChangeDutyCycle(abs(speed))
    else:
        if motor == 'L': pwm_L.ChangeDutyCycle(0)
        elif motor == 'R': pwm_R.ChangeDutyCycle(0)
def stop_all_motors(): set_motor_speed('L', 0); set_motor_speed('R', 0)
def full_stop_and_cleanup():
    print("Módulo de Controle: Limpando pinos GPIO.")
    if pwm_L: pwm_L.stop()
    if pwm_R: pwm_R.stop()
    if GPIO.getmode() is not None: GPIO.cleanup()
def _calculate_pid(error):
    global integral, last_error
    integral += error; integral = max(-INTEGRAL_LIMIT, min(INTEGRAL_LIMIT, integral))
    derivative = error - last_error; last_error = error
    return KP * error + KI * integral + KD * derivative
def _follow_line_pid(error, base_speed):
    pid_output = _calculate_pid(error)
    set_motor_speed('L', base_speed - pid_output)
    set_motor_speed('R', base_speed + pid_output)
def _turn(direction, speed, duration):
    if direction == 'left': set_motor_speed('L', -speed); set_motor_speed('R', speed)
    else: set_motor_speed('L', speed); set_motor_speed('R', -speed)
    time.sleep(duration); stop_all_motors()
def _move_forward(speed, duration):
    set_motor_speed('L', speed); set_motor_speed('R', speed)
    time.sleep(duration); stop_all_motors()
    
# ===================================================================
# --- FUNÇÃO PRINCIPAL (A única que o main vai chamar) ---
# ===================================================================

def gerenciar_movimento(acao, erro):
    """
    Recebe a ação da visão e sensores e executa o movimento correspondente.
    """
    global last_action_time
    current_time = time.time()

    is_special_maneuver = any(sub in acao for sub in ["Curva", "Virar", "Meia Volta", "Obstaculo"])
    if is_special_maneuver and (current_time - last_action_time < ACTION_DELAY_SECONDS):
        stop_all_motors()
        return

    # --- LÓGICA DE MOVIMENTO ---
    if "Seguindo Linha" in acao:
        _follow_line_pid(erro, base_speed=BASE_SPEED)
    elif "Seguir em Frente" in acao:
        _follow_line_pid(erro, base_speed=INTERSECTION_SPEED)
    elif "Atravessando Gap" in acao:
        _follow_line_pid(erro, base_speed=BASE_SPEED + 5)

    # <<< NOVA LÓGICA DE MOVIMENTOS PARA DESVIO DE OBSTÁCULO >>>
    elif acao == "Obstaculo - Recuar":
        print("Módulo de Controle: Obstáculo detectado. Recuando.")
        # Anda de ré para criar espaço
        set_motor_speed('L', -OBSTACLE_MANEUVER_SPEED)
        set_motor_speed('R', -OBSTACLE_MANEUVER_SPEED)
        time.sleep(OBSTACLE_REVERSE_DURATION)
        stop_all_motors()
        last_action_time = time.time()
    
    elif acao == "Obstaculo - Virar Direita":
        print("Módulo de Controle: Virando para desviar.")
        _turn('right', OBSTACLE_MANEUVER_SPEED, OBSTACLE_TURN_DURATION)
        last_action_time = time.time()

    elif acao == "Obstaculo - Contornar":
        print("Módulo de Controle: Contornando obstáculo.")
        _move_forward(OBSTACLE_MANEUVER_SPEED, OBSTACLE_FORWARD_DURATION)
        last_action_time = time.time()
        
    elif acao == "Obstaculo - Virar Esquerda":
        print("Módulo de Controle: Realinhando com a pista.")
        _turn('left', OBSTACLE_MANEUVER_SPEED, OBSTACLE_TURN_DURATION)
        last_action_time = time.time()
        
    elif acao == "Obstaculo - Procurar Linha":
        print("Módulo de Controle: Procurando a linha após desvio.")
        _move_forward(OBSTACLE_MANEUVER_SPEED, OBSTACLE_SEARCH_DURATION)
        last_action_time = time.time()
        
    # --- MANOBRAS ESPECIAIS JÁ EXISTENTES ---
    elif "Curva de 90" in acao or "Virar a" in acao:
        # A lógica de curvas permanece a mesma
        if "Direita" in acao:
            _move_forward(INTERSECTION_SPEED, 0.25) 
            _turn('right', TURN_SPEED, 0.5)
        else: # Esquerda
            _move_forward(INTERSECTION_SPEED, 0.25)
            _turn('left', TURN_SPEED, 0.5)
        last_action_time = time.time()
        
    elif "Meia Volta" in acao:
        _move_forward(INTERSECTION_SPEED, 0.2)
        _turn('right', TURN_SPEED, 0.9)
        last_action_time = time.time()

    elif "Procurando Linha" in acao:
        set_motor_speed('L', 35)
        set_motor_speed('R', -35)
    
    else:
        stop_all_motors()
