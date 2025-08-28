import cv2
import numpy as np
import pygame
import sys
import os
import time
import motor_control 
import ultrassonico 

# --- Configurações da Interface Gráfica ---
SCREEN_WIDTH, SCREEN_HEIGHT = 480, 800
BG_COLOR = (0, 0, 0)
PURPLE_COLOR, GREEN_COLOR, RED_PINK_COLOR = (129, 123, 183), (92, 214, 141), (236, 112, 99)
TEXT_PURPLE_COLOR, WHITE_COLOR, GRAY_COLOR = (204, 204, 255), (255, 255, 255), (50, 50, 50)
CAMERA_DISPLAY_SIZE = (430, 242)

# --- Configurações da Webcam ---
FRAME_WIDTH, FRAME_HEIGHT = 640, 360

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Axiom Robô Vision")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'inicio'

        # Carrega assets
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
            ultrassonico.setup_sensor()
        except Exception as e:
            print(f'Erro fatal ao iniciar hardware: {e}')
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
        if self.state == 'calibracao': self.tela_calibracao.update()
        elif self.state == 'rodada': self.tela_rodada.update()

    def draw(self):
        self.screen.fill(BG_COLOR)
        if self.state == 'inicio': self.tela_inicio.draw()
        elif self.state == 'calibracao': self.tela_calibracao.draw()
        elif self.state == 'rodada': self.tela_rodada.draw()
        pygame.display.flip()

    def quit_app(self):
        print("Encerrando aplicação...")
        self.tela_calibracao.stop()
        self.tela_rodada.stop()
        motor_control.full_stop_and_cleanup()
        pygame.quit()
        sys.exit()

class TelaInicio:
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

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_iniciar.collidepoint(event.pos): self.app.state = 'rodada'; self.app.tela_rodada.start()
            elif self.btn_calibrar.collidepoint(event.pos): self.app.state = 'calibracao'; self.app.tela_calibracao.start()
            elif self.btn_sair.collidepoint(event.pos): self.app.running = False

class TelaCalibracao:
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
            self.app.screen.blit(pygame.transform.scale(frame_pygame, CAMERA_DISPLAY_SIZE), self.camera_rect.topleft)
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
        self.app.screen.blit(self.app.font_media.render(texto_botao, True, WHITE_COLOR), self.btn_proximo.center)

    def avancar_passo(self):
        if self.step == 0 and self.black_samples: self.app.calib_vars['THRESHOLD_VALUE'] = int(np.mean(self.black_samples) + 30)
        elif self.step == 1 and self.green_samples:
            h_vals, _, _ = zip(*self.green_samples)
            self.app.calib_vars['LOWER_GREEN'] = np.array([max(0, min(h_vals) - 10), 40, 40])
            self.app.calib_vars['UPPER_GREEN'] = np.array([min(179, max(h_vals) + 10), 255, 255])
        elif self.step == 2 and self.white_samples: self.app.calib_vars['WHITE_THRESHOLD_LOWER'] = int(np.mean(self.white_samples) - 30)
        if self.step < 3: self.step += 1
        else: print("Calibração finalizada."); self.stop(); self.app.state = 'inicio'
            
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN: self.avancar_passo()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_proximo.collidepoint(event.pos): self.avancar_passo()
            elif self.camera_rect.collidepoint(event.pos):
                x_frame = int((event.pos[0] - self.camera_rect.x) * (FRAME_WIDTH / CAMERA_DISPLAY_SIZE[0]))
                y_frame = int((event.pos[1] - self.camera_rect.y) * (FRAME_HEIGHT / CAMERA_DISPLAY_SIZE[1]))
                if self.step == 0 and self.gray_frame is not None: self.black_samples.append(self.gray_frame[y_frame, x_frame])
                elif self.step == 1 and self.hsv_frame is not None: self.green_samples.append(self.hsv_frame[y_frame, x_frame])
                elif self.step == 2 and self.gray_frame is not None: self.white_samples.append(self.gray_frame[y_frame, x_frame])
                elif self.step == 3 and self.hsv_frame is not None: self.red_samples.append(self.hsv_frame[y_frame, x_frame])

class TelaRodada:
    def __init__(self, app):
        self.app = app; self.cap = None; self.frame = None
        self.camera_rect = pygame.Rect((SCREEN_WIDTH - CAMERA_DISPLAY_SIZE[0]) // 2, 100, CAMERA_DISPLAY_SIZE[0], CAMERA_DISPLAY_SIZE[1])
        self.btn_parar = pygame.Rect(25, 700, 430, 70)
        self.erro, self.acao, self.area = 0, "Iniciando...", "Percurso"
        self.last_erro, self.gap_counter, self.MAX_GAP_FRAMES = 0, 0, 15
        self.ROI_CM = (262, 8, 116, 85); self.ROI_CE = (64, 131, 186, 85); self.ROI_CD = (390, 131, 186, 85)
        self.ROI_BE = (64, 275, 186, 85); self.ROI_BD = (390, 275, 186, 85)
        self.ZONAS = {'CM': self.ROI_CM, 'CE': self.ROI_CE, 'CD': self.ROI_CD, 'BE': self.ROI_BE, 'BD': self.ROI_BD}
        self.ROI_LINE_Y, self.ROI_LINE_HEIGHT = 240, 40
        self.obstacle_state = "Nenhum"; self.obstacle_dist_thresh = 15.0; self.last_obstacle_action_time = 0

    def start(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not self.cap.isOpened(): print("Erro: Webcam."); self.app.state = 'inicio'; return
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH); self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.acao, self.erro, self.last_erro, self.gap_counter = "Iniciando...", 0, 0, 0
        self.obstacle_state = "Nenhum"

    def stop(self):
        motor_control.stop_all_motors()
        if self.cap: self.cap.release(); self.cap = None
        self.app.state = 'inicio'

    def get_zone_state(self, hsv_frame, gray_frame, zone_roi, calib):
        x, y, w, h = zone_roi
        roi_hsv, roi_gray, total_pixels = hsv_frame[y:y+h, x:x+w], gray_frame[y:y+h, x:x+w], w*h
        if total_pixels == 0: return "Branco"
        mask_r1, mask_r2 = cv2.inRange(roi_hsv, calib['LOWER_RED1'], calib['UPPER_RED1']), cv2.inRange(roi_hsv, calib['LOWER_RED2'], calib['UPPER_RED2'])
        if (cv2.countNonZero(mask_r1 + mask_r2) * 100 / total_pixels) > calib['RED_PERCENT_THRESH']: return "Vermelho"
        if (cv2.countNonZero(cv2.inRange(roi_hsv, calib['LOWER_GREEN'], calib['UPPER_GREEN']))*100/total_pixels) > calib['GREEN_PERCENT_THRESH']: return "Verde"
        _, mask_black = cv2.threshold(roi_gray, calib['THRESHOLD_VALUE'], 255, cv2.THRESH_BINARY_INV)
        if (cv2.countNonZero(mask_black) * 100 / total_pixels) > calib['BLACK_PERCENT_THRESH']: return "Preto"
        return "Branco"

    def update(self):
        if not self.cap or not self.cap.isOpened(): self.acao = "Câmera Desconectada"; motor_control.stop_all_motors(); return
        ret, self.frame = self.cap.read()
        if not ret: self.acao = "Falha na Captura"; motor_control.stop_all_motors(); return
        
        distance = ultrassonico.get_distance()
        calib = self.app.calib_vars
        gray_frame, hsv_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY), cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        zone_states = {name: self.get_zone_state(hsv_frame, gray_frame, roi, calib) for name, roi in self.ZONAS.items()}
        
        # --- MÁQUINA DE ESTADOS HIERÁRQUICA ---
        if distance < self.obstacle_dist_thresh and self.obstacle_state == "Nenhum": self.obstacle_state = "Iniciando_Desvio"
        
        if self.obstacle_state != "Nenhum":
            current_time = time.time()
            if self.obstacle_state == "Iniciando_Desvio":
                self.acao = "Obstaculo - Iniciar Desvio"; self.obstacle_state = "Contornando"
            elif self.obstacle_state == "Contornando":
                self.acao = "Obstaculo - Contornar"; self.obstacle_state = "Realinhando"
            elif self.obstacle_state == "Realinhando":
                self.acao = "Obstaculo - Realinhar"; self.obstacle_state = "Procurando_Linha"
            elif self.obstacle_state == "Procurando_Linha":
                self.acao = "Obstaculo - Procurar Linha"; self.obstacle_state = "Nenhum" # Fim da manobra
        elif any(s == "Vermelho" for s in zone_states.values()): self.acao = "Fim de Pista"
        elif zone_states['BE']=="Preto" and zone_states['BD']=="Preto": self.acao = "Seguir em Frente"
        elif zone_states['BD']=="Verde" and zone_states['BE']=="Verde": self.acao = "Meia Volta"
        elif zone_states['CE']=="Preto" and zone_states['CD']=="Branco" and zone_states['CM']=="Branco": self.acao = "Curva de 90 Esquerda"
        elif zone_states['CD']=="Preto" and zone_states['CE']=="Branco" and zone_states['CM']=="Branco": self.acao = "Curva de 90 Direita"
        else:
            self.acao = "Seguindo Linha"
            roi_line = gray_frame[self.ROI_LINE_Y : self.ROI_LINE_Y + self.ROI_LINE_HEIGHT, :]
            _, mask = cv2.threshold(roi_line, calib['THRESHOLD_VALUE'], 255, cv2.THRESH_BINARY_INV)
            M = cv2.moments(mask)
            if M["m00"] > 0:
                self.erro = int(M["m10"] / M["m00"]) - FRAME_WIDTH // 2; self.last_erro = self.erro; self.gap_counter = 0
            else:
                self.gap_counter += 1
                if self.gap_counter < self.MAX_GAP_FRAMES: self.acao, self.erro = "Atravessando Gap", self.last_erro
                else: self.acao, self.erro = "Procurando Linha", 0
        
        if self.acao == "Fim de Pista": motor_control.stop_all_motors()
        else: motor_control.gerenciar_movimento(self.acao, self.erro)
        
        self.frame = self.visualize_rois(self.frame.copy(), zone_states)

    def visualize_rois(self, display_frame, zone_states):
        cv2.rectangle(display_frame, (0, self.ROI_LINE_Y), (FRAME_WIDTH, self.ROI_LINE_Y + self.ROI_LINE_HEIGHT), (255, 255, 0), 2)
        for name, roi in self.ZONAS.items():
            color = (255,0,255)
            if zone_states[name] == "Vermelho": color = (0, 0, 255)
            elif zone_states[name] == "Verde": color = (0, 255, 0)
            elif zone_states[name] == "Preto": color = (0, 0, 0)
            elif zone_states[name] == "Branco": color = (255, 255, 255)
            cv2.rectangle(display_frame, (roi[0], roi[1]), (roi[0]+roi[2], roi[1]+roi[3]), color, 2)
        return display_frame

    def draw(self):
        self.app.screen.blit(self.app.logo_pequeno, (SCREEN_WIDTH // 2 - 50, 0))
        if self.frame is not None:
            frame_rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            self.app.screen.blit(pygame.transform.scale(pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1)), CAMERA_DISPLAY_SIZE), self.camera_rect.topleft)
        else: pygame.draw.rect(self.app.screen, GRAY_COLOR, self.camera_rect)
        erro_text = self.app.font_media_bold.render(f"ERRO: {self.erro}", True, TEXT_PURPLE_COLOR)
        self.app.screen.blit(erro_text, erro_text.get_rect(centerx=SCREEN_WIDTH/2, y=400))
        self.app.screen.blit(self.app.font_media_bold.render("AÇÃO:", True, TEXT_PURPLE_COLOR), self.app.font_media_bold.render("AÇÃO:", True, TEXT_PURPLE_COLOR).get_rect(centerx=SCREEN_WIDTH/2, y=460))
        self.app.screen.blit(self.app.font_media.render(self.acao, True, TEXT_PURPLE_COLOR), self.app.font_media.render(self.acao, True, TEXT_PURPLE_COLOR).get_rect(centerx=SCREEN_WIDTH/2, y=500))
        pygame.draw.rect(self.app.screen, PURPLE_COLOR, self.btn_parar, border_radius=10)
        self.app.screen.blit(self.app.font_grande.render("PARAR LEITURA", True, WHITE_COLOR), self.app.font_grande.render("PARAR LEITURA", True, WHITE_COLOR).get_rect(center=self.btn_parar.center))

    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and self.btn_parar.collidepoint(event.pos)) or \
           (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE): self.stop()

if __name__ == '__main__':
    try: os.chdir(os.path.dirname(os.path.abspath(__file__)))
    except NameError: pass
    app = App()
    app.run()
