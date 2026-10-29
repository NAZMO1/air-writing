"""Reproducible synthetic baseline; validation is NOT webcam accuracy."""
import argparse
from pathlib import Path
import cv2
import joblib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score
from threadpoolctl import threadpool_limits
from src.preprocessing import normalize_letter

ROOT = Path(__file__).resolve().parent


def available_fonts():
    candidates = ['arial.ttf', 'DejaVuSans.ttf', 'DejaVuSansMono.ttf',
                  'C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/calibri.ttf',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
                  '/System/Library/Fonts/Supplemental/Arial.ttf']
    fonts = []
    for path in candidates:
        try:
            font = ImageFont.truetype(path, 48)
            if font.path not in [f.path for f in fonts]:
                fonts.append(font)
        except OSError:
            pass
    if not fonts:
        raise RuntimeError('Installez une police TrueType Arial ou DejaVu Sans avant l entrainement.')
    return fonts


def generate_augmented_dataset(samples_per_letter=250, seed=42):
    rng = np.random.default_rng(seed)
    fonts = available_fonts()
    X, y = [], []
    for label in range(1, 27):
        for _ in range(samples_per_letter):
            # Mix typography and single-line lettering, closer to finger strokes.
            arr = np.zeros((96, 96), np.uint8)
            letter = chr(64+label)
            if rng.random() < .5:
                font = fonts[int(rng.integers(len(fonts)))]
                img = Image.fromarray(arr)
                draw = ImageDraw.Draw(img)
                box = draw.textbbox((0, 0), letter, font=font)
                draw.text(((96-box[2]+box[0])/2-box[0], (96-box[3]+box[1])/2-box[1]), letter, font=font, fill=255)
                arr = np.array(img)
            else:
                face = int(rng.choice([cv2.FONT_HERSHEY_SIMPLEX, cv2.FONT_HERSHEY_PLAIN, cv2.FONT_HERSHEY_DUPLEX]))
                size, _ = cv2.getTextSize(letter, face, 2, 2)
                cv2.putText(arr, letter, ((96-size[0])//2, (96+size[1])//2), face, 2, 255, int(rng.integers(1, 4)), cv2.LINE_AA)
            matrix = cv2.getRotationMatrix2D((48,48), float(rng.uniform(-15,15)), float(rng.uniform(.85,1.1)))
            matrix[0,1] += rng.uniform(-.12,.12)
            arr = cv2.warpAffine(arr, matrix, (96,96))
            if rng.random() < .35:
                arr = cv2.dilate(arr, np.ones((2,2), np.uint8))
            features = normalize_letter(arr)
            if features is not None:
                X.append(features)
                y.append(label)
    return np.asarray(X, np.float32), np.asarray(y)


def train(samples=300, iterations=80):
    X, y = generate_augmented_dataset(samples)
    train_x, test_x, train_y, test_y = train_test_split(X, y, test_size=.2, stratify=y, random_state=42)
    clf = MLPClassifier(hidden_layer_sizes=(128,64), max_iter=iterations,
                        early_stopping=True, n_iter_no_change=8, random_state=42)
    with threadpool_limits(limits=2):
        clf.fit(train_x, train_y)
        score = accuracy_score(test_y, clf.predict(test_x))
    print(f'Validation synthetique separee : {score:.1%} (ne mesure pas la precision webcam).')
    (ROOT/'data').mkdir(exist_ok=True)
    joblib.dump(clf, ROOT/'data/letter_model.pkl')
    print('Modele sauvegarde. Relancez python main.py.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=300)
    parser.add_argument('--iterations', type=int, default=80)
    args = parser.parse_args()
    if args.samples < 10 or args.iterations < 1:
        parser.error('--samples doit etre >= 10 et --iterations >= 1')
    train(args.samples, args.iterations)
