import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Carregar o modelo salvo localmente
model = load_model("C:/Users/20221084010016/Documents/obr2025") #alterar quando necessário
print("Modelo carregado com sucesso!")

# Dicionário de tradução para os comandos
traducao = {
    "forward": "FRENTE",
    "left": "ESQUERDA",
    "right": "DIREITA",
    "nothing": "SEM LINHA",
    "forward-black": "SEGUIR (PRETO)",
    "verde-emfrente": "FRENTE-INTS",
    "verde-vira-direita": "DIREITA-INTS",
    "verde-vira-esquerda": "ESQUERDA-INTS",
    "curva": "CURVA"
}

# Capturar a webcam
cap = cv2.VideoCapture(2)

if not cap.isOpened():
    print("Erro ao abrir a câmera.")
else:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erro ao capturar frame da câmera.")
            break

        # Pré-processamento da imagem (agora em RGB)
        img = cv2.resize(frame, (28, 28))
        img = img.astype("float32") / 255.0
        img = img.reshape(1, 28, 28, 3)

        # Fazer a previsão
        prediction = model.predict(img)
        class_index = np.argmax(prediction)

        classes = ["forward", "left", "right", "nothing", "forward-black", "verde", "vermelho", "prateado", "interseção-t"]
        comando = traducao[classes[class_index]]

        # Exibir o comando na imagem
        cv2.putText(frame, f"Comando: {comando}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2)
        cv2.imshow("Teste ao Vivo", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
