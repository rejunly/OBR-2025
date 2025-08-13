import RPi.GPIO as GPIO
import time

# Pinos
TRIG = 23
ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def distancia():
    GPIO.output(TRIG, False)
    time.sleep(0.000002)
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    start_time = time.time()
    pulse_start = 0
    pulse_end = 0

    timeout = start_time + 1
    
    while GPIO.input(ECHO) == 0 and time.time() < timeout:
        pulse_start = time.time()
    
    timeout = time.time() + 1
    
    while GPIO.input(ECHO) == 1 and time.time() < timeout:
        pulse_end = time.time()

    if pulse_start and pulse_end:
        pulse_duration = pulse_end - pulse_start
        dist = pulse_duration * 17150
        dist = round(dist, 2)
        return dist
    else:
        return 999  # Retorna um valor alto se não conseguir ler
        
# Teste manual
if __name__ == "__main__":
    try:
        while True:
            distancia_lida = distancia()
            print(f"Distância: {distancia_lida} cm")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Programa interrompido")
    finally:
        GPIO.cleanup()
