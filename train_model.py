import os
import joblib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
from sklearn.neural_network import MLPClassifier

def generate_augmented_dataset(samples_per_letter=250):
    X = []
    y = []

    # 1 à 26 pour A à Z
    for label in range(1, 27):
        letter = chr(64 + label)
        
        for _ in range(samples_per_letter):
            # Image de base 64x64 pour dessiner proprement
            img = Image.new("L", (64, 64), color=0)
            draw = ImageDraw.Draw(img)

            # Variation de taille de police
            font_size = np.random.randint(40, 56)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()

            # Placement aléatoire avec décalage
            offset_x = np.random.randint(-6, 7)
            offset_y = np.random.randint(-6, 7)
            draw.text((16 + offset_x, 8 + offset_y), letter, fill=255, font=font)

            arr = np.array(img)

            # 1. Rotation aléatoire (-18° à +18°)
            angle = np.random.uniform(-18, 18)
            M_rot = cv2.getRotationMatrix2D((32, 32), angle, 1.0)
            arr = cv2.warpAffine(arr, M_rot, (64, 64))

            # 2. Épaississement ou amincissement aléatoire du trait
            k_size = np.random.choice([1, 2, 3])
            if k_size > 1:
                kernel = np.ones((k_size, k_size), np.uint8)
                if np.random.rand() > 0.4:
                    arr = cv2.dilate(arr, kernel, iterations=1)
                else:
                    arr = cv2.erode(arr, kernel, iterations=1)

            # 3. Recadrage strict et centrage dans 20x20 vers 28x28 (identique au classifier)
            pts = cv2.findNonZero(arr)
            if pts is not None:
                x, y_box, w, h = cv2.boundingRect(pts)
                if w > 0 and h > 0:
                    roi = arr[y_box : y_box + h, x : x + w]
                    
                    if w > h:
                        new_w = 20
                        new_h = max(int(h * (20 / w)), 1)
                    else:
                        new_h = 20
                        new_w = max(int(w * (20 / h)), 1)

                    resized = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_AREA)

                    padded = np.zeros((28, 28), dtype=np.uint8)
                    pad_x = (28 - new_w) // 2
                    pad_y = (28 - new_h) // 2
                    padded[pad_y : pad_y + new_h, pad_x : pad_x + new_w] = resized

                    # Flou léger pour simuler la fluidité du doigt
                    padded = cv2.GaussianBlur(padded, (3, 3), 0)

                    X.append(padded.flatten() / 255.0)
                    y.append(label)

    return np.array(X, dtype=np.float32), np.array(y)

def train():
    os.makedirs("data", exist_ok=True)
    print("Génération du dataset enrichi (lettres déformées, pivotées, épaissies)...")
    X, y = generate_augmented_dataset(samples_per_letter=300)
    print(f"Dataset prêt : {len(X)} images générées.")

    print("Entraînement du MLP en cours...")
    # Deux couches cachées pour mieux capturer les variations géométriques
    clf = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation="relu",
        max_iter=30,
        random_state=42
    )
    clf.fit(X, y)

    model_path = "data/letter_model.pkl"
    joblib.dump(clf, model_path)
    print(f"Modèle sauvegardé dans {model_path} avec succès.")

if __name__ == "__main__":
    train()