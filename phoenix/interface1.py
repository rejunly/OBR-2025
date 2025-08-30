import cv2
import numpy as np
import pygame
import sys
import os
import motor_control
import ultrassonico 

# --- Configurações da Interface Gráfica ---
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800
BG_COLOR = (0, 0, 0)

# Cores
PURPLE_COLOR = (129, 123, 183)
GREEN_COLOR = (92, 214, 141)
RED_PINK_COLOR = (236, 112, 99)
TEXT_PURPLE_COLOR = (204, 204, 255)
WHITE_COLOR = (255, 255, 255)
GRAY_COLOR = (50, 50, 50)

CAMERA_DISPLAY_SIZE = (430, 242)

# --- Configurações da Webcam---
FRAME_WIDTH = 320
FRAME_HEIGHT = 180

# --- Classe Principal da Aplicação ---
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
            print("Aviso: 'logo.png' não encontrado.")
            self.logo = pygame.Surface((150, 150), pygame.SRCALPHA)
            self.logo_pequeno = pygame.Surface((100, 100), pygame.SRCALPHA)
        
        try:
            self.font_grande = pygame.font.Font('Montserrat-Bold.ttf', 30)
            self.font_media_bold = pygame.font.Font('Montserrat-Bold.ttf', 26)
            self.font_media = pygame.font.Font('Montserrat-Bold.ttf', 24)
        except FileNotFoundError:
            print("Aviso: Fonte 'Montserrat-Bold.ttf' não encontrada.")
            self.font_grande = pygame.font.Font(None, 46)
            self.font_media_bold = pygame.font.Font(None, 40)
            self.font_media = pygame.font.Font(None, 36)

        self.tela_inicio = TelaInicio(self)
        self.tela_calibracao = TelaCalibracao(self)
        self.tela_rodada = TelaRodada(self)

        # Variáveis de Calibração com valores padrão
        self.calib_vars = {
            'THRESHOLD_VALUE': 80,
            'WHITE_THRESHOLD_LOWER': 200,
            'LOWER_GREEN': np.array([40, 50, 50]),
            'UPPER_GREEN': np.array([80, 255, 255]),
            'LOWER_RED1': np.array([0, 70, 50]),
            'UPPER_RED1': np.array([10, 255, 255]),
            'LOWER_RED2': np.array([170, 70, 50]),
            'UPPER_RED2': np.array([180, 255, 255]),
            'BLACK_PERCENT_THRESH': 50.0,
            'GREEN_PERCENT_THRESH': 30.0,
            'WHITE_PERCENT_THRESH': 50.0,
            'RED_PERCENT_THRESH': 40.0,
        }

        try:
            motor_control.setup_motors()
            ultrassonico.setup_ultrassonico()
        except Exception as e:
            print(f'Erro ao iniciar hardware:{e}')
            self.running = False

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(30)
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
        print("encerrando aplicação")
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
        if self.step == 0 and self.black_samples:
            self.app.calib_vars['THRESHOLD_VALUE'] = int(np.mean(self.black_samples) + 30)
        elif self.step == 1 and self.green_samples:
            h_vals, _, _ = zip(*self.green_samples)
            h_min, h_max = max(0, min(h_vals) - 10), min(179, max(h_vals) + 10)
            self.app.calib_vars['LOWER_GREEN'] = np.array([h_min, 40, 40])
            self.app.calib_vars['UPPER_GREEN'] = np.array([h_max, 255, 255])
        elif self.step == 2 and self.white_samples:
             self.app.calib_vars['WHITE_THRESHOLD_LOWER'] = int(np.mean(self.white_samples) - 30)

        if self.step < 3: self.step += 1
        else:
            if self.red_samples:
                print("Faixas de vermelho definidas para o padrão.")
            print("Calibração finalizada."); self.stop(); self.app.state = 'inicio'
            
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN: self.avancar_passo()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_proximo.collidepoint(event.pos): self.avancar_passo()
            elif self.camera_rect.collidepoint(event.pos):
                x_gui, y_gui = event.pos
                frame_h, frame_w, _ = self.frame.shape if self.frame is not None else (FRAME_HEIGHT, FRAME_WIDTH, 0)
                
                x_frame = int((x_gui - self.camera_rect.x) * (frame_w / CAMERA_DISPLAY_SIZE[0]))
                y_frame = int((y_gui - self.camera_rect.y) * (frame_h / CAMERA_DISPLAY_SIZE[1]))

                if 0 <= y_frame < frame_h and 0 <= x_frame < frame_w:
                    if self.step == 0 and self.gray_frame is not None: self.black_samples.append(self.gray_frame[y_frame, x_frame])
                    elif self.step == 1 and self.hsv_frame is not None: self.green_samples.append(self.hsv_frame[y_frame, x_frame])
                    elif self.step == 2 and self.gray_frame is not None: self.white_samples.append(self.gray_frame[y_frame, x_frame])
                    elif self.step == 3 and self.hsv_frame is not None: self.red_samples.append(self.hsv_frame[y_frame, x_frame])

