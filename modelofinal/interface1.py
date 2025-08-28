import cv2
import numpy as np
import pygame
import sys
import os
import motor_control 
import ultrassonico 

# ... (Mantenha todo o início do arquivo igual: Configs, Cores, Classe App __init__) ...
class App:
    def __init__(self):
        # ... (código __init__ existente) ...
        self.calib_vars = {
            # ... (variáveis de calibração existentes) ...
        }
        
        try:
            motor_control.setup_motors()
            ultrassonico.setup_sensor() # <<< INICIA O SENSOR
        except Exception as e:
            print(f'Erro ao iniciar hardware:{e}')
            self.running = False
    # ... (Mantenha o resto da classe App igual: run, handle_events, etc.) ...
# ... (Mantenha as classes TelaInicio e TelaCalibracao iguais) ...

class TelaRodada:
    def __init__(self, app):
        # ... (código __init__ existente) ...
        self.erro, self.acao, self.area = 0, "Iniciando...", "Percurso"
        self.last_erro = 0; self.gap_counter = 0; self.MAX_GAP_FRAMES = 15
        
        # <<< NOVO PARÂMETRO PARA OBSTÁCULOS >>>
        self.OBSTACLE_DISTANCE_THRESHOLD = 15 # Distância em cm para acionar o desvio
        
        # ... (código de ROIs existente) ...
        
    # ... (Mantenha as funções start e stop iguais) ...
    # ... (Mantenha a função get_zone_state igual) ...

    def update(self):
        if not self.cap or not self.cap.isOpened(): 
            self.acao = "Câmera Desconectada"; motor_control.stop_all_motors(); return
        ret, self.frame = self.cap.read()
        if not ret: 
            self.acao = "Falha na Captura"; motor_control.stop_all_motors(); return
        
        calib = self.app.calib_vars
        gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        hsv_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        
        # --- LÓGICA DE DECISÃO HIERÁRQUICA ---
        
        # 1. PRIORIDADE MÁXIMA: OBSTÁCULO
        distancia_obstaculo = ultrassonico.get_distance()
        if distancia_obstaculo < self.OBSTACLE_DISTANCE_THRESHOLD:
            self.acao = "Desviar Esquerda" # Ou "Desviar Direita" se preferir
        
        # 2. SEGUNDA PRIORIDADE: FIM DE PROVA (VERMELHO)
        elif any(self.get_zone_state(hsv_frame, gray_frame, roi, calib) == "Vermelho" for roi in self.ZONAS.values()):
            self.acao = "Fim de Pista"
        
        # 3. TERCEIRA PRIORIDADE: MANOBRAS ESPECIAIS (CURVAS, VERDE, ETC.)
        else:
            zone_states = {name: self.get_zone_state(hsv_frame, gray_frame, roi, calib) for name, roi in self.ZONAS.items()}
            if zone_states['BE'] == "Preto" and zone_states['BD'] == "Preto": self.acao = "Seguir em Frente"
            elif zone_states['BD'] == "Verde" and zone_states['BE'] == "Verde": self.acao = "Meia Volta"
            elif zone_states['CE'] == "Preto" and zone_states['CD'] == "Branco" and zone_states['CM'] == "Branco": self.acao = "Curva de 90 Esquerda"
            elif zone_states['CD'] == "Preto" and zone_states['CE'] == "Branco" and zone_states['CM'] == "Branco": self.acao = "Curva de 90 Direita"
            
            # 4. QUARTA PRIORIDADE: SEGUIR LINHA
            else:
                self.acao = "Seguindo Linha"
                roi_line = gray_frame[self.ROI_LINE_Y : self.ROI_LINE_Y + self.ROI_LINE_HEIGHT, :]
                _, mask = cv2.threshold(roi_line, calib['THRESHOLD_VALUE'], 255, cv2.THRESH_BINARY_INV)
                M = cv2.moments(mask)
                
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"]); self.erro = cx - FRAME_WIDTH // 2
                    self.last_erro = self.erro; self.gap_counter = 0
                
                # 5. ÚLTIMO RECURSO: LÓGICA DE GAP/PROCURAR LINHA
                else:
                    self.gap_counter += 1
                    if self.gap_counter < self.MAX_GAP_FRAMES:
                        self.acao = "Atravessando Gap"; self.erro = self.last_erro
                    else:
                        self.acao = "Procurando Linha"; self.erro = 0
        
        # Envia comando final para os motores
        if self.acao == "Fim de Pista":
            motor_control.stop_all_motors()
        else:
            motor_control.gerenciar_movimento(self.acao, self.erro)
        
        # Atualiza o frame para exibição (não precisa de mudanças)
        # self.frame = self.visualize_rois(self.frame.copy(), zone_states) # Opcional se zone_states for calculado

    # ... (Mantenha as funções visualize_rois, draw e handle_event iguais) ...
