import cv2
import joblib
import numpy as np


class LetterClassifier:

    def __init__(self, model_path="data/letter_model.pkl"):
        self.model = joblib.load(model_path)
        self.letters = {i: chr(64 + i) for i in range(1, 27)}

    def predict(self, canvas_gray):
        # 1. Nettoyage et dilatation pour combler les trous du tracé rapide
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(canvas_gray, kernel, iterations=1)

        pts = cv2.findNonZero(dilated)
        if pts is None:
            return ""

        x, y, w, h = cv2.boundingRect(pts)
        # Ignorer les micro-mouvements ou clics parasites
        if w < 20 or h < 20:
            return ""

        roi = dilated[y : y + h, x : x + w]

        # 2. Redimensionnement en conservant les proportions dans 20x20 pixels
        if w > h:
            new_w = 20
            new_h = max(int(h * (20 / w)), 1)
        else:
            new_h = 20
            new_w = max(int(w * (20 / h)), 1)

        resized = cv2.resize(
            roi, (new_w, new_h), interpolation=cv2.INTER_AREA
        )

        # 3. Placement au centre d'une matrice 28x28 (comme MNIST)
        padded = np.zeros((28, 28), dtype=np.uint8)
        pad_x = (28 - new_w) // 2
        pad_y = (28 - new_h) // 2
        padded[pad_y : pad_y + new_h, pad_x : pad_x + new_w] = resized

        # Léger lissage pour éviter les artefacts pixelisés
        padded = cv2.GaussianBlur(padded, (3, 3), 0)

        # Normalisation entre 0.0 et 1.0
        input_data = (padded.astype("float32") / 255.0).reshape(1, -1)

        probabilities = self.model.predict_proba(input_data)[0]
        max_idx = np.argmax(probabilities)
        confidence = probabilities[max_idx]
        predicted_class = self.model.classes_[max_idx]

        # Seuil d'acceptation plus permissif (25%)
        if confidence > 0.25:
            return self.letters.get(predicted_class, "")
        return ""