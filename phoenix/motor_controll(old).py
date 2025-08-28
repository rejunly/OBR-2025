import RPi.GPIO as GPIO
import time

# ===================================================================
# --- CONFIGURAÇÕES E CONSTANTES DE MOVIMENTO ---
# ===================================================================

# --- Pinos GPIO ---
IN1_L, IN2_L, EN_L = 21, 20, 12
IN1_R, IN2_R, EN_R = 16, 19, 13

# --- Parâmetros PID (Calibre estes!) ---
KP, KI, KD = 0.4, 0.0, 0.05

# --- Parâmetros de Velocidade (Calibre estes!) ---
BASE_SPEED = 20
INTERSECTION_SPEED = 20
TURN_SPEED = 25

# --- Constantes para Manobras Especiais (Calibre estes!) ---
TURN_DURATION_90_DEGREES = 0.5 # Tempo para girar 90 graus em intersecções
TURN_DURATION_180_DEGREES = 0.9
FORWARD_BEFORE_TURN_DURATION = 0.25

# --- Constantes para o Desvio de Obstáculo (Calibre estes!) ---
OBSTACLE_MANEUVER_SPEED = 25
OBSTACLE_REVERSE_DURATION = 0.3
OBSTACLE_TURN_DURATION = 0.5
OBSTACLE_FORWARD_DURATION = 0.8
OBSTACLE_SEARCH_DURATION = 0.5

# --- Variáveis de Estado Internas ---
last_error, integral = 0, 0
INTEGRAL_LIMIT = 200
pwm_L, pwm_R = None, None
last_action_time = 0
ACTION_DELAY_SECONDS = 0.5

# ===================================================================
# --- FUNÇÕES DE CONTROLE DE MOTORES ---
# ===================================================================

def setup_motors():
    global pwm_L, pwm_R
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([IN1_L, IN2_L, EN_L, IN1_R, IN2_R, EN_R], GPIO.OUT)
        pwm_L = GPIO.PWM(EN_L, 1000)
        pwm_R = GPIO.PWM(EN_R, 1000)
        pwm_L.start(0)
        pwm_R.start(0)
        print("Módulo de Controle: Motores configurados.")
    except Exception as e:
        print(f"Módulo de Controle: Erro no setup: {e}")
        raise e

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

def stop_all_motors():
    set_motor_speed('L', 0)
    set_motor_speed('R', 0)

def full_stop_and_cleanup():
    print("Módulo de Controle: Limpando pinos GPIO.")
    if pwm_L: pwm_L.stop()
    if pwm_R: pwm_R.stop()
    if GPIO.getmode() is not None:
        GPIO.cleanup()

def _calculate_pid(error):
    global integral, last_error
    integral += error
    integral = max(-INTEGRAL_LIMIT, min(INTEGRAL_LIMIT, integral))
    derivative = error - last_error
    last_error = error
    return KP * error + KI * integral + KD * derivative

def _follow_line_pid(error, base_speed):
    pid_output = _calculate_pid(error)
    set_motor_speed('L', base_speed - pid_output)
    set_motor_speed('R', base_speed + pid_output)

def _turn(direction, speed, duration):
    if direction == 'left': set_motor_speed('L', -speed); set_motor_speed('R', speed)
    else: set_motor_speed('L', speed); set_motor_speed('R', -speed)
    time.sleep(duration)
    stop_all_motors()

def _move_forward(speed, duration):
    set_motor_speed('L', speed)
    set_motor_speed('R', speed)
    time.sleep(duration)
    stop_all_motors()
    
def _move_backward(speed, duration):
    set_motor_speed('L', -speed)
    set_motor_speed('R', -speed)
    time.sleep(duration)
    stop_all_motors()

# ===================================================================
# --- FUNÇÃO PRINCIPAL DE MOVIMENTO ---
# ===================================================================

def gerenciar_movimento(acao, erro):
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

    # --- LÓGICA DE DESVIO DE OBSTÁCULO ---
    elif acao == "Obstaculo - Iniciar Desvio":
        print("Módulo de Controle: Obstáculo. Recuando e virando.")
        _move_backward(OBSTACLE_MANEUVER_SPEED, OBSTACLE_REVERSE_DURATION)
        _turn('right', OBSTACLE_MANEUVER_SPEED, OBSTACLE_TURN_DURATION)
        last_action_time = time.time()
    
    elif acao == "Obstaculo - Contornar":
        print("Módulo de Controle: Contornando obstáculo.")
        _move_forward(OBSTACLE_MANEUVER_SPEED, OBSTACLE_FORWARD_DURATION)
        last_action_time = time.time()
        
    elif acao == "Obstaculo - Realinhar":
        print("Módulo de Controle: Realinhando com a pista.")
        _turn('left', OBSTACLE_MANEUVER_SPEED, OBSTACLE_TURN_DURATION)
        last_action_time = time.time()
        
    elif acao == "Obstaculo - Procurar Linha":
        print("Módulo de Controle: Procurando a linha após desvio.")
        _move_forward(OBSTACLE_MANEUVER_SPEED, OBSTACLE_SEARCH_DURATION)
        last_action_time = time.time()
        
    # --- MANOBRAS ESPECIAIS ---
    elif "Curva de 90" in acao or "Virar a" in acao:
        direction = 'right' if "Direita" in acao else 'left'
        _move_forward(INTERSECTION_SPEED, FORWARD_BEFORE_TURN_DURATION)
        _turn(direction, TURN_SPEED, TURN_DURATION_90_DEGREES)
        last_action_time = time.time()
        
    elif "Meia Volta" in acao:
        _move_forward(INTERSECTION_SPEED, 0.2)
        _turn('right', TURN_SPEED, TURN_DURATION_180_DEGREES)
        last_action_time = time.time()

    elif "Procurando Linha" in acao:
        set_motor_speed('L', 35)
        set_motor_speed('R', -35)
    
    else:
        stop_all_motors()
