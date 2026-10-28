# ✍️ Air Writing — Reconnaissance de lettres dans l'air

**Interaction gestuelle en temps réel — MediaPipe · OpenCV · scikit-learn**

![Python](https://img.shields.io/badge/Python-Computer_Vision-3776AB?logo=python&logoColor=white) ![OpenCV](https://img.shields.io/badge/OpenCV-Image_Processing-5C3EE8?logo=opencv&logoColor=white) ![MediaPipe](https://img.shields.io/badge/MediaPipe-Hand_Landmarker-0097A7) ![MLP](https://img.shields.io/badge/scikit--learn-MLP-F7931E?logo=scikitlearn&logoColor=white)

**Air Writing** est un prototype de vision par ordinateur qui permet de tracer des lettres devant une webcam avec son index. Le programme transforme un geste en image, prétraite celle-ci puis utilise un réseau de neurones multicouches pour prédire une lettre de l'alphabet.

## ✨ Fonctionnalités

- Détection d'une main et de ses **21 points de repère** avec MediaPipe Hand Landmarker.
- Dessin sur un canevas virtuel lorsque **l'index est levé**.
- Validation après une **pause supérieure à une seconde**.
- Détection de la main ouverte pour réinitialiser le texte et le tracé.
- Affichage en direct de la webcam, du tracé et des lettres reconnues.
- Prétraitement OpenCV des tracés (dilatation, zone utile, redimensionnement et centrage).
- Classification des lettres **A–Z** avec `MLPClassifier` de scikit-learn.
- Génération d'exemples synthétiques avec rotation, décalage et changements d'épaisseur des lettres.

## 🧱 Pipeline technique

```text
Webcam → MediaPipe Hand Landmarker
           │
           ▼
       Analyse des gestes
           │
           ├── Index levé → Tracé sur canevas
           ├── Main ouverte → Effacement
           └── Pause > 1 s → Classification
                                  │
                                  ▼
                       Prétraitement OpenCV
                       ROI → 20×20 → 28×28
                                  │
                                  ▼
                      784 valeurs normalisées
                                  │
                                  ▼
                       MLPClassifier → A–Z
                                  │
                                  ▼
                      Texte affiché à l'écran
```

| Composant | Technologie |
| --- | --- |
| Capture et affichage | OpenCV |
| Détection gestuelle | MediaPipe Tasks |
| Calcul | NumPy |
| Classification | scikit-learn, MLP |
| Données synthétiques | Pillow, OpenCV |
| Sauvegarde du modèle | joblib |

## 🚀 Installation et lancement

**Prérequis :** Python et dépendances compatibles avec `requirements.txt`, webcam accessible et bibliothèques graphiques système nécessaires à OpenCV.

```bash
git clone https://github.com/NAZMO1/air-writing.git
cd air-writing
python -m venv .venv

# Linux/macOS
source .venv/bin/activate
# Windows PowerShell : .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

**1. Télécharger le détecteur MediaPipe :**

```bash
mkdir -p data
curl -L "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -o data/hand_landmarker.task
```

**2. Entraîner le modèle de lettres :**

```bash
python train_model.py
```

Le script génère des lettres synthétiques et sauvegarde le classifieur dans `data/letter_model.pkl`. Ces deux fichiers de modèles ne figurent pas actuellement dans le dépôt : leur préparation est indispensable avant le premier lancement.

**3. Démarrer :**

```bash
python main.py
```

| Action | Geste ou touche |
| --- | --- |
| Dessiner | Index levé, autres doigts repliés |
| Déclencher une prédiction | Pause de plus d'une seconde après un tracé |
| Réinitialiser | Main ouverte, si détectée |
| Effacer | `c` |
| Quitter | `q` |

## 📁 Organisation

```text
air-writing/
├── main.py                # Capture vidéo, gestes et affichage
├── train_model.py         # Création des données et entraînement
├── test_cam.py            # Test de la caméra
├── src/
│   ├── __init__.py
│   ├── hand_tracker.py    # Détection de main avec MediaPipe
│   └── classifier.py      # Prétraitement et classification
├── requirements.txt
└── README.md

data/                      # Dossier créé localement
├── hand_landmarker.task   # Modèle MediaPipe téléchargé
└── letter_model.pkl       # Modèle entraîné
```

## 🧠 Modèle de classification

`train_model.py` tente de produire **300 exemples par lettre**, soit jusqu'à **7 800 images** réparties sur les 26 classes. Les caractères synthétiques sont déformés puis normalisés en **28 × 28 pixels**. Le classifieur utilise deux couches cachées de **128 et 64 neurones**.

L'inférence dans `src/classifier.py` retient une prédiction si la probabilité maximale dépasse **0,25**. Ce seuil heuristique **n'est pas une mesure de précision**.

**Attention :** le modèle est entraîné sur des images de caractères typographiques transformés, et non sur un ensemble de tracés aériens capturés avec webcam. Aucune évaluation indépendante de précision n'est publiée. Les résultats réels peuvent donc être limités ou variables.

Le script d'entraînement essaie de charger la police `arial.ttf` puis utilise une police de secours si elle manque, ce qui peut influencer les données.

## ⚠️ Limites

- La reconnaissance de gestes utilise des règles géométriques simples, sensibles à l'orientation de la main.
- La classification porte sur l'image du tracé, **pas sur la trajectoire temporelle**.
- Les modèles doivent être préparés localement ; la compatibilité des versions de dépendances peut varier.
- Pas de validation quantitative sur un jeu de test indépendant dans la version actuelle.

## 🛣️ Évolutions possibles

- [ ] Collecter des tracés aériens réels et mesurer la précision sur des données séparées.
- [ ] Comparer le MLP à un réseau convolutif (CNN).
- [ ] Expérimenter une classification de trajectoires dans le temps.
- [ ] Fiabiliser la détection des gestes et les différentes orientations de main.
- [ ] Ajouter tests automatisés, captures et démonstration vidéo.

---

**Projet personnel : computer vision, traitement d'image et apprentissage automatique.**
