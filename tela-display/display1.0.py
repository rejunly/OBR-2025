import tkinter as tk
import random

class RoboInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Interface do Robô OBR")
        self.root.geometry("800x480")

        self.calibrated_values = {}  # Ex: {'S1_Preto': (R, G, B)}
        self.rgb_labels = {}         # Referência visual dos valores
        self.current_page = None

        self.setup_page_calibracao()

    def setup_page_calibracao(self):
        self.clear_page()

        tk.Label(self.root, text="Calibração dos Sensores", font=("Arial", 20)).pack(pady=10)

        cores = ["Preto", "Branco", "Vermelho", "Prateado", "Verde"]

        for i in range(4):
            sensor_id = f"S{i+1}"
            sensor_frame = tk.LabelFrame(self.root, text=f"Sensor {sensor_id}", padx=10, pady=10)
            sensor_frame.pack(pady=5)

            for cor in cores:
                btn = tk.Button(sensor_frame, text=f"Calibrar {cor}", width=13,
                                command=lambda s=sensor_id, c=cor: self.calibrar_sensor(s, c))
                btn.pack(side=tk.LEFT, padx=2)

                lbl = tk.Label(sensor_frame, text="R: - G: - B: -", width=15)
                lbl.pack(side=tk.LEFT, padx=5)
                self.rgb_labels[f"{sensor_id}_{cor}"] = lbl

        tk.Button(self.root, text="Salvar Calibração", command=self.salvar_calibracao, bg="green", fg="white").pack(pady=10)
        tk.Button(self.root, text="Ir para Leitura", command=self.setup_page_leitura).pack()

    def calibrar_sensor(self, sensor_id, cor):
        # Simulação da leitura RGB
        rgb = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.calibrated_values[f"{sensor_id}_{cor}"] = rgb

        # Atualiza na tela
        label = self.rgb_labels.get(f"{sensor_id}_{cor}")
        if label:
            label.config(text=f"R: {rgb[0]} G: {rgb[1]} B: {rgb[2]}")

    def salvar_calibracao(self):
        # Aqui você pode salvar em arquivo, banco, etc., se quiser
        pass  # Nenhuma ação terminal

    def setup_page_leitura(self):
        self.clear_page()

        tk.Label(self.root, text="Leitura em Tempo Real", font=("Arial", 20)).pack(pady=10)

        self.estado_label = tk.Label(self.root, text="Estado: Seguindo linha", font=("Arial", 16))
        self.estado_label.pack()

        self.movimento_label = tk.Label(self.root, text="Movimento: Reto", font=("Arial", 16))
        self.movimento_label.pack()

        self.sensores_frame = tk.Frame(self.root)
        self.sensores_frame.pack(pady=10)

        self.sensor_labels = []
        for i in range(4):
            lbl = tk.Label(self.sensores_frame, text=f"S{i+1}: ---", font=("Arial", 14))
            lbl.grid(row=0, column=i, padx=10)
            self.sensor_labels.append(lbl)

        self.ultrassonico_label = tk.Label(self.root, text="Sensor Ultrassônico: 20 cm", font=("Arial", 16))
        self.ultrassonico_label.pack()

        tk.Button(self.root, text="Voltar para Calibração", command=self.setup_page_calibracao).pack(pady=20)

        self.root.after(1000, self.update_leituras)

    def update_leituras(self):
        # Atualizações simuladas
        estados = ["Seguindo linha", "Desvio de obstáculo", "Resgate"]
        movimentos = ["Reto", "Curva à esquerda", "Curva à direita", "Parado"]
        cores = ["Preto", "Branco", "Vermelho", "Prateado", "Verde"]

        self.estado_label.config(text=f"Estado: {random.choice(estados)}")
        self.movimento_label.config(text=f"Movimento: {random.choice(movimentos)}")

        for i, lbl in enumerate(self.sensor_labels):
            cor = random.choice(cores)
            lbl.config(text=f"S{i+1}: {cor}")

        distancia = random.randint(3, 100)
        self.ultrassonico_label.config(text=f"Sensor Ultrassônico: {distancia} cm")

        self.root.after(1000, self.update_leituras)

    def clear_page(self):
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = RoboInterface(root)
    root.mainloop()
