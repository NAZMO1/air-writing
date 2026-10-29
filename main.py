import sys
import time
import cv2
import numpy as np
from src.classifier import LetterClassifier
from src.hand_tracker import HandTracker
from src.gestures import StrokeTracker


def run():
    backend = cv2.CAP_DSHOW if sys.platform.startswith('win') else cv2.CAP_ANY
    cap = cv2.VideoCapture(0, backend)
    tracker = None
    try:
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(1, backend)
        if not cap.isOpened():
            print('Impossible d ouvrir la webcam.')
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        classifier = LetterClassifier()
        tracker = HandTracker()
        stroke = StrokeTracker()
        canvas = None
        word, status = '', 'Index seul : dessiner'
        pen_up_since = open_since = None
        clear_latched = False
        pending = False
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            if canvas is None or canvas.shape != (h, w):
                canvas = np.zeros((h, w), np.uint8)
                stroke.reset()
                pending = False
            now = time.monotonic()
            tracker.find_hand(frame)
            landmarks = tracker.get_landmarks(frame)
            fingers = tracker.get_fingers_up(landmarks)
            writing = bool(landmarks and fingers[1] and not any(fingers[2:]))
            opened = bool(landmarks and all(fingers))
            if opened:
                if open_since is None:
                    open_since = now
                if now-open_since >= 0.8 and not clear_latched:
                    word, status = '', 'Efface'
                    canvas.fill(0)
                    pending = False
                    stroke.reset()
                    clear_latched = True
            else:
                open_since = None
                clear_latched = False
            point = landmarks[8] if landmarks else None
            segment = stroke.update(point, writing, now, (w, h))
            if point is not None:
                cv2.circle(frame, point, 7, (0, 0, 255) if writing else (255, 200, 0), -1)
            if segment:
                cv2.line(canvas, *segment, 255, 8, cv2.LINE_AA)
                pending = True
                status = 'Trace en cours'
            if writing or opened or not landmarks:
                # Missing detections never commit an incomplete letter.
                pen_up_since = None
            elif pen_up_since is None:
                pen_up_since = now
            key = cv2.waitKey(1) & 0xff
            auto_commit = pen_up_since is not None and now-pen_up_since >= 1.2
            if pending and (auto_commit or key in (10, 13)):
                letter = classifier.predict(canvas)
                if letter:
                    word += letter
                    status = f'{letter} (score {classifier.confidence:.0%})'
                    canvas.fill(0)
                else:
                    status = 'Incertain : corriger le trace ou touche x'
                pending = False
                stroke.reset()
                pen_up_since = None
            if key == ord('q'):
                break
            if key in (ord('c'), ord('x')):
                canvas.fill(0)
                stroke.reset()
                pending = False
                pen_up_since = None
                status = 'Efface'
                if key == ord('c'):
                    word = ''
            if key in (8, 127):
                word = word[:-1]
            frame[canvas > 0] = (0, 255, 0)
            cv2.rectangle(frame, (0, 0), (w, 85), (30, 30, 30), -1)
            cv2.putText(frame, f'Mot : {word[-25:]}', (12, 32), cv2.FONT_HERSHEY_SIMPLEX, .8, (255,255,255), 2)
            cv2.putText(frame, status, (12, 60), cv2.FONT_HERSHEY_SIMPLEX, .5, (220,220,220), 1)
            cv2.putText(frame, 'Entree: valider | x: trace | c: tout | q: quitter', (12, h-12), cv2.FONT_HERSHEY_SIMPLEX, .45, (255,255,255), 1)
            cv2.imshow('Air Writing', frame)
    except (FileNotFoundError, OSError) as exc:
        print(f'Modeles indisponibles : {exc}. Consultez le README et lancez python train_model.py.')
    finally:
        if tracker is not None:
            tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    run()
