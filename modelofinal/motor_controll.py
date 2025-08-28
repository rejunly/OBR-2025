import RPi.GPIO as GPIO
import time

# ===================================================================
# --- CONFIGURAÇÕES E CONSTANTES DE MOVIMENTO (Tudo em um só lugar) ---
# ===================================================================

# --- Pinos GPIO ---
IN1_L, IN2_L, EN_L = 21, 20, 12
IN1_R, IN2_R, EN_R = 16, 19, 13

# --- Parâmetros PID (Valores iniciais para calibração) ---
KP, KI, KD = 0.4, 0.0, 0.05
INTEGRAL_MAX = 50 # <<< MELHORIA: Limite para evitar "Integral Windup"

# --- Parâmetros de Velocidade (Ajuste estes valores!) ---
BASE_SPEED = 15
INTERSECTION_SPEED = 15
TURN_SPEED = 15 

# --- Parâmetros de Manobra (Calibre estes valores!) ---
TURN_DURATION_180 = 0.9
FORWARD_DURATION = 0.2

# <<< NOVOS PARÂMETROS PARA DESVIO DE OBSTÁCULO >>>
OBSTACLE_TURN_DURATION = 0.4  # Tempo para virar 45-60 graus
OBSTACLE_FORWARD_DURATION = 0.7 # Tempo para avançar ao lado do obstáculo
OBSTACLE_TURN_SPEED = 20

# --- Variáveis de Estado Internas do Módulo ---
last_error = 0
integral = 0
pwm_L, pwm_R = None, None
last_action_time = 0
ACTION_DELAY_SECONDS = 0.5

# ===================================================================
# --- FUNÇÕES DE BAIXO NÍVEL (Controle direto dos motores) ---
# ===================================================================

def setup_motors():
    """Configura os pinos GPIO para os motores."""
    global pwm_L, pwm_R
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([IN1_L, IN2_L, EN_L, IN1_R, IN2_R, EN_R], GPIO.OUT)
        pwm_L = GPIO.PWM(EN_L, 1000)
        pwm_R = GPIO.PWM(EN_R, 1000)
        pwm_L.start(0)
        pwm_R.start(0)
    except Exception as e:
        print(f"Módulo de Controle: Erro no setup do RPi.GPIO: {e}")
        raise e

def set_motor_speed(motor, speed):
    """Define a velocidade de um motor individual (-100 a 100)."""
    # Limita a velocidade para garantir que não ultrapasse 100%
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

# ===================================================================
# --- FUNÇÕES DE MÉDIO NÍVEL (Cálculos e Manobras) ---
# ===================================================================

def _calculate_pid(error):
    """Lógica interna do cálculo PID com proteção contra Windup."""
    global integral, last_error
    
    integral += error
    # <<< MELHORIA: Aplica o limite no termo integral >>>
    if integral > INTEGRAL_MAX: integral = INTEGRAL_MAX
    elif integral < -INTEGRAL_MAX: integral = -INTEGRAL_MAX
        
    derivative = error - last_error
    last_error = error
    return KP * error + KI * integral + KD * derivative

def _follow_line_pid(error, base_speed):
    pid_output = _calculate_pid(error)
    speed_L = base_speed - pid_output
    speed_R = base_speed + pid_output
    set_motor_speed('L', speed_L)
    set_motor_speed('R', speed_R)

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

# ===================================================================
# --- FUNÇÃO PRINCIPAL (A única que o main vai chamar) ---
# ===================================================================
def gerenciar_movimento(acao, erro):
    """Recebe a ação da visão computacional e executa o movimento correspondente."""
    global last_action_time, integral # Reseta o integral ao mudar de ação
    current_time = time.time()

    if "Seguindo Linha" in acao or "Seguir em Frente" in acao or "Atravessando Gap" in acao:
        _follow_line_pid(erro, base_speed=BASE_SPEED)
    
    # Manobras que precisam de delay para não serem repetidas
    elif "Curva" in acao or "Virar" in acao or "Meia Volta" in acao:
        if current_time - last_action_time < ACTION_DELAY_SECONDS:
            stop_all_motors()
            return
        
        integral = 0 # Zera o integral antes de uma manobra brusca
        last_action_time = time.time()
        
        if "Curva de 90 para Direita" in aco or "Virar a Direita" in acao:
            _move_forward(INTERSECTION_SPEED, 0.25) 
            _turn('right', TURN_SPEED, 0.5)
            
        elif "Curva de 90 para Esquerda" in acao or "Virar a Esquerda" in acao:
            _move_forward(INTERSECTION_SPEED, 0.25)
            _turn('left', TURN_SPEED, 0.5)
            
        elif "Meia Volta" in acao:
            _move_forward(INTERSECTION_SPEED, FORWARD_DURATION)
            _turn('right', TURN_SPEED, TURN_DURATION_180)

    elif "Procurando Linha" in acao:
        integral = 0 # Zera o integral ao procurar a linha
        set_motor_speed('L', 35)
        set_motor_speed('R', -35)
    
    else: # Parada
        stop_all_motors()
