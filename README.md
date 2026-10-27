# Air Writing

Application de reconnaissance d'écriture aérienne en temps réel en Python.

## Fonctionnalités
- Détection des repères de la main en temps réel via MediaPipe Tasks.
- Tracé dynamique à l'index avec OpenCV.
- Classification de lettres majuscules via un réseau de neurones (Scikit-learn MLP).

## Installation
```bash
pip install -r requirements.txt
python train_model.py
python main.py