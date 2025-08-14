import cv2
import numpy as np
from movimento import movimentar, parar, desviar
from ultrassonico import distancia
import RPi.GPIO as GPIO

# Inicialização da câmera e GPIO
cap = cv2.VideoCapture(0)  # Use 0, 1 ou o IP da câmera do celular
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
GPIO.setmode(GPIO.BCM)

#distancia minima para desvio
DISTANCIA_MINIMA = 10 #em cm

#Teste inicialização
if not cap.isOpened():
    print("Erro: Não foi possível abrir a câmera.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("Erro: Frame não capturado.")
        continue

    # 1. Checar por obstáculos primeiro
    dist = distancia()
    print(f"Distância do obstáculo: {dist} cm")

    if dist < DISTANCIA_MINIMA:
        print("Obstáculo detectado! Iniciando desvio.")
        desviar()  # Chama a rotina de desvio
        continue   # Pula o restante do loop para checar a distância novamente

    # 2. Se não houver obstáculo, continue com a lógica de seguir a linha
    height, width, _ = frame.shape    # Região de Interesse (ROI) para análise
    roi = frame[380:440, 0:width]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Máscaras para preto (linha) e verde (sinal) ajustadas
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([179, 50, 50])
    Blackline = cv2.inRange(hsv, lower_black, upper_black)
    
    lower_green = np.array([40, 50, 50])
    upper_green = np.array([80, 255, 255])
    Greensign = cv2.inRange(hsv, lower_green, upper_green)
    
    # A máscara para vermelho permanece a mesma
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
        direction = "parar" 
        color = (0, 0, 255) 
        print(f"Comando: {direction}")
        movimentar(direction)
    
    # Lógica de controle de movimento
    else:
        # 1. Prioridade para dois contornos pretos (seguir em frente)
        # A área de cada contorno deve ser grande o suficiente
        if len(contours_blk) > 1 and all(cv2.contourArea(c) > 200 for c in contours_blk):
            direction = "seguir em frente"
            print(f"Comando: {direction}")
            movimentar(direction)
            continue # Pula o resto da lógica e reinicia o loop
    
        # 2. Detecção de dois quadrados verdes para giro de 180°
        if len(contours_grn) > 1 and all(cv2.contourArea(c) > 500 for c in contours_grn):
            direction = "girar 180"
            print(f"Comando: {direction}")
            movimentar(direction)
            continue
        
        # 2. Detecção de um quadrado verde
        if len(contours_grn) > 0 and cv2.contourArea(max(contours_grn, key=cv2.contourArea)) > 500:
            Greendected = True
            largest_grn = max(contours_grn, key=cv2.contourArea)
            x_grn, y_grn, w_grn, h_grn = cv2.boundingRect(largest_grn)
            centerx_grn = x_grn + w_grn // 2
            
            # Precisamos do contorno da linha preta para comparar posições
            if len(contours_blk) > 0:
                largest_blk = max(contours_blk, key=cv2.contourArea)
                x_blk, y_blk, w_blk, h_blk = cv2.boundingRect(largest_blk)
                centerx_blk = x_blk + w_blk // 2
                
                # Para saber se o verde está na frente ou atrás, verificamos a posição Y
                # y_grn < y_blk (verde em cima da linha, ou seja, 'atrás' na visão do robô)
                # y_grn > y_blk (verde embaixo da linha, ou seja, 'na frente' na visão do robô)
                
                                # O código corrigido ficaria assim:
                if y_grn > y_blk: # Se o quadrado verde está 'à frente' da linha (mais baixo na tela)
                    # Mantenha o movimento em frente
                    direction = "seguir em frente"
                    movimentar(direction)
                    print(f"Comando: {direction}")
                else: # Se o quadrado verde está 'atrás' da linha (mais alto na tela)
                    # Lógica de curva
                    if centerx_grn > centerx_blk:
                        direction = "Curva verde à direita"
                    else:
                        direction = "Curva verde à esquerda"
                    movimentar(direction)
                    print(f"Comando: {direction}")
            else:
                # Caso o quadrado verde seja detectado, mas a linha não.
                # A lógica de curva verde já existente serve como um bom padrão.
                if centerx_grn < width // 3:
                    direction = "Curva verde à esquerda"
                elif centerx_grn > 2 * width // 3:
                    direction = "Curva verde à direita"
                else:
                    direction = "Seguir em frente"
                movimentar(direction)
                print(f"Comando: {direction}")
                
        # 3. Lógica original de seguir a linha preta (se nenhum verde foi detectado)
        elif len(contours_blk) > 0:
            largest_blk = max(contours_blk, key=cv2.contourArea)
            x_blk, y_blk, w_blk, h_blk = cv2.boundingRect(largest_blk)
            centerx_blk = x_blk + w_blk // 2
            
            if centerx_blk < width // 3:
                direction = "Curva à esquerda"
            elif centerx_blk > 2 * width // 3:
                direction = "Curva à direita"
            else:
                direction = "Seguir em frente"
            movimentar(direction)
            print(f"Comando: {direction}")
        else:
            direction = "Linha não detectada!"
            movimentar(direction)
            print(f"Comando: {direction}")

    # Exibição e encerramento
    #cv2.putText(frame, direction, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    #cv2.imshow("Visão do robô", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

# Encerramento seguro
cap.release()
cv2.destroyAllWindows()
