import cv2
import numpy as np
import pygame
import sys
import os
import motor_control 
import RPi.GPIO as GPIO
import time

# --- Pinos do Sensor Ultrassônico ---
GPIO_TRIGGER = 23
GPIO_ECHO = 24

# --- Configurações da Interface Gráfica ---
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800
BG_COLOR = (0, 0, 0)
# (Restante das cores e constantes da UI)
PURPLE_COLOR, GREEN_COLOR, RED_PINK_COLOR = (129, 123, 183), (92, 214, 141), (236, 112, 99)
TEXT_PURPLE_COLOR, WHITE_COLOR, GRAY_COLOR = (204, 204, 255), (255, 255, 255), (50, 50, 50)
CAMERA_DISPLAY_SIZE = (430, 242)
FRAME_WIDTH, FRAME_HEIGHT = 640, 360

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Axiom Robô Vision")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'inicio'

        # (Carregamento de assets como logo e fontes - sem alterações)
        try:
            logo_original = pygame.image.load('logo.png').convert_alpha()
            self.logo = pygame.transform.scale(logo_original, (150, 150))
            self.logo_pequeno = pygame.transform.scale(logo_original, (100, 100))
        except pygame.error:
            self.logo = pygame.Surface((150, 150), pygame.SRCALPHA)
            self.logo_pequeno = pygame.Surface((100, 100), pygame.SRCALPHA)
        try:
            self.font_grande = pygame.font.Font('Montserrat-Bold.ttf', 30)
            self.font_media_bold = pygame.font.Font('Montserrat-Bold.ttf', 26)
            self.font_media = pygame.font.Font('Montserrat-Bold.ttf', 24)
        except FileNotFoundError:
            self.font_grande = pygame.font.Font(None, 46)
            self.font_media_bold = pygame.font.Font(None, 40)
            self.font_media = pygame.font.Font(None, 36)

        self.tela_inicio = TelaInicio(self)
        self.tela_calibracao = TelaCalibracao(self)
        self.tela_rodada = TelaRodada(self)

        self.calib_vars = {
            'THRESHOLD_VALUE': 80, 'WHITE_THRESHOLD_LOWER': 200,
            'LOWER_GREEN': np.array([40, 50, 50]), 'UPPER_GREEN': np.array([80, 255, 255]),
            'LOWER_RED1': np.array([0, 70, 50]), 'UPPER_RED1': np.array([10, 255, 255]),
            'LOWER_RED2': np.array([170, 70, 50]), 'UPPER_RED2': np.array([180, 255, 255]),
            'BLACK_PERCENT_THRESH': 50.0, 'GREEN_PERCENT_THRESH': 30.0,
            'WHITE_PERCENT_THRESH': 50.0, 'RED_PERCENT_THRESH': 40.0,
        }

        try:
            motor_control.setup_motors()
            # --- Setup do Sensor Ultrassônico ---
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
            GPIO.setup(GPIO_ECHO, GPIO.IN)
            print("Sensor ultrassônico configurado.")
        except Exception as e:
            print(f'Erro na inicialização de hardware:{e}')
            self.running = False

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        self.quit_app()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if self.state == 'inicio': self.tela_inicio.handle_event(event)
            elif self.state == 'calibracao': self.tela_calibracao.handle_event(event)
            elif self.state == 'rodada': self.tela_rodada.handle_event(event)
    
    def update(self):
        if self.state == 'rodada': self.tela_rodada.update()
        elif self.state == 'calibracao': self.tela_calibracao.update()

    def draw(self):
        self.screen.fill(BG_COLOR)
        if self.state == 'inicio': self.tela_inicio.draw()
        elif self.state == 'calibracao': self.tela_calibracao.draw()
        elif self.state == 'rodada': self.tela_rodada.draw()
        pygame.display.flip()

    def quit_app(self):
        print("encerrando aplicação")
        self.tela_calibracao.stop()
        self.tela_rodada.stop()
        motor_control.full_stop_and_cleanup() # Limpa GPIO dos motores
        # GPIO.cleanup() # O cleanup dos motores já faz isso
        pygame.quit()
        sys.exit()

class TelaInicio:
    # (Sem alterações nesta classe)
    def __init__(self, app):
        self.app = app
        self.btn_iniciar = pygame.Rect(25, 250, 430, 80)
        self.btn_calibrar = pygame.Rect(25, 350, 430, 80)
        self.btn_sair = pygame.Rect(25, 450, 430, 80)

    def draw(self):
        self.app.screen.blit(self.app.logo, (SCREEN_WIDTH // 2 - 75, 50))
        pygame.draw.rect(self.app.screen, GREEN_COLOR, self.btn_iniciar, border_radius=10)
        pygame.draw.rect(self.app.screen, PURPLE_COLOR, self.btn_calibrar, border_radius=10)
        pygame.draw.rect(self.app.screen, RED_PINK_COLOR, self.btn_sair, border_radius=10)
        texto_iniciar = self.app.font_grande.render("INICIAR RODADA", True, WHITE_COLOR)
        texto_calibrar = self.app.font_grande.render("CALIBRAR", True, WHITE_COLOR)
        texto_sair = self.app.font_grande.render("SAIR", True, WHITE_COLOR)
        self.app.screen.blit(texto_iniciar, texto_iniciar.get_rect(center=self.btn_iniciar.center))
        self.app.screen.blit(texto_calibrar, texto_calibrar.get_rect(center=self.btn_calibrar.center))
        self.app.screen.blit(texto_sair, texto_sair.get_rect(center=self.btn_sair.center))
        texto_footer = self.app.font_media.render("Desenvolvido por Axiom", True, WHITE_COLOR)
        self.app.screen.blit(texto_footer, (SCREEN_WIDTH // 2 - texto_footer.get_width() // 2, 720))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_iniciar.collidepoint(event.pos):
                self.app.state = 'rodada'; self.app.tela_rodada.start()
            elif self.btn_calibrar.collidepoint(event.pos):
                self.app.state = 'calibracao'; self.app.tela_calibracao.start()
            elif self.btn_sair.collidepoint(event.pos):
                self.app.running = False


class TelaCalibracao:
    # (Sem alterações nesta classe, a calibração de vermelho já existe)
    def __init__(self, app):
        self.app = app; self.cap = None; self.frame = None; self.gray_frame = None; self.hsv_frame = None
        self.step = 0; self.btn_proximo = pygame.Rect(SCREEN_WIDTH // 2 - 125, 550, 250, 60)
        self.camera_rect = pygame.Rect((SCREEN_WIDTH - CAMERA_DISPLAY_SIZE[0]) // 2, 120, CAMERA_DISPLAY_SIZE[0], CAMERA_DISPLAY_SIZE[1])
        self.black_samples, self.green_samples, self.white_samples, self.red_samples = [], [], [], []

    def start(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not self.cap.isOpened(): print("Erro: Não foi possível abrir a webcam."); self.app.state = 'inicio'; return
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH); self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.step = 0; self.black_samples, self.green_samples, self.white_samples, self.red_samples = [], [], [], []

    def stop(self):
        if self.cap: self.cap.release(); self.cap = None

    def update(self):
        if self.cap and self.cap.isOpened():
            ret, self.frame = self.cap.read()
            if ret: self.gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY); self.hsv_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
            else: self.frame = None

    def draw(self):
        self.app.screen.blit(self.app.logo_pequeno, (SCREEN_WIDTH // 2 - 50, 10))
        if self.frame is not None:
            frame_rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            frame_pygame = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            frame_pygame = pygame.transform.scale(frame_pygame, CAMERA_DISPLAY_SIZE)
            self.app.screen.blit(frame_pygame, self.camera_rect.topleft)
        else:
            pygame.draw.rect(self.app.screen, GRAY_COLOR, self.camera_rect)
            texto_cam = self.app.font_media.render("Sem Sinal da Câmera", True, WHITE_COLOR)
            self.app.screen.blit(texto_cam, texto_cam.get_rect(center=self.camera_rect.center))

        if self.step == 0: instrucao, texto_botao = "Clique em vários pontos do Preto", "Próximo Passo"
        elif self.step == 1: instrucao, texto_botao = "Clique em vários tons de Verde", "Próximo Passo"
        elif self.step == 2: instrucao, texto_botao = "Clique em vários pontos do Branco", "Próximo Passo"
        else: instrucao, texto_botao = "Clique em vários pontos do Vermelho", "Finalizar Calibração"
        
        texto_instrucao = self.app.font_media.render(instrucao, True, TEXT_PURPLE_COLOR)
        self.app.screen.blit(texto_instrucao, (SCREEN_WIDTH // 2 - texto_instrucao.get_width() // 2, 420))
        pygame.draw.rect(self.app.screen, PURPLE_COLOR, self.btn_proximo, border_radius=10)
        texto_renderizado_botao = self.app.font_media.render(texto_botao, True, WHITE_COLOR)
        self.app.screen.blit(texto_renderizado_botao, texto_renderizado_botao.get_rect(center=self.btn_proximo.center))

    def avancar_passo(self):
        if self.step == 0 and self.black_samples: self.app.calib_vars['THRESHOLD_VALUE'] = int(np.mean(self.black_samples) + 30)
        elif self.step == 1 and self.green_samples:
            h_vals, _, _ = zip(*self.green_samples)
            h_min, h_max = max(0, min(h_vals) - 10), min(179, max(h_vals) + 10)
            self.app.calib_vars['LOWER_GREEN'] = np.array([h_min, 40, 40])
            self.app.calib_vars['UPPER_GREEN'] = np.array([h_max, 255, 255])
        elif self.step == 2 and self.white_samples: self.app.calib_vars['WHITE_THRESHOLD_LOWER'] = int(np.mean(self.white_samples) - 30)
        if self.step < 3: self.step += 1
        else:
            if self.red_samples: print("Faixas de vermelho definidas para o padrão.")
            print("Calibração finalizada."); self.stop(); self.app.state = 'inicio'
            
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN: self.avancar_passo()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_proximo.collidepoint(event.pos): self.avancar_passo()
            elif self.camera_rect.collidepoint(event.pos):
                x_gui, y_gui = event.pos
                x_frame = int((x_gui - self.camera_rect.x) * (FRAME_WIDTH / CAMERA_DISPLAY_SIZE[0]))
                y_frame = int((y_gui - self.camera_rect.y) * (FRAME_HEIGHT / CAMERA_DISPLAY_SIZE[1]))
                if self.step == 0: self.black_samples.append(self.gray_frame[y_frame, x_frame])
                elif self.step == 1: self.green_samples.append(self.hsv_frame[y_frame, x_frame])
                elif self.step == 2: self.white_samples.append(self.gray_frame[y_frame, x_frame])
                elif self.step == 3: self.red_samples.append(self.hsv_frame[y_frame, x_frame])


class TelaRodada:
    def __init__(self, app):
        self.app = app; self.cap = None; self.frame = None;
        self.camera_rect = pygame.Rect((SCREEN_WIDTH - CAMERA_DISPLAY_SIZE[0]) // 2, 100, CAMERA_DISPLAY_SIZE[0], CAMERA_DISPLAY_SIZE[1])
        self.btn_parar = pygame.Rect(25, 700, 430, 70)
        
        # Variáveis de estado
        self.erro, self.acao, self.area = 0, "Iniciando...", "Percurso"
        self.distancia_obstaculo = 999
        
        # Estado para lógica de Gaps
        self.last_erro = 0; self.gap_counter = 0; self.MAX_GAP_FRAMES = 15
        
        # --- NOVO: Estado para a manobra de desvio ---
        self.desvio_estado = 0 # 0: Inativo, 1: Desviando, 2: Contornando, 3: Retornando
        self.DISTANCIA_MIN_OBSTACULO = 15 # cm - CALIBRAR ESTE VALOR

        # ROIs
        self.ROI_CM = (262, 8, 116, 85); self.ROI_CE = (64, 131, 186, 85); self.ROI_CD = (390, 131, 186, 85)
        self.ROI_BE = (64, 275, 186, 85); self.ROI_BD = (390, 275, 186, 85)
        self.ZONAS = {'CM': self.ROI_CM, 'CE': self.ROI_CE, 'CD': self.ROI_CD, 'BE': self.ROI_BE, 'BD': self.ROI_BD}
        self.ROI_LINE_Y = 240; self.ROI_LINE_HEIGHT = 40

    def start(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not self.cap.isOpened(): print("Erro: Não foi possível abrir a webcam."); self.app.state = 'inicio'; return
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH); self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.acao, self.erro, self.last_erro, self.gap_counter = "Iniciando...", 0, 0, 0
        self.desvio_estado = 0

    def stop(self):
        motor_control.stop_all_motors()
        if self.cap: self.cap.release(); self.cap = None
        self.app.state = 'inicio'

    def medir_distancia(self):
        # Mede a distância com o sensor HC-SR04
        GPIO.output(GPIO_TRIGGER, True)
        time.sleep(0.00001)
        GPIO.output(GPIO_TRIGGER, False)
        
        tempo_inicio = time.time()
        tempo_fim = time.time()
        
        # Grava o tempo do último pulso baixo
        while GPIO.input(GPIO_ECHO) == 0:
            tempo_inicio = time.time()
            
        # Grava o tempo da chegada do pulso alto
        while GPIO.input(GPIO_ECHO) == 1:
            tempo_fim = time.time()
            
        duracao_pulso = tempo_fim - tempo_inicio
        # Velocidade do som (34300 cm/s) / 2 (ida e volta)
        distancia = (duracao_pulso * 34300) / 2
        return distancia

    def get_zone_state(self, hsv_frame, gray_frame, zone_roi, calib):
        x, y, w, h = zone_roi
        # (Lógica de detecção de cor das ROIs - sem alterações)
        roi_hsv = hsv_frame[y:y+h, x:x+w]
        roi_gray = gray_frame[y:y+h, x:x+w]
        total_pixels = w * h
        if total_pixels == 0: return "Branco"
        mask_r1 = cv2.inRange(roi_hsv, calib['LOWER_RED1'], calib['UPPER_RED1'])
        mask_r2 = cv2.inRange(roi_hsv, calib['LOWER_RED2'], calib['UPPER_RED2'])
        mask_red = mask_r1 + mask_r2
        if (cv2.countNonZero(mask_red) * 100 / total_pixels) > calib['RED_PERCENT_THRESH']: return "Vermelho"
        mask_green = cv2.inRange(roi_hsv, calib['LOWER_GREEN'], calib['UPPER_GREEN'])
        if (cv2.countNonZero(mask_green) * 100 / total_pixels) > calib['GREEN_PERCENT_THRESH']: return "Verde"
        _, mask_black = cv2.threshold(roi_gray, calib['THRESHOLD_VALUE'], 255, cv2.THRESH_BINARY_INV)
        if (cv2.countNonZero(mask_black) * 100 / total_pixels) > calib['BLACK_PERCENT_THRESH']: return "Preto"
        return "Branco"


    def update(self):
        if not self.cap or not self.cap.isOpened(): self.acao = "Câmera Desconectada"; motor_control.stop_all_motors(); return
        ret, self.frame = self.cap.read()
        if not ret: self.acao = "Falha na Captura"; motor_control.stop_all_motors(); return
        
        # --- LÓGICA DE DECISÃO HIERÁRQUICA ---
        
        # 1. MEDIR DISTÂNCIA DO OBSTÁCULO
        self.distancia_obstaculo = self.medir_distancia()

        # 2. PRIORIDADE MÁXIMA: DESVIO DE OBSTÁCULO
        if self.distancia_obstaculo < self.DISTANCIA_MIN_OBSTACULO or self.desvio_estado != 0:
            if self.desvio_estado == 0: # Iniciar desvio
                self.desvio_estado = 1
                self.acao = "Desviar Esquerda"
            elif self.desvio_estado == 1: # Já desviou, agora contorna
                self.desvio_estado = 2
                self.acao = "Contornar Obstaculo"
            elif self.desvio_estado == 2: # Já contornou, agora retorna
                self.desvio_estado = 3
                self.acao = "Retornar para Linha"
            elif self.desvio_estado == 3: # Já retornou, volta a procurar a linha
                self.desvio_estado = 0
                self.acao = "Procurando Linha" # Força a procurar a linha após o desvio
        
        # 3. SE NÃO HÁ OBSTÁCULO, USA A LÓGICA DA CÂMERA
        else:
            calib = self.app.calib_vars
            gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            hsv_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
            zone_states = {name: self.get_zone_state(hsv_frame, gray_frame, roi, calib) for name, roi in self.ZONAS.items()}
            
            # 3.1 Prioridade da Câmera: Fim de Prova (Vermelho)
            if any(state == "Vermelho" for state in zone_states.values()):
                self.acao = "Fim de Pista"
            
            # 3.2 Manobras Especiais (Curvas, Verde, etc.)
            elif zone_states['BE'] == "Preto" and zone_states['BD'] == "Preto": self.acao = "Seguir em Frente"
            elif zone_states['BD'] == "Verde" and zone_states['BE'] == "Verde": self.acao = "Meia Volta"
            elif zone_states['CE'] == "Preto" and zone_states['CD'] == "Branco" and zone_states['CM'] == "Branco": self.acao = "Curva de 90 Esquerda"
            elif zone_states['CD'] == "Preto" and zone_states['CE'] == "Branco" and zone_states['CM'] == "Branco": self.acao = "Curva de 90 Direita"
            
            # 3.3 Seguir Linha e Lógica de Gaps
            else:
                self.acao = "Seguindo Linha" # Assume seguir linha por padrão
                roi_line = gray_frame[self.ROI_LINE_Y : self.ROI_LINE_Y + self.ROI_LINE_HEIGHT, :]
                _, mask = cv2.threshold(roi_line, calib['THRESHOLD_VALUE'], 255, cv2.THRESH_BINARY_INV)
                M = cv2.moments(mask)
                
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    self.erro = cx - FRAME_WIDTH // 2
                    self.last_erro = self.erro
                    self.gap_counter = 0
                else:
                    self.gap_counter += 1
                    if self.gap_counter < self.MAX_GAP_FRAMES:
                        self.acao = "Atravessando Gap"
                        self.erro = self.last_erro
                    else:
                        self.acao = "Procurando Linha"
                        self.erro = 0
        
        # Envia comando final para os motores
        motor_control.gerenciar_movimento(self.acao, self.erro)
        self.frame = self.visualize_rois(self.frame.copy())

    def visualize_rois(self, display_frame):
        # Esta função agora não precisa mais de zone_states, pois a lógica de decisão está no update
        # Apenas desenha as caixas para debug visual
        cv2.rectangle(display_frame, (0, self.ROI_LINE_Y), (FRAME_WIDTH, self.ROI_LINE_Y + self.ROI_LINE_HEIGHT), (255, 255, 0), 2)
        for name, roi in self.ZONAS.items():
            x, y, w, h = roi
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
        return display_frame

    def draw(self):
        # (Código de desenho da UI - Adicionado display de distância)
        if self.frame is not None:
            frame_rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            frame_pygame = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            frame_pygame = pygame.transform.scale(frame_pygame, CAMERA_DISPLAY_SIZE)
            self.app.screen.blit(frame_pygame, self.camera_rect.topleft)
        else: pygame.draw.rect(self.app.screen, GRAY_COLOR, self.camera_rect)
        
        # Display de informações
        erro_text = f"ERRO: {self.erro}"
        dist_text = f"DISTANCIA: {self.distancia_obstaculo:.1f} cm" # Mostra a distância do obstáculo
        
        texto_erro = self.app.font_media_bold.render(erro_text, True, TEXT_PURPLE_COLOR)
        texto_dist = self.app.font_media_bold.render(dist_text, True, TEXT_PURPLE_COLOR)
        texto_acao_valor = self.app.font_media.render(self.acao, True, WHITE_COLOR)

        self.app.screen.blit(texto_erro, texto_erro.get_rect(centerx=SCREEN_WIDTH/2, y=400))
        self.app.screen.blit(texto_dist, texto_dist.get_rect(centerx=SCREEN_WIDTH/2, y=440))
        self.app.screen.blit(texto_acao_valor, texto_acao_valor.get_rect(centerx=SCREEN_WIDTH/2, y=500))

        pygame.draw.rect(self.app.screen, RED_PINK_COLOR, self.btn_parar, border_radius=10)
        texto_parar = self.app.font_grande.render("PARAR", True, WHITE_COLOR)
        self.app.screen.blit(texto_parar, texto_parar.get_rect(center=self.btn_parar.center))

    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and self.btn_parar.collidepoint(event.pos)) or \
           (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.stop()

if __name__ == '__main__':
    try: os.chdir(os.path.dirname(os.path.abspath(__file__)))
    except NameError: pass
    app = App()
    app.run()
