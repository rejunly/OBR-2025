import cv2
import numpy as np
import pygame
import sys
import os
import motor_control 

# --- Configurações da Interface Gráfica ---
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800
BG_COLOR = (0, 0, 0)

# Cores
PURPLE_COLOR = (129, 123, 183)  # #817bb7
GREEN_COLOR = (92, 214, 141)
RED_PINK_COLOR = (236, 112, 99)
TEXT_PURPLE_COLOR = (204, 204, 255)
WHITE_COLOR = (255, 255, 255)
GRAY_COLOR = (50, 50, 50)

CAMERA_DISPLAY_SIZE = (430, 242)

# --- Configurações da Webcam ---
FRAME_WIDTH = 640
FRAME_HEIGHT = 360

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
            print("Aviso: 'logo.png' não encontrado. O logo não será exibido.")
            self.logo = pygame.Surface((150, 150), pygame.SRCALPHA)
            self.logo_pequeno = pygame.Surface((100, 100), pygame.SRCALPHA)
        
        try:
            self.font_grande = pygame.font.Font('Montserrat-Bold.ttf', 30)
            self.font_media_bold = pygame.font.Font('Montserrat-Bold.ttf', 26)
            self.font_media = pygame.font.Font('Montserrat-Bold.ttf', 24)
            self.font_pequena = pygame.font.Font('Montserrat-Bold.ttf', 18)
        except FileNotFoundError:
            print("Aviso: Fonte 'Montserrat-Bold.ttf' não encontrada. Usando fonte padrão.")
            self.font_grande = pygame.font.Font(None, 46)
            self.font_media_bold = pygame.font.Font(None, 40)
            self.font_media = pygame.font.Font(None, 36)
            self.font_pequena = pygame.font.Font(None, 28)

        # Telas
        self.tela_inicio = TelaInicio(self)
        self.tela_calibracao = TelaCalibracao(self)
        self.tela_rodada = TelaRodada(self)

        # Variáveis de Calibração com valores padrão
        self.calib_vars = {
            'THRESHOLD_VALUE': 80, # Limiar para preto (quanto menor, mais escuro)
            'WHITE_THRESHOLD_LOWER': 200, # Limiar para branco (quanto maior, mais claro)
            'LOWER_GREEN': np.array([40, 50, 50]),
            'UPPER_GREEN': np.array([80, 255, 255]),
            'BLACK_PERCENT_THRESH': 50.0,
            'GREEN_PERCENT_THRESH': 30.0,
            'WHITE_PERCENT_THRESH': 50.0
        }

        #Inicia modulo dos motores
        try:
            motor_control.setup_motors()
        except Exception as e:
            print(f'Erro ao iniciar motores:{e}')
            self.running = False


    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        # Garante que, ao sair do loop, tudo seja encerrado corretamente
        self.quit_app()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.state == 'inicio':
                self.tela_inicio.handle_event(event)
            elif self.state == 'calibracao':
                self.tela_calibracao.handle_event(event)
            elif self.state == 'rodada':
                self.tela_rodada.handle_event(event)
    
    def update(self):
        if self.state == 'calibracao':
            self.tela_calibracao.update()
        elif self.state == 'rodada':
            self.tela_rodada.update()

    def draw(self):
        self.screen.fill(BG_COLOR)
        if self.state == 'inicio':
            self.tela_inicio.draw()
        elif self.state == 'calibracao':
            self.tela_calibracao.draw()
        elif self.state == 'rodada':
            self.tela_rodada.draw()
        pygame.display.flip()

    def quit_app(self):
        print("encerrando aplicação")
        self.tela_calibracao.stop()
        self.tela_rodada.stop()
        motor_control.full_stop_and_cleanup()
        pygame.quit()
        sys.exit()

# --- Tela de Início ---
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
                self.app.tela_rodada.start()
                self.app.state = 'rodada'
            elif self.btn_calibrar.collidepoint(event.pos):
                self.app.tela_calibracao.start()
                self.app.state = 'calibracao'
            elif self.btn_sair.collidepoint(event.pos):
                self.app.running = False

