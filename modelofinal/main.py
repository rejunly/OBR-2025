from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import numpy as np
import RPi.GPIO as GPIO
from movimento import movimentar


# Configuração do GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(40, GPIO.OUT)
GPIO.output(40, GPIO.HIGH)

# Inicialização da câmera
camera = PiCamera()
camera.resolution = (640, 360)
camera.rotation = 180
rawCapture = PiRGBArray(camera, size=(640, 360))
time.sleep(0.1)

# Loop principal de captura
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    image = frame.array
    roi = image[200:250, 0:640]

    # Máscaras de cor
    Blackline = cv2.inRange(roi, (0, 0, 0), (50, 50, 50)) #calibra preto
    Greensign = cv2.inRange(roi, (0, 65, 0), (100, 200, 100)) #calibra verde
    Redsign = cv2.inRange(roi, (0, 0, 100), (80, 80, 255)) #calibra vermelho

    # Processamento morfológico
    kernel = np.ones((3, 3), np.uint8)
    Blackline = cv2.erode(Blackline, kernel, iterations=5)
    Blackline = cv2.dilate(Blackline, kernel, iterations=9)

    Greensign = cv2.erode(Greensign, kernel, iterations=5)
    Greensign = cv2.dilate(Greensign, kernel, iterations=9)

    Redsign = cv2.erode(Redsign, kernel, iterations=5)
    Redsign = cv2.dilate(Redsign, kernel, iterations=9)

    # Detecção de contornos
    contours_blk, _ = cv2.findContours(Blackline.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours_grn, _ = cv2.findContours(Greensign.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours_red, _ = cv2.findContours(Redsign.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    direction = "Linha não detectada!"
    color = (0, 0, 255)

    centerx_blk = None
    if len(contours_blk) > 0:
        largest_blk = max(contours_blk, key=cv2.contourArea)
        x_blk, y_blk, w_blk, h_blk = cv2.boundingRect(largest_blk)
        centerx_blk = x_blk + w_blk // 2
        cv2.line(image, (centerx_blk, 200), (centerx_blk, 250), (255, 0, 0), 3)

    # Verde
    if len(contours_grn) > 0 and centerx_blk is not None:
        x, y, w, h = cv2.boundingRect(max(contours_grn, key=cv2.contourArea))
        centerx_grn = x + w // 2
        cv2.line(image, (centerx_grn, 200), (centerx_grn, 250), (0, 255, 0), 3)
        if centerx_grn > centerx_blk:
            direction = "Curva verde à direita"
        else:
            direction = "Curva verde à esquerda"
        color = (0, 255, 0)

    # Vermelho
    elif len(contours_red) > 0:
        direction = "Comando vermelho detectado (ex: parar)"
        color = (0, 0, 255)

    # Sem cor especial, apenas linha preta
    elif centerx_blk is not None:
        if centerx_blk < 640 // 3:
            direction = "Curva à esquerda"
        elif centerx_blk > 2 * 640 // 3:
            direction = "Curva à direita"
        else:
            direction = "Seguir em frente"
        color = (255, 0, 0)

    print(f"Comando: {direction}")
    movimentar(direction)
    cv2.putText(image, direction, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.imshow("Visão do robô", image)

    # Limpar o buffer da câmera
    rawCapture.truncate(0)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

# Finalização
GPIO.output(40, GPIO.LOW)
cv2.destroyAllWindows()
