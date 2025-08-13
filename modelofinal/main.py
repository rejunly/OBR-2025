import cv2
import numpy as np
from movimento import movimentar, parar
import RPi.GPIO as GPIO

#Inicialização de camera e GPIO
cap = cv2.VideoCapture(0)  #0: webcam; 1: celular
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
GPIO.setmode(GPIO.BCM)

#Teste inicialização
if not cap.isOpened():
    print("Erro")
    exit()


while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("nao abre")
        continue

    height, width, _ = frame.shape
    roi = frame[380:440, 0:width]

    # Máscaras para preto (linha) e verde (sinal)
    Blackline = cv2.inRange(roi, (0, 0, 0), (50, 50, 50))
    Greensign = cv2.inRange(roi, (0, 65, 0), (100, 200, 100))

    kernel = np.ones((3, 3), np.uint8)
    Blackline = cv2.erode(Blackline, kernel, iterations=5)
    Blackline = cv2.dilate(Blackline, kernel, iterations=9)
    Greensign = cv2.erode(Greensign, kernel, iterations=5)
    Greensign = cv2.dilate(Greensign, kernel, iterations=9)

    # Contornos da linha e do sinal verde
    contours_blk, _ = cv2.findContours(Blackline.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours_grn, _ = cv2.findContours(Greensign.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    Greendected = False
    direction = ""

    if len(contours_blk) > 0:
        largest_blk = max(contours_blk, key=cv2.contourArea)
        x_blk, y_blk, w_blk, h_blk = cv2.boundingRect(largest_blk)
        centerx_blk = x_blk + w_blk // 2
        cv2.line(frame, (centerx_blk, 200), (centerx_blk, 250), (255, 0, 0), 3)

    if len(contours_grn) > 0:
        Greendected = True
        largest_grn = max(contours_grn, key=cv2.contourArea)
        x_grn, y_grn, w_grn, h_grn = cv2.boundingRect(largest_grn)
        centerx_grn = x_grn + w_grn // 2
        cv2.line(frame, (centerx_grn, 200), (centerx_grn, 250), (0, 255, 0), 3)

    if Greendected and len(contours_blk) > 0:
        if centerx_grn > centerx_blk:
            direction = "Curva verde à direita"
        else:
            direction = "Curva verde à esquerda"
        color = (0, 255, 0)
    elif len(contours_blk) > 0:
        if centerx_blk < width // 3:
            direction = "Curva à esquerda"
        elif centerx_blk > 2 * width // 3:
            direction = "Curva à direita"
        else:
            direction = "Seguir em frente"
        color = (255, 0, 0)
    else:
        direction = "Linha não detectada!"
        color = (0, 0, 255)

    print(f"Comando: {direction}")
    #cv2.putText(frame, direction, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    #cv2.imshow("Visão do robô", frame)
    movimentar(direction)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()
