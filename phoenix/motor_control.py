import RPi.GPIO as GPIO
import time

# --- Pinos GPIO ---
IN1_L, IN2_L, EN_L = 21, 20, 12
IN1_R, IN2_R, EN_R = 16, 19, 13

# --- Parâmetros PID --
KP, KI, KD = 0.4, 0.0, 0.05

# --- Parâmetros de Velocidade ---
BASE_SPEED = 15
INTERSECTION_SPEED = 15
TURN_SPEED = 15
GAP_SPEED = 20 

# --- Parâmetros de Manobra ---
TURN_DURATION_180 = 0.9   # Segundos para girar 180 graus
FORWARD_DURATION = 0.2    # Segundos para avançar um pouco antes de virar

# --- Variáveis de Estado Internas do Módulo ---
last_error = 0
integral = 0
pwm_L, pwm_R = None, None
last_action_time = 0
ACTION_DELAY_SECONDS = 0.5 # Delay para evitar comandos duplicados

# ===================================================================
# --- FUNÇÕES DE BAIXO NÍVEL (Controle direto dos motores) ---
# ===================================================================

def setup_motors():
    """Configura os pinos GPIO para os motores. Chame isso uma vez no início."""
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

def set_motor_speed(motor, speed):
    """Define a velocidade de um motor individual (-100 a 100)."""
    if speed > 0:
        if motor == 'L': GPIO.output(IN1_L, GPIO.HIGH); GPIO.output(IN2_L, GPIO.LOW); pwm_L.ChangeDutyCycle(min(100, speed))
        elif motor == 'R': GPIO.output(IN1_R, GPIO.HIGH); GPIO.output(IN2_R, GPIO.LOW); pwm_R.ChangeDutyCycle(min(100, speed))
    elif speed < 0:
        if motor == 'L': GPIO.output(IN1_L, GPIO.LOW); GPIO.output(IN2_L, GPIO.HIGH); pwm_L.ChangeDutyCycle(min(100, abs(speed)))
        elif motor == 'R': GPIO.output(IN1_R, GPIO.LOW); GPIO.output(IN2_R, GPIO.HIGH); pwm_R.ChangeDutyCycle(min(100, abs(speed)))
    else:
        if motor == 'L': pwm_L.ChangeDutyCycle(0)
        elif motor == 'R': pwm_R.ChangeDutyCycle(0)

def stop_all_motors():
    """Para ambos os motores."""
    set_motor_speed('L', 0)
    set_motor_speed('R', 0)

def full_stop_and_cleanup():
    """Para os motores e limpa os pinos GPIO. Chame ao sair do programa."""
    print("Módulo de Controle: Limpando pinos GPIO.")
    if pwm_L: pwm_L.stop()
    if pwm_R: pwm_R.stop()
    if GPIO.getmode() is not None:
        GPIO.cleanup()

# ===================================================================
# --- FUNÇÕES DE MÉDIO NÍVEL (Cálculos e Manobras) ---
# ===================================================================

def _calculate_pid(error):
    """Lógica interna do cálculo PID."""
    global integral, last_error
    integral += error
    derivative = error - last_error
    last_error = error
    return KP * error + KI * integral + KD * derivative

def _follow_line_pid(error, base_speed):
    """Lógica interna de seguir linha."""
    pid_output = _calculate_pid(error)
    speed_L = base_speed - pid_output
    speed_R = base_speed + pid_output
    set_motor_speed('L', max(-100, min(100, speed_L)))
    set_motor_speed('R', max(-100, min(100, speed_R)))

def _turn(direction, speed, duration):
    """Lógica interna para giros (usado apenas para Meia Volta)."""
    if direction == 'left':
        set_motor_speed('L', -speed)
        set_motor_speed('R', speed)
    else: # right
        set_motor_speed('L', speed)
        set_motor_speed('R', -speed)
    time.sleep(duration)
    stop_all_motors()

def _move_forward(speed, duration):
    """Lógica interna para mover para frente."""
    set_motor_speed('L', speed)
    set_motor_speed('R', speed)
    time.sleep(duration)
    stop_all_motors()

# ===================================================================
# --- FUNÇÃO PRINCIPAL (A única que o main vai chamar) ---
# ===================================================================

def gerenciar_movimento(acao, erro):
    """
    Recebe a ação da visão computacional e executa o movimento correspondente.
    """
    global last_action_time
    current_time = time.time()


    if acao == "Seguindo Linha":
        _follow_line_pid(erro, base_speed=BASE_SPEED)
    
    elif "Seguir em Frente" in acao:
        _follow_line_pid(erro, base_speed=INTERSECTION_SPEED)

    elif acao == "Atravessando Gap":
        _follow_line_pid(erro, base_speed=GAP_SPEED)

    elif "Curva de 90 para Direita" in acao or "Virar a Direita" in acao:
        if current_time - last_action_time < ACTION_DELAY_SECONDS: return
        print("Módulo de Controle: Executando curva de 90 graus à direita.")
        _move_forward(INTERSECTION_SPEED, 0.25)
        _turn('right', TURN_SPEED, 0.5)
        last_action_time = time.time()
        
    elif "Curva de 90 para Esquerda" in acao or "Virar a Esquerda" in acao:
        if current_time - last_action_time < ACTION_DELAY_SECONDS: return
        print("Módulo de Controle: Executando curva de 90 graus à esquerda.")
        _move_forward(INTERSECTION_SPEED, 0.25)
        _turn('left', TURN_SPEED, 0.5)
        last_action_time = time.time()
        
    elif "Meia Volta" in acao:
        if current_time - last_action_time < ACTION_DELAY_SECONDS: return
        print("Módulo de Controle: Executando meia volta.")
        _move_forward(INTERSECTION_SPEED, FORWARD_DURATION)
        _turn('right', TURN_SPEED, TURN_DURATION_180)
        last_action_time = time.time()

    elif "Procurando Linha" in acao:
        set_motor_speed('L', 35)
        set_motor_speed('R', -35)
    
    else:
        stop_all_motors()
