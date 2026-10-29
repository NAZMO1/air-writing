from pathlib import Path
import joblib
import numpy as np
from src.preprocessing import normalize_letter


class LetterClassifier:
    def __init__(self, model_path=None, min_confidence=0.60, min_margin=0.15):
        if model_path is None:
            model_path = Path(__file__).resolve().parents[1] / 'data/letter_model.pkl'
        self.model = joblib.load(model_path)
        self.min_confidence, self.min_margin = min_confidence, min_margin
        self.confidence = 0.0

    def predict(self, canvas_gray):
        self.confidence = 0.0
        features = normalize_letter(canvas_gray, min_extent=20)
        if features is None:
            return ''
        probabilities = self.model.predict_proba(features.reshape(1, -1))[0]
        order = np.argsort(probabilities)
        best = order[-1]
        self.confidence = float(probabilities[best])
        runner_up = float(probabilities[order[-2]]) if len(order) > 1 else 0
        if self.confidence < self.min_confidence or self.confidence-runner_up < self.min_margin:
            return ''
        label = int(self.model.classes_[best])
        return chr(64+label) if 1 <= label <= 26 else ''
