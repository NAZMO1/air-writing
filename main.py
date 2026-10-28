import sys
import time
import cv2
import numpy as np

from src.classifier import LetterClassifier
from src.hand_tracker import HandTracker


def run():
    # Sélection du bon pilote vidéo selon l'OS (DirectShow sous Windows, V4L2 sous Linux)
    backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_V4L2

    cap = cv2.VideoCapture(0, backend)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1, backend)

    # Repli automatique sur le pilote par défaut si besoin
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Erreur : impossible d'ouvrir la webcam.")
        return

    # Définition de la résolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    try:
        tracker = HandTracker()
        classifier = LetterClassifier()
    except (FileNotFoundError, OSError) as exc:
        print(f"Impossible de charger les modèles : {exc}")
        print("Vérifiez data/hand_landmarker.task et lancez python train_model.py pour créer data/letter_model.pkl.")
        cap.release()
        return

    canvas = None
    prev_x, prev_y = 0, 0
    current_word = ""
    last_draw_time = 0
    is_drawing = False
    pause_delay = 1.0  # Pause d'une seconde pour analyser la lettre

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Erreur de réception du flux vidéo.")
            break

        # Effet miroir horizontal
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        if canvas is None:
            canvas = np.zeros((h, w), dtype=np.uint8)

        # Détection de la main et repères
        tracker.find_hand(frame)
        landmarks = tracker.get_landmarks(frame)
        fingers = tracker.get_fingers_up(landmarks)

        if landmarks:
            idx_x, idx_y = landmarks[8]

            # 1. Écrire : index seul levé
            if fingers[1] and not any([fingers[2], fingers[3], fingers[4]]):
                cv2.circle(frame, (idx_x, idx_y), 8, (0, 0, 255), -1)

                if prev_x == 0 and prev_y == 0:
                    prev_x, prev_y = idx_x, idx_y

                cv2.line(canvas, (prev_x, prev_y), (idx_x, idx_y), 255, 12)
                prev_x, prev_y = idx_x, idx_y
                last_draw_time = time.time()
                is_drawing = True

            # 2. Main ouverte (5 doigts) : valider le mot et effacer le tracé
            elif all(fingers):
                current_word = ""
                canvas.fill(0)
                prev_x, prev_y = 0, 0
                is_drawing = False

            else:
                prev_x, prev_y = 0, 0

        else:
            prev_x, prev_y = 0, 0

        # 3. Fin de tracé détectée après la pause
        if is_drawing and (time.time() - last_draw_time > pause_delay):
            letter = classifier.predict(canvas)
            if letter:
                current_word += letter
            canvas.fill(0)
            is_drawing = False

        # Superposition du tracé vert fluo sur la caméra
        frame[canvas > 0] = (0, 255, 0)

        # Bandeau d'affichage
        cv2.rectangle(frame, (0, 0), (w, 60), (30, 30, 30), -1)
        cv2.putText(
            frame,
            f"Mot : {current_word}",
            (15, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.1,
            (255, 255, 255),
            2,
        )

        cv2.imshow("Air Writing", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("c"):
            current_word = ""
            canvas.fill(0)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()