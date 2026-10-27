# Air Writing — Reconnaissance d'Écriture Aérienne en Temps Réel

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green.svg)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Tasks-orange.svg)](https://developers.google.com/mediapipe)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-MLP-yellow.svg)](https://scikit-learn.org/)

Système interactif de vision par ordinateur et d'apprentissage automatique permettant d'écrire des lettres dans les airs à l'aide de l'index devant une webcam, puis de les transcrire en texte en temps réel.

---

## Fonctionnalités

- **Suivi gestuel temps réel** : tracking précis des 21 repères biométriques de la main via la nouvelle API **MediaPipe Tasks**.
- **Contrôle gestuel sans contact** :
  - **Index levé seul** : écriture sur le canvas virtuel.
  - **Main ouverte (5 doigts levés)** : réinitialisation du tracé et du mot en cours.
  - **Pause de 1 seconde** : validation automatique et classification du caractère tracé.
- **Pipeline de classification robuste** :
  - Extraction de la zone d'intérêt (*bounding box*) et préservation du ratio d'aspect.
  - Centrage dans une matrice $28 \times 28$ pixels (format standard MNIST).
  - Prédiction par réseau de neurones multicouches (**MLPClassifier**).
- **Entraînement enrichi par Data Augmentation** : génération synthétique avec rotations aléatoires, variations d'échelles, translations et opérations morphologiques (dilatation/érosion).

---

## Architecture du Projet

```text
air-writing/
│
├── data/
│   ├── hand_landmarker.task   # Modèle de détection de main MediaPipe
│   └── letter_model.pkl       # Modèle Scikit-learn entraîné
│
├── src/
│   ├── __init__.py
│   ├── hand_tracker.py        # Wrapper MediaPipe Tasks & extraction des gestes
│   └── classifier.py          # Prétraitement d'image et inférence MLP
│
├── main.py                    # Boucle principale temps réel OpenCV
├── train_model.py             # Script d'entraînement avec data augmentation
├── requirements.txt           # Dépendances du projet
└── README.md
Pipeline Technique
Flux Vidéo (Webcam)
       │
       ▼
[MediaPipe HandLandmarker] ──► Détection des repères (Landmark 8 : Index)
       │
       ▼
[Contrôle d'États] ──────────► Détection du geste (Index seul / Main ouverte)
       │
       ▼
[Canvas Virtuel] ────────────► Tracé continu en pixels blancs (masque binaire)
       │
       ▼ (Pause > 1s)
[Prétraitement OpenCV] ──────► Boîte englobante, redimensionnement 20x20, centrage 28x28, flou
       │
       ▼
[MLPClassifier] ─────────────► Vecteur aplati (784 features) ──► Lettre prédite (A-Z)
Installation et Utilisation
1. Cloner le dépôt
Bash
git clone [https://github.com/NAZMO1/air-writing.git](https://github.com/NAZMO1/air-writing.git)
cd air-writing
2. Créer un environnement virtuel et installer les dépendances
Bash
python -m venv venv
# Sur Linux / WSL :
source venv/bin/activate
# Sur Windows (PowerShell) :
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
3. Télécharger le modèle de main MediaPipe
Bash
mkdir -p data
curl -o data/hand_landmarker.task -L [https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task)
4. Entraîner le modèle de classification
Bash
python train_model.py
5. Lancer l'application
Bash
python main.py
Appuyez sur c pour effacer l'écran manuellement.

Appuyez sur q pour quitter.

Défis Techniques Résolus
Migration d'API MediaPipe : intégration directe de l'API mediapipe.tasks.python.vision.HandLandmarker pour pérenniser la compatibilité avec les versions récentes de Python.

Prétraitement d'Image Dynamique : normalisation des tracés aériens (souvent tremblants et d'échelles variées) via une boîte englobante dynamique et un redimensionnement avec conservation de proportions (aspect ratio padding).

Gestion Matérielle & Flux Vidéo : configuration des backends de capture OpenCV (cv2.CAP_DSHOW sous Windows, cv2.CAP_V4L2 sous Linux) et résolution des dépendances graphiques natives OpenGL/GLES (libGLESv2).

Améliorations Futures
[ ] Entraînement sur le dataset manuscrit EMNIST Letters pour supporter des styles d'écriture encore plus variés.

[ ] Remplacement du classifieur MLP par un réseau convolutif (CNN) sous PyTorch.

[ ] Reconnaissance dynamique par trajectoire séquentielle (coordonnées temporelles avec LSTM / Dynamic Time Warping).