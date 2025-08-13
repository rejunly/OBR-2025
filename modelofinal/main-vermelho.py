import cv2
import numpy as np
from movimento import movimentar, parar
import RPi.GPIO as GPIO

# Inicialização da câmera
cap = cv2.VideoCapture(0)  # Use 0, 1 ou o IP da câmera do celular
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("Erro: Não foi possível abrir a câmera.")
    exit()

# Configuração GPIO (modificado para comentar as linhas que não são usadas)
GPIO.setmode(GPIO.BCM)

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("Erro: Frame não capturado.")
        continue

    # Região de Interesse (ROI) para análise
    height, width, _ = frame.shape
    roi = frame[380:440, 0:width]
    
    # Conversão para HSV (necessário para a detecção de cores)
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Máscaras para preto (linha), verde (sinal) e vermelho (parar)
    Blackline = cv2.inRange(roi, (0, 0, 0), (50, 50, 50))
    Greensign = cv2.inRange(roi, (0, 65, 0), (100, 200, 100))

    # Máscaras para a cor vermelha em HSV (o vermelho está em duas extremidades no HSV)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)

    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)

    RedSign = cv2.bitwise_or(mask_red1, mask_red2)
    
    # Processamento de imagem
    kernel = np.ones((3, 3), np.uint8)
    Blackline = cv2.erode(Blackline, kernel, iterations=5)
    Blackline = cv2.dilate(Blackline, kernel, iterations=9)
    Greensign = cv2.erode(Greensign, kernel, iterations=5)
    Greensign = cv2.dilate(Greensign, kernel, iterations=9)
    RedSign = cv2.erode(RedSign, kernel, iterations=5)
    RedSign = cv2.dilate(RedSign, kernel, iterations=9)

    # Contornos da linha, sinal verde e sinal vermelho
    contours_blk, _ = cv2.findContours(Blackline.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours_grn, _ = cv2.findContours(Greensign.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours_red, _ = cv2.findContours(RedSign.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    Greendected = False
    RedDected = False
    direction = ""

    # Condição para detecção de vermelho
    if len(contours_red) > 0 and cv2.contourArea(max(contours_red, key=cv2.contourArea)) > 500:
        RedDected = True
        direction = "vermelho detectado" # Mudei para uma string que o "movimentar" possa entender
        color = (0, 0, 255) # Cor vermelha para o texto
        print(f"Comando: {direction}")
        movimentar(direction)

    # Lógica de controle de movimento (agora aninhada em um 'else' para priorizar o vermelho)
    else:
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
        movimentar(direction)

    # Exibição e encerramento
    #cv2.putText(frame, direction, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    #cv2.imshow("Visão do robô", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

# Encerramento seguro
cap.release()
cv2.destroyAllWindows()