class TelaRodada:
    def __init__(self, app):
        self.app = app; self.cap = None; self.frame = None;
        self.camera_rect = pygame.Rect((SCREEN_WIDTH - CAMERA_DISPLAY_SIZE[0]) // 2, 100, CAMERA_DISPLAY_SIZE[0], CAMERA_DISPLAY_SIZE[1])
        self.btn_parar = pygame.Rect(25, 700, 430, 70)
        self.erro, self.acao, self.area = 0, "Iniciando...", "Percurso"
        self.last_erro = 0; self.gap_counter = 0; self.MAX_GAP_FRAMES = 15
        
        self.ZONAS = {}
        self.ROI_LINE_Y = 0
        self.ROI_LINE_HEIGHT = 0
        self.frame_width = 0

    def start(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            print("Erro: Não foi possível abrir a webcam.")
            self.app.state = 'inicio'
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"AVISO: Resolução da câmara definida para {self.frame_width}x{frame_height}")
        
        # ROI Central Superior (CM)
        self.ROI_CM = (int(247/640 * self.frame_width), int(8/360 * frame_height), int(145/640 * self.frame_width), int(106/360 * frame_height))
        # ROI Centro-Esquerda (CE)
        self.ROI_CE = (int(41/640 * self.frame_width), int(120/360 * frame_height), int(232/640 * self.frame_width), int(106/360 * frame_height))
        # ROI Centro-Direita (CD)
        self.ROI_CD = (int(367/640 * self.frame_width), int(120/360 * frame_height), int(232/640 * self.frame_width), int(106/360 * frame_height))
        # ROI Base-Esquerda (BE)
        self.ROI_BE = (int(41/640 * self.frame_width), int(264/360 * frame_height), int(232/640 * self.frame_width), int(106/360 * frame_height))
        # ROI Base-Direita (BD)
        self.ROI_BD = (int(367/640 * self.frame_width), int(264/360 * frame_height), int(232/640 * self.frame_width), int(106/360 * frame_height))
        
        self.ZONAS = {'CM': self.ROI_CM, 'CE': self.ROI_CE, 'CD': self.ROI_CD, 'BE': self.ROI_BE, 'BD': self.ROI_BD}
        
        # ROI de seguimento de linha 
        self.ROI_LINE_Y = int(230/360 * frame_height) 
        self.ROI_LINE_HEIGHT = int(60/360 * frame_height)
        
        self.acao, self.erro, self.last_erro, self.gap_counter = "Iniciando...", 0, 0, 0

    def stop(self):
        motor_control.stop_all_motors()
        if self.cap: self.cap.release(); self.cap = None
        self.app.state = 'inicio'

    def get_zone_state(self, frame, zone_roi, calib):
        x, y, w, h = zone_roi
        roi_bgr = frame[y:y+h, x:x+w]
        total_pixels = w * h
        if total_pixels == 0: return "Branco"
        
        roi_hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
        roi_gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        
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
        
        # --- LÓGICA DE DESVIO DE OBSTÁCULO ---
        dist = ultrassonico.medir_distancia()
        if dist < ultrassonico.DISTANCIA_OBSTACULO:
            self.acao = "Desviando..."
            self.area = "Obstáculo"
            motor_control.gerenciar_movimento("Desviando", 0) 
            self.last_erro = 0 # Reseta o erro para recomeçar o PID
            return # Pula o resto da lógica de visão se estiver desviando
        
        # --- LÓGICA DE SEGUIMENTO DE LINHA ---
        self.area = "Percurso" # Volta para a área normal
        ret, self.frame = self.cap.read()
        if not ret: self.acao = "Falha na Captura"; motor_control.stop_all_motors(); return
        
        calib = self.app.calib_vars
        zone_states = {name: self.get_zone_state(self.frame, roi, calib) for name, roi in self.ZONAS.items()}
        
        if any(state == "Vermelho" for state in zone_states.values()):
            self.acao = "Fim de Pista"
        elif zone_states['BE'] == "Preto" and zone_states['BD'] == "Preto": self.acao = "Seguir em Frente"
        elif zone_states['BD'] == "Verde" and zone_states['BE'] == "Verde": self.acao = "Meia Volta"
        elif zone_states['CE'] == "Preto" and zone_states['CD'] == "Branco" and zone_states['CM'] == "Branco": self.acao = "Curva de 90 Esquerda"
        elif zone_states['CD'] == "Preto" and zone_states['CE'] == "Branco" and zone_states['CM'] == "Branco": self.acao = "Curva de 90 Direita"
        else:
            self.acao = "Seguindo Linha"
            gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            roi_line = gray_frame[self.ROI_LINE_Y : self.ROI_LINE_Y + self.ROI_LINE_HEIGHT, :]
            _, mask = cv2.threshold(roi_line, calib['THRESHOLD_VALUE'], 255, cv2.THRESH_BINARY_INV)
            M = cv2.moments(mask)
            
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                self.erro = (self.frame_width // 2) - cx
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
        
        if self.acao == "Fim de Pista":
            motor_control.stop_all_motors()
        else:
            motor_control.gerenciar_movimento(self.acao, self.erro)
        
        self.frame = self.visualize_rois(self.frame.copy(), zone_states)

    def visualize_rois(self, display_frame, zone_states):
        cv2.rectangle(display_frame, (0, self.ROI_LINE_Y), (self.frame_width, self.ROI_LINE_Y + self.ROI_LINE_HEIGHT), (255, 255, 0), 2)
        for name, roi in self.ZONAS.items():
            x, y, w, h = roi
            color = (255, 0, 255)
            if zone_states[name] == "Vermelho": color = (255, 0, 0)
            elif zone_states[name] == "Verde": color = (0, 255, 0)
            elif zone_states[name] == "Preto": color = (0, 0, 255)
            elif zone_states[name] == "Branco": color = (255, 255, 255)
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), color, 2)
        return display_frame

    def draw(self):
        self.app.screen.blit(self.app.logo_pequeno, (SCREEN_WIDTH // 2 - 50, 0))
        if self.frame is not None:
            frame_rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            frame_pygame = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            frame_pygame = pygame.transform.scale(frame_pygame, CAMERA_DISPLAY_SIZE)
            self.app.screen.blit(frame_pygame, self.camera_rect.topleft)
        else: pygame.draw.rect(self.app.screen, GRAY_COLOR, self.camera_rect)
        erro_text = f"ERRO: {self.erro}"
        texto_erro = self.app.font_media_bold.render(erro_text, True, TEXT_PURPLE_COLOR)
        self.app.screen.blit(texto_erro, texto_erro.get_rect(centerx=SCREEN_WIDTH/2, y=400))
        texto_acao_label = self.app.font_media_bold.render("AÇÃO:", True, TEXT_PURPLE_COLOR)
        texto_acao_valor = self.app.font_media.render(self.acao, True, TEXT_PURPLE_COLOR)
        self.app.screen.blit(texto_acao_label, texto_acao_label.get_rect(centerx=SCREEN_WIDTH/2, y=460))
        self.app.screen.blit(texto_acao_valor, texto_acao_valor.get_rect(centerx=SCREEN_WIDTH/2, y=500))
        texto_area_label = self.app.font_media_bold.render("ÁREA:", True, TEXT_PURPLE_COLOR)
        texto_area_valor = self.app.font_media.render(self.area, True, TEXT_PURPLE_COLOR)
        self.app.screen.blit(texto_area_label, texto_area_label.get_rect(centerx=SCREEN_WIDTH/2, y=560))
        self.app.screen.blit(texto_area_valor, texto_area_valor.get_rect(centerx=SCREEN_WIDTH/2, y=600))
        pygame.draw.rect(self.app.screen, PURPLE_COLOR, self.btn_parar, border_radius=10)
        texto_parar = self.app.font_grande.render("PARAR LEITURA", True, WHITE_COLOR)
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
