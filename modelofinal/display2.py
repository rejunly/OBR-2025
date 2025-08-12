from picamera2 import Picamera2
import cv2
from PIL import Image, ImageTk
import numpy as np
import tkinter as tk
from tkinter import ttk
import threading
import time
import RPi.GPIO as GPIO
from movimento import movimentar, parar

# ==== GPIO ====
GPIO.setmode(GPIO.BOARD)
GPIO.setup(40, GPIO.OUT)
GPIO.output(40, GPIO.HIGH)

# ==== Inicialização da câmera ====
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 360), "format": "RGB888"})
picam2.configure(config)
picam2.start()
time.sleep(0.1)

# ==== Interface Gráfica ====
class RoboApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Interface AXIOM")
        self.running = False
        self.tela_inicial()

    def tela_inicial(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        tk.Label(self.master, text="Bem-vindo equipe AXIOM", font=("Helvetica", 20, "bold")).pack(pady=30)
        iniciar_btn = ttk.Button(self.master, text="Iniciar Robô", command=self.iniciar_robo)
        iniciar_btn.pack(pady=20)

    def iniciar_robo(self):
        self.running = True
        self.tela_operacao()
        threading.Thread(target=self.processar_video, daemon=True).start()

    def parar_robo(self):
        self.running = False
        parar()

    def tela_operacao(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        self.label_video = tk.Label(self.master)
        self.label_video.pack()
        self.label_comando = tk.Label(self.master, text="Comando: ---", font=("Helvetica", 14))
        self.label_comando.pack(pady=10)
        parar_btn = ttk.Button(self.master, text="Parar", command=self.parar_robo)
        parar_btn.pack(pady=10)

    def processar_video(self):
        while self.running:
            image = picam2.capture_array()
            roi = image[200:250, 0:640]
            
            # Convertendo para HSV para detecção de cor mais estável
            hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)

            # Máscaras de cor
            Blackline = cv2.inRange(hsv, (0, 0, 0), (180, 255, 50))
            Greensign = cv2.inRange(hsv, (35, 40, 40), (85, 255, 255))
            Redsign = cv2.inRange(hsv, (0, 70, 50), (10, 255, 255))

            kernel = np.ones((3, 3), np.uint8)
            for mask in [Blackline, Greensign, Redsign]:
                mask = cv2.erode(mask, kernel, iterations=5)
                mask = cv2.dilate(mask, kernel, iterations=9)

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

            if len(contours_grn) > 0 and centerx_blk is not None:
                x, y, w, h = cv2.boundingRect(max(contours_grn, key=cv2.contourArea))
                centerx_grn = x + w // 2
                cv2.line(image, (centerx_grn, 200), (centerx_grn, 250), (0, 255, 0), 3)
                if centerx_grn > centerx_blk:
                    direction = "Curva verde à direita"
                else:
                    direction = "Curva verde à esquerda"
                color = (0, 255, 0)
            elif len(contours_red) > 0:
                direction = "Comando vermelho detectado (ex: parar)"
                color = (0, 0, 255)
            elif centerx_blk is not None:
                if centerx_blk < 640 // 3:
                    direction = "Curva à esquerda"
                elif centerx_blk > 2 * 640 // 3:
                    direction = "Curva à direita"
                else:
                    direction = "Seguir em frente"
                color = (255, 0, 0)

            movimentar(direction)
            self.label_comando.config(text=f"Comando: {direction}")

            cv2.putText(image, direction, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            image_pil = Image.fromarray(image)
            imgtk = ImageTk.PhotoImage(image_pil)
            self.label_video.imgtk = imgtk
            self.label_video.configure(image=imgtk)

# ==== Execução ====
root = tk.Tk()
root.geometry("800x500")
app = RoboApp(root)
root.mainloop()

GPIO.output(40, GPIO.LOW)
cv2.destroyAllWindows()
