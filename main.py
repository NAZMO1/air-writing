import sys
import time
import cv2
import numpy as np
from src.classifier import LetterClassifier
from src.hand_tracker import HandTracker
from src.gestures import StrokeTracker
from src.words import WordComposer, ascii_text
from src.speech import SpeechPlayer


def run():
    backend = cv2.CAP_DSHOW if sys.platform.startswith('win') else cv2.CAP_ANY
    cap = cv2.VideoCapture(0, backend)
    tracker = None
    speaker = SpeechPlayer()
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
        composer = WordComposer()
        status = 'Index seul : dessiner'
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
                    composer.clear()
                    status = 'Efface'
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
                    composer.add_letter(letter)
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
                    composer.clear()
            if key in (8, 127):
                composer.backspace()
            if key == ord('l'):
                composer.toggle_language()
                status = f'Langue : {composer.language.upper()}'
            if key == 32 or key in (ord('1'), ord('2'), ord('3')):
                if np.any(canvas):
                    status = 'Validez la lettre avec Entree ou effacez le trace avec x'
                elif key == 32:
                    composer.space()
                    status = 'Espace ajoute'
                elif composer.accept(key - ord('1')):
                    status = 'Suggestion validee + espace'
            speech_status = speaker.poll()
            if speech_status:
                status = speech_status
            if key in (ord('v'), ord('b')):
                text = composer.text if key == ord('v') else composer.text.strip().rsplit(' ', 1)[-1]
                status = speaker.play(text, composer.language)
            frame[canvas > 0] = (0, 255, 0)
            # Put controls outside the camera area; no hidden strokes under the HUD.
            display = np.zeros((h + 160, w, 3), np.uint8)
            display[110:110+h] = frame
            def label(text, y, scale=.48, color=(220,220,220)):
                cv2.putText(display, ascii_text(text), (12, y), cv2.FONT_HERSHEY_SIMPLEX,
                            scale, color, 1, cv2.LINE_AA)
            label(f'[{composer.language.upper()}] Texte : {composer.text[-45:]}', 25, .65)
            word_state = 'mot reconnu' if composer.recognized else 'mot en cours / inconnu'
            choices = ' | '.join(f'{i+1}: {word}' for i, word in enumerate(composer.suggestions))
            label(f'{word_state} | {choices}'[:95], 52)
            label(status, 80)
            label('L: FR/EN | Espace: mot suivant | 1/2/3: suggestion', h+130)
            label('Entree: lettre | V: lire texte | B: dernier mot | x: trace | c: tout | q: quitter', h+150, .40)
            cv2.imshow('Air Writing', display)
    except (FileNotFoundError, OSError) as exc:
        print(f'Modeles indisponibles : {exc}. Consultez le README et lancez python train_model.py.')
    finally:
        speaker.close()
        if tracker is not None:
            tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    run()