# --- Tela de Calibração ---
class TelaCalibracao:
    def __init__(self, app):
        self.app = app
        self.cap = None
        self.step = 0
        self.camera_rect = pygame.Rect((SCREEN_WIDTH - CAMERA_DISPLAY_SIZE[0]) // 2, 120, CAMERA_DISPLAY_SIZE[0], CAMERA_DISPLAY_SIZE[1])
        self.frame = None
        self.gray_frame = None
        self.hsv_frame = None
        self.btn_proximo = pygame.Rect(SCREEN_WIDTH // 2 - 125, 550, 250, 60)
        
        self.black_samples = []
        self.green_samples = []
        self.white_samples = []

    def start(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            print("Erro: Não foi possível abrir a webcam.")
            self.app.state = 'inicio'
            return
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.step = 0
        self.black_samples = []
        self.green_samples = []
        self.white_samples = []

    def stop(self):
        if self.cap:
            self.cap.release()
            self.cap = None

    def update(self):
        if self.cap and self.cap.isOpened():
            ret, self.frame = self.cap.read()
            if ret:
                self.gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
                self.hsv_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
            else:
                self.frame = None

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

        if self.step == 0:
            instrucao = "Clique em vários pontos do Preto"
            texto_botao = "Próximo Passo"
        elif self.step == 1:
            instrucao = "Clique em vários tons de Verde"
            texto_botao = "Próximo Passo"
        else: # self.step == 2
            instrucao = "Clique em vários pontos do Branco"
            texto_botao = "Finalizar Calibração"
        
        texto_instrucao = self.app.font_media.render(instrucao, True, TEXT_PURPLE_COLOR)
        self.app.screen.blit(texto_instrucao, (SCREEN_WIDTH // 2 - texto_instrucao.get_width() // 2, 420))
        
        pygame.draw.rect(self.app.screen, PURPLE_COLOR, self.btn_proximo, border_radius=10)
        texto_renderizado_botao = self.app.font_media.render(texto_botao, True, WHITE_COLOR)
        self.app.screen.blit(texto_renderizado_botao, texto_renderizado_botao.get_rect(center=self.btn_proximo.center))

    def avancar_passo(self):
        if self.step == 0 and self.black_samples:
            avg_black = np.mean(self.black_samples)
            self.app.calib_vars['THRESHOLD_VALUE'] = int(avg_black + 30)
            print(f"Limiar de Preto calculado: {self.app.calib_vars['THRESHOLD_VALUE']} a partir de {len(self.black_samples)} amostras.")

        elif self.step == 1 and self.green_samples:
            h_vals, s_vals, v_vals = zip(*self.green_samples)
            h_min, h_max = max(0, min(h_vals) - 10), min(179, max(h_vals) + 10)
            s_min, v_min = 40, 40
            self.app.calib_vars['LOWER_GREEN'] = np.array([h_min, s_min, v_min])
            self.app.calib_vars['UPPER_GREEN'] = np.array([h_max, 255, 255])
            print(f"Faixa de Verde calculada: {self.app.calib_vars['LOWER_GREEN']} a {self.app.calib_vars['UPPER_GREEN']}")

        if self.step < 2:
            self.step += 1
        else:
            if self.white_samples:
                avg_white = np.mean(self.white_samples)
                self.app.calib_vars['WHITE_THRESHOLD_LOWER'] = int(avg_white - 30)
                print(f"Limiar de Branco calculado: {self.app.calib_vars['WHITE_THRESHOLD_LOWER']} a partir de {len(self.white_samples)} amostras.")
            
            print("Calibração finalizada. Retornando ao menu.")
            self.stop()
            self.app.state = 'inicio'
            
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.avancar_passo()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_proximo.collidepoint(event.pos):
                self.avancar_passo()
            
            elif self.camera_rect.collidepoint(event.pos):
                x_gui, y_gui = event.pos
                x_frame = int((x_gui - self.camera_rect.x) * (FRAME_WIDTH / CAMERA_DISPLAY_SIZE[0]))
                y_frame = int((y_gui - self.camera_rect.y) * (FRAME_HEIGHT / CAMERA_DISPLAY_SIZE[1]))

                if self.step == 0 and self.gray_frame is not None:
                    pixel_gray = self.gray_frame[y_frame, x_frame]
                    self.black_samples.append(pixel_gray)
                    print(f"Amostra de Preto adicionada: {pixel_gray}. Total: {len(self.black_samples)}")
                
                elif self.step == 1 and self.hsv_frame is not None:
                    hsv_val = self.hsv_frame[y_frame, x_frame]
                    self.green_samples.append(hsv_val)
                    print(f"Amostra de Verde adicionada: {hsv_val}. Total: {len(self.green_samples)}")

                elif self.step == 2 and self.gray_frame is not None:
                    pixel_gray = self.gray_frame[y_frame, x_frame]
                    self.white_samples.append(pixel_gray)
                    print(f"Amostra de Branco adicionada: {pixel_gray}. Total: {len(self.white_samples)}")

# --- Tela da Rodada / Leitura de Linha ---
class TelaRodada:
    def __init__(self, app):
        self.app = app
        self.cap = None
        self.frame = None
        self.camera_rect = pygame.Rect((SCREEN_WIDTH - CAMERA_DISPLAY_SIZE[0]) // 2, 100, CAMERA_DISPLAY_SIZE[0], CAMERA_DISPLAY_SIZE[1])
        self.btn_parar = pygame.Rect(25, 700, 430, 70)
        
        self.erro, self.acao, self.area = 0, "Iniciando...", "Percurso"
        
        # Zonas de Interesse (ROI)
        self.ROI_CM = (int(262.47), int(8.34), int(116.07), int(85.3))
        self.ROI_CE = (int(64), int(131), int(186), int(85))
        self.ROI_CD = (int(390), int(131), int(186), int(85))
        self.ROI_BE = (int(64), int(275), int(186), int(85))
        self.ROI_BD = (int(390), int(275), int(186), int(85))
        self.ZONAS = {'CM': self.ROI_CM, 'CE': self.ROI_CE, 'CD': self.ROI_CD, 'BE': self.ROI_BE, 'BD': self.ROI_BD}
        
        # Zona de Seguimento de Linha (ZSL)
        self.ROI_LINE_Y = 240
        self.ROI_LINE_HEIGHT = 20

    def start(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            print("Erro: Não foi possível abrir a webcam.")
            self.app.state = 'inicio'
            return
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.acao, self.erro = "Procurando Linha", 0

    def stop(self):
        # <<< ADIÇÃO IMPORTANTE >>>
        # Garante que os motores parem imediatamente ao sair da tela da rodada
        motor_control.stop_all_motors()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.app.state = 'inicio'

    def get_zone_state(self, hsv_frame, gray_frame, zone_roi, calib):
        x, y, w, h = int(zone_roi[0]), int(zone_roi[1]), int(zone_roi[2]), int(zone_roi[3])
        total_pixels = w * h
        if total_pixels == 0: return "Branco"

        roi_hsv = hsv_frame[y:y+h, x:x+w]
        roi_gray = gray_frame[y:y+h, x:x+w]

        # 1. Checa por Verde (maior prioridade)
        mask_green = cv2.inRange(roi_hsv, calib['LOWER_GREEN'], cal.get('UPPER_GREEN'))
        if (cv2.countNonZero(mask_green) / total_pixels) * 100 > calib['GREEN_PERCENT_THRESH']:
            return "Verde"

        # 2. Checa por Branco
        _, mask_white = cv2.threshold(roi_gray, calib['WHITE_THRESHOLD_LOWER'], 255, cv2.THRESH_BINARY)
        if (cv2.countNonZero(mask_white) / total_pixels) * 100 > calib['WHITE_PERCENT_THRESH']:
            return "Branco"

        # 3. Checa por Preto
        _, mask_black = cv2.threshold(roi_gray, calib['THRESHOLD_VALUE'], 255, cv2.THRESH_BINARY_INV)
        if (cv2.countNonZero(mask_black) / total_pixels) * 100 > calib['BLACK_PERCENT_THRESH']:
            return "Preto"
            
        # 4. Default
        return "Branco"

    def update(self):
        if not self.cap or not self.cap.isOpened():
            self.acao = "Câmera Desconectada"
            motor_control.stop_all_motors() # Para o robô se a câmera falhar
            return
            
        ret, self.frame = self.cap.read()
        if not ret:
            self.frame = None
            self.acao = "Falha na Captura"
            motor_control.stop_all_motors() # Para o robô se a captura falhar
            return
        
        # --- PASSO 1: LÓGICA DE VISÃO PARA DEFINIR AÇÃO E ERRO ---
        calib = self.app.calib_vars
        display_frame = self.frame.copy()
        gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        hsv_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)

        zone_states = {name: self.get_zone_state(hsv_frame, gray_frame, roi, calib) for name, roi in self.ZONAS.items()}
        cm, ce, cd, be, bd = zone_states['CM'], zone_states['CE'], zone_states['CD'], zone_states['BE'], zone_states['BD']

        # Regras de Decisão
        if be == "Preto" and bd == "Preto": self.acao = "Seguir em Frente (Intersecao T/Cruzamento)"
        elif bd == "Verde" and be == "Verde" and ce == "Preto" and cd == "Preto": self.acao = "Meia Volta"
        elif bd == "Branco" and be == "Verde" and ce == "Preto" and cd == "Preto": self.acao = "Virar a Esquerda (Obstaculo Direita)"
        elif bd == "Verde" and be == "Branco" and ce == "Preto" and cd == "Preto": self.acao = "Virar a Direita (Obstaculo Esquerda)"
        elif bd == "Branco" and be == "Verde" and ce == "Preto" and cd == "Branco": self.acao = "Virar a Esquerda"
        elif bd == "Verde" and be == "Branco" and ce == "Branco" and cd == "Preto": self.acao = "Virar a Direita"
        elif ce == "Preto" and cd == "Branco" and be == "Branco" and bd == "Branco" and cm == "Branco": self.acao = "Curva de 90 para Esquerda"
        elif cd == "Preto" and ce == "Branco" and be == "Branco" and bd == "Branco" and cm == "Branco": self.acao = "Curva de 90 para Direita"
        else: self.acao = "Seguindo Linha"

        # Lógica de Seguimento de Linha
        # --- Lógica de Seguimento de Linha NOVA E MELHORADA ---
        self.erro = 0 # Reseta o erro
        if "Seguindo Linha" in self.acao or "Seguir em Frente" in self.acao:
            # Aumente a altura da ROI para uma leitura mais estável
            self.ROI_LINE_HEIGHT = 40 # Aumentado de 20 para 40
            roi_line_slice = gray_frame[self.ROI_LINE_Y : self.ROI_LINE_Y + self.ROI_LINE_HEIGHT, 0 : FRAME_WIDTH]
            
            # Binariza a imagem para encontrar a linha preta
            _, mask_line = cv2.threshold(roi_line_slice, calib['THRESHOLD_VALUE'], 255, cv2.THRESH_BINARY_INV)
            
            # Calcula os momentos da imagem binarizada
            M = cv2.moments(mask_line)
            
            if M["m00"] > 0: # Verifica se algum pixel preto foi encontrado
                # Calcula o centro de massa de todos os pixels pretos
                cx = int(M["m10"] / M["m00"])
                # Calcula o erro em relação ao centro da imagem
                self.erro = cx - FRAME_WIDTH // 2
            else:
                # Se nenhuma linha for encontrada, aciona a busca
                self.acao = "Procurando Linha..."
        
        # --- PASSO 2: DELEGAR O MOVIMENTO PARA O MÓDULO DE CONTROLE ---
        # <<< ESTA É A ADIÇÃO PRINCIPAL >>>
        # A mágica da modularização está nesta única linha.
        motor_control.gerenciar_movimento(self.acao, self.erro)


        # Visualização (desenha no frame da câmera)
        cv2.rectangle(display_frame, (0, self.ROI_LINE_Y), (FRAME_WIDTH, self.ROI_LINE_Y + self.ROI_LINE_HEIGHT), (255, 255, 0), 2)
        for name, roi in self.ZONAS.items():
            x, y, w, h = int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3])
            color = (0, 0, 0)
            if zone_states[name] == "Verde": color = (0, 255, 0)
            elif zone_states[name] == "Preto": color = (0, 0, 255)
            elif zone_states[name] == "Branco": color = (255, 255, 255)
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), color, 2)
        
        self.frame = display_frame

    def draw(self):
        self.app.screen.blit(self.app.logo_pequeno, (SCREEN_WIDTH // 2 - 50, 0))

        if self.frame is not None:
            frame_rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            frame_pygame = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            frame_pygame = pygame.transform.scale(frame_pygame, CAMERA_DISPLAY_SIZE)
            self.app.screen.blit(frame_pygame, self.camera_rect.topleft)
        else:
            pygame.draw.rect(self.app.screen, GRAY_COLOR, self.camera_rect)

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
        if event.type == pygame.MOUSEBUTTONDOWN and self.btn_parar.collidepoint(event.pos):
            self.stop()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.stop()

# --- Ponto de Entrada do Programa ---
if __name__ == '__main__':
    # Garante que os assets sejam encontrados se o script for executado de outro diretório
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        pass # __file__ não está definido em alguns ambientes, como IDLE
    
    app = App()
    app.run()
