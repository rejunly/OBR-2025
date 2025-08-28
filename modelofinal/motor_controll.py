import RPi.GPIO as GPIO
import time

# ===================================================================
# --- CONFIGURAÇÕES E CONSTANTES DE MOVIMENTO ---
# ===================================================================

# --- Pinos GPIO ---
IN1_L, IN2_L, EN_L = 21, 20, 12
IN1_R, IN2_R, EN_R = 16, 19, 13

# --- Parâmetros PID ---
KP, KI, KD = 0.4, 0.0, 0.05

# --- Parâmetros de Velocidade ---
BASE_SPEED = 20
INTERSECTION_SPEED = 15
TURN_SPEED = 25 
OBSTACLE_SPEED = 25 # Velocidade para manobras de desvio

# --- Parâmetros de Manobra (CALIBRAR ESTES VALORES) ---
TURN_DURATION_90 = 0.55   # Segundos para girar 90 graus
OBSTACLE_SIDE_DURATION = 1.0  # Segundos para andar ao lado do obstáculo
TURN_DURATION_180 = 0.9
FORWARD_DURATION = 0.2

# --- Variáveis de Estado Internas ---
last_error, integral = 0, 0
INTEGRAL_LIMIT = 200 
pwm_L, pwm_R = None, None
last_action_time = 0
ACTION_DELAY_SECONDS = 0.5

# ===================================================================
# --- FUNÇÕES DE SETUP E LIMPEZA ---
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
        print(f"Módulo de Controle: Erro no setup do RPi.GPIO: {e}")
        raise e

def full_stop_and_cleanup():
    print("Módulo de Controle: Limpando pinos GPIO.")
    if pwm_L: pwm_L.stop()
    if pwm_R: pwm_R.stop()
    if GPIO.getmode() is not None:
        GPIO.cleanup()

# ===================================================================
# --- FUNÇÕES DE MOVIMENTO DE BAIXO NÍVEL ---
# ===================================================================

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

def _turn(direction, speed, duration):
    if direction == 'left':
        set_motor_speed('L', -speed)
        set_motor_speed('R', speed)
    else: # right
        set_motor_speed('L', speed)
        set_motor_speed('R', -speed)
    time.sleep(duration)
    # Não para os motores aqui para permitir transições mais suaves

def _move_forward(speed, duration):
    set_motor_speed('L', speed)
    set_motor_speed('R', speed)
    time.sleep(duration)

# ===================================================================
# --- LÓGICA PID ---
# ===================================================================

def _calculate_pid(error):
    global integral, last_error
    integral += error
    integral = max(-INTEGRAL_LIMIT, min(INTEGRAL_LIMIT, integral))
    derivative = error - last_error
    last_error = error
    return KP * error + KI * integral + KD * derivative

def _follow_line_pid(error, base_speed):
    pid_output = _calculate_pid(error)
    speed_L = base_speed - pid_output
    speed_R = base_speed + pid_output
    set_motor_speed('L', speed_L)
    set_motor_speed('R', speed_R)

# ===================================================================
# --- FUNÇÃO PRINCIPAL DE MOVIMENTO ---
# ===================================================================

def gerenciar_movimento(acao, erro):
    global last_action_time
    current_time = time.time()
    
    # Previne que manobras especiais sejam chamadas repetidamente
    is_special_maneuver = any(sub in acao for sub in ["Curva", "Virar", "Meia Volta", "Desviar", "Contornar", "Retornar"])
    if is_special_maneuver and (current_time - last_action_time < ACTION_DELAY_SECONDS):
        return

    # --- LÓGICA DE SEGUIMENTO DE LINHA E GAPS ---
    if acao == "Seguindo Linha":
        _follow_line_pid(erro, base_speed=BASE_SPEED)
    elif "Seguir em Frente" in acao:
        _follow_line_pid(erro, base_speed=INTERSECTION_SPEED)
    elif "Atravessando Gap" in acao:
        _follow_line_pid(erro, base_speed=BASE_SPEED + 5)
    
    # --- NOVAS AÇÕES PARA DESVIO DE OBSTÁCULO ---
    elif acao == "Desviar Esquerda":
        print("Módulo de Controle: Obstáculo! Desviando para a esquerda.")
        _turn('left', TURN_SPEED, TURN_DURATION_90)
        stop_all_motors()
        last_action_time = time.time()
    
    elif acao == "Contornar Obstaculo":
        print("Módulo de Controle: Contornando obstáculo.")
        _move_forward(OBSTACLE_SPEED, OBSTACLE_SIDE_DURATION)
        stop_all_motors()
        last_action_time = time.time()
        
    elif acao == "Retornar para Linha":
        print("Módulo de Controle: Retornando para a linha.")
        _turn('right', TURN_SPEED, TURN_DURATION_90)
        stop_all_motors()
        last_action_time = time.time()

    # --- MANOBRAS DE PISTA (CURVAS, ETC) ---
    elif "Curva de 90" in acao or "Virar a" in acao:
        direction = 'left' if 'Esquerda' in acao else 'right'
        print(f"Módulo de Controle: Executando curva de 90 graus à {direction}.")
        _move_forward(INTERSECTION_SPEED, 0.25) 
        _turn(direction, TURN_SPEED, TURN_DURATION_90)
        stop_all_motors()
        last_action_time = time.time()
        
    elif "Meia Volta" in acao:
        print("Módulo de Controle: Executando meia volta.")
        _move_forward(INTERSECTION_SPEED, FORWARD_DURATION)
        _turn('right', TURN_SPEED, TURN_DURATION_180)
        stop_all_motors()
        last_action_time = time.time()

    elif "Procurando Linha" in acao:
        set_motor_speed('L', 35)
        set_motor_speed('R', -35)
    
    else: # "Iniciando...", "Fim de Pista", etc.
        stop_all_motors()
