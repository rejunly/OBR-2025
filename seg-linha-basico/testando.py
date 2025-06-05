import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Carregar o modelo salvo localmente (atualize o caminho conforme necessário)
model = load_model("C:/Users/Cliente-TechNew/Downloads/IAs/ia-seg-linha-basico.h5")
print("Modelo carregado com sucesso!")

# Dicionário de tradução para os comandos
traducao = {
    "forward": "FRENTE",
    "left": "ESQUERDA",
    "nothing": "DIREITA", #parametros [sem linha e direita] invertidos
    "right": "SEM LINHA",
    "forward-black": "SEGUE RETO (dois pretos)"
}

# Capturar a webcam (o EpocCam precisa estar funcionando como webcam padrão)
cap = cv2.VideoCapture(2) #P  ARÂMETROS - 0: webcam do notebook; 1: EpocCam; 2: camera USB

if not cap.isOpened():
    print("Erro ao abrir a câmera. Verifique se a câmera está funcionando corretamente ou se o parâmetro está correto.")
else:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erro ao capturar frame da câmera.")
            break

        # Pré-processamento da imagem
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        img = cv2.resize(img, (28, 28))
        img = img.astype("float32") / 255.0
        img = img.reshape(1, 28, 28, 1)

        # Fazer a previsão
        prediction = model.predict(img)
        class_index = np.argmax(prediction)
        classes = ["forward", "left", "right", "nothing", ]
        comando = traducao[classes[class_index]]

        # Exibir o comando na imagem
        cv2.putText(frame, f"Comando: {comando}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2)
        cv2.imshow("Teste ao Vivo", frame)

        # Pressione 'q' para sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
