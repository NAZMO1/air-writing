"""Gesture-controlled air writing with live line OCR and offline speech."""
import argparse
import sys
import textwrap
import time

import cv2
import numpy as np

from src.editor import LiveTextEditor
from src.gestures import HeldGesture, StrokeTracker, language_gesture
from src.speech import SpeechPlayer
from src.words import WordComposer, ascii_text


def run(mode='words'):
    # Import only when running: pure editing tests do not need a webcam/MediaPipe.
    from src.hand_tracker import HandTracker
    from src.text_recognition import RecognitionWorker

    backend = cv2.CAP_DSHOW if sys.platform.startswith('win') else cv2.CAP_ANY
    cap = cv2.VideoCapture(0, backend)
    tracker = worker = None
    speaker = SpeechPlayer()
    try:
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(1, backend)
        if not cap.isOpened():
            print('Impossible d ouvrir la webcam.')
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
        tracker = HandTracker()
        composer = WordComposer()
        editor = LiveTextEditor(composer)
        stroke = StrokeTracker()
        language_hold = HeldGesture(1.0)
        command_hold = HeldGesture(1.0)
        classifier = None
        canvas = None
        selected = False
        release_required = False
        status = 'Choisissez FR (index) ou EN (index + majeur), maintenir 1 s'

        def clear_ink():
            canvas.fill(0)
            editor.reset_ink()
            stroke.reset()

        def read_all():
            # Enter always reads the current sentence, replacing queued auto speech.
            speaker.close()
            return speaker.play(composer.text, composer.language)

        def commit_letter():
            nonlocal classifier, status
            try:
                if classifier is None:
                    from src.classifier import LetterClassifier
                    classifier = LetterClassifier()
                letter = classifier.predict(canvas)
                if letter:
                    composer.add_letter(letter)
                    status = f'{letter} (score {classifier.confidence:.0%})'
                    clear_ink()
                    return True
                status = 'Lettre incertaine : corrigez le trace ou x pour effacer'
            except Exception as exc:
                status = 'Modele lettres indisponible : lancez python train_model.py'
                print(f'Classification : {exc}', file=sys.stderr)
            return False

        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            if canvas is None or canvas.shape != (h, w):
                canvas = np.zeros((h, w), np.uint8)
                editor.reset_ink()
                stroke.reset()
            now = time.monotonic()
            tracker.find_hand(frame)
            landmarks = tracker.get_landmarks(frame)
            fingers = tracker.get_fingers_up(landmarks)
            writing = bool(landmarks and fingers[1] and not any(fingers[2:]))
            opened = bool(landmarks and all(fingers))
            fist = bool(landmarks and not any(fingers[1:]))
            key = cv2.waitKey(1) & 0xff
            if key == ord('q'):
                break
            speech_status = speaker.poll()
            if speech_status:
                status = speech_status

            if not selected:
                choice = language_hold.update(language_gesture(fingers) if landmarks else None, now)
                choice = 'fr' if key == ord('f') else 'en' if key == ord('e') else choice
                if choice:
                    composer.set_language(choice)
                    editor.reset_ink()
                    selected = True
                    release_required = True
                    command_hold.reset()
                    status = f'{choice.upper()} choisi : repliez les doigts puis dessinez'
                cv2.putText(frame, 'FR : index seul / EN : index + majeur (1 s)',
                            (10, h//2), cv2.FONT_HERSHEY_SIMPLEX, .58, (0, 255, 255), 2)
                cv2.putText(frame, 'Clavier : F = francais / E = English',
                            (10, h//2+35), cv2.FONT_HERSHEY_SIMPLEX, .55, (255, 255, 255), 1)
            else:
                if release_required:
                    stroke.reset()
                    if not writing:
                        release_required = False
                    command = None
                else:
                    # A final OCR snapshot is frozen until it is accepted or cancelled.
                    point = landmarks[8] if landmarks else None
                    segment = stroke.update(point, writing and not editor.locked, now, (w, h))
                    if point is not None:
                        cv2.circle(frame, point, 7, (0, 0, 255) if writing else (255, 200, 0), -1)
                    if segment:
                        cv2.line(canvas, *segment, 255, 7, cv2.LINE_AA)
                        editor.changed()
                    command = command_hold.update('space' if opened else 'commit' if fist else None, now)
                has_ink = bool(np.any(canvas))

                if key in (ord('c'), ord('x')):
                    clear_ink()
                    if key == ord('c'):
                        composer.clear()
                        speaker.close()
                    status = 'Trace efface' if key == ord('x') else 'Texte et trace effaces'
                elif key == ord('l'):
                    if has_ink or editor.locked:
                        status = 'Validez le trace ou effacez-le avec x avant de changer de langue'
                    else:
                        selected = False
                        language_hold.reset()
                        speaker.close()
                        status = 'Choisir FR : index / EN : index + majeur (1 s)'
                elif key == 9:
                    if has_ink or editor.locked:
                        status = 'Validez le trace ou effacez-le avec x avant de changer de mode'
                    else:
                        mode = 'letters' if mode == 'words' else 'words'
                        editor.reset_ink()
                        status = f'Mode : {mode}'
                elif key == ord('a'):
                    editor.continuous_speech = not editor.continuous_speech
                    if not editor.continuous_speech:
                        speaker.close()
                    status = 'Lecture automatique : ' + ('ON' if editor.continuous_speech else 'OFF')
                elif key in (8, 127):
                    if has_ink or editor.locked:
                        status = 'x efface le trace ; Retour arriere modifie le texte valide'
                    else:
                        composer.backspace()
                elif not editor.locked:
                    enter = key in (10, 13, ord('v'))
                    space = key == 32 or command == 'space'
                    punctuation = chr(key) if key in (ord('.'), ord('!'), ord('?')) else None
                    if mode == 'words':
                        if has_ink and (enter or space or punctuation or command == 'commit'):
                            editor.finish('speak' if enter else punctuation or 'space')
                            status = 'Validation OCR en cours... (x pour annuler)'
                        elif not has_ink:
                            if enter:
                                status = read_all()
                            elif space:
                                composer.space()
                                status = 'Espace ajoute'
                            elif punctuation:
                                composer.punctuate(punctuation)
                    else:
                        # Preserve the previous single-letter classifier as an alternative.
                        if has_ink and (enter or space or punctuation or command == 'commit' or key == ord('r')):
                            if commit_letter():
                                if space:
                                    composer.space()
                                elif punctuation:
                                    composer.punctuate(punctuation)
                                if enter:
                                    status = read_all()
                        elif not has_ink:
                            if enter:
                                status = read_all()
                            elif punctuation:
                                composer.punctuate(punctuation)
                            elif space:
                                word = composer.current_word
                                composer.space()
                                if editor.continuous_speech and word:
                                    status = speaker.play(word, composer.language, enqueue=True)
                            elif key in (ord('1'), ord('2'), ord('3')):
                                if composer.accept(key-ord('1')):
                                    status = 'Suggestion validee + espace'
                    if key == ord('b'):
                        status = speaker.play(composer.text.strip().rsplit(' ', 1)[-1], composer.language)

                if mode == 'words' and selected:
                    if worker is None:
                        worker = RecognitionWorker()
                    event = editor.tick(now, canvas, worker)
                    if event.status:
                        status = event.status
                    if event.clear_canvas:
                        canvas.fill(0)
                        stroke.reset()
                    if event.speak_text:
                        if not event.automatic:
                            speaker.close()
                        status = speaker.play(event.speak_text, composer.language, enqueue=event.automatic)
                    if editor.ocr_error:
                        status = 'OCR indisponible : voir terminal / README ; TAB : mode lettres'
                        # Print once per ink generation, not on every frame.
                        if getattr(editor, '_reported_error', None) != editor.ocr_error:
                            print(editor.ocr_error, file=sys.stderr)
                            editor._reported_error = editor.ocr_error

            frame[canvas > 0] = (0, 255, 0)
            display = np.zeros((h+300, w, 3), np.uint8)
            display[180:180+h] = frame

            def label(text, y, scale=.5, color=(220, 220, 220)):
                cv2.putText(display, ascii_text(text), (12, y), cv2.FONT_HERSHEY_SIMPLEX,
                            scale, color, 1, cv2.LINE_AA)

            label(f'[{composer.language.upper() if selected else "FR / EN ?"}] Mode: {mode} | Voix auto: {"ON" if editor.continuous_speech else "OFF"}', 25, .62)
            columns = max(25, int((w-24)/9))
            for i, line in enumerate(textwrap.wrap(composer.text[-columns*2:], width=columns)[:2]):
                label(line, 53+i*24, .55)
            preview = editor.preview if mode == 'words' else ' | '.join(f'{i+1}: {v}' for i, v in enumerate(composer.suggestions))
            label(('Apercu : ' + preview)[:columns], 106, .52, (100, 255, 180))
            if mode == 'words' and worker is not None and worker.busy:
                label('OCR en cours... ' + ('validation' if editor.locked else 'apercu'), 132)
            label(status[:columns], 160, .48)
            label('Index: tracer | 2 doigts: deplacer | Paume 1 s: espace | Poing 1 s: valider', h+205, .43)
            label('Entree/V: valider + lire | Espace: mot suivant | A: voix auto | L: langue | TAB: mode', h+231, .43)
            label('x: effacer trace | c: tout effacer | Retour: supprimer | . ! ?: ponctuer | q: quitter', h+257, .43)
            label('Mode mots: ecrire lisiblement, lettres detachees, de gauche a droite. R: valider une lettre.', h+283, .40)
            cv2.imshow('Air Writing', display)
    except (FileNotFoundError, OSError) as exc:
        print(f'Initialisation impossible : {exc}. Consultez le README et les modeles requis.')
    finally:
        if worker is not None:
            worker.close()
        speaker.close()
        if tracker is not None:
            tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Air Writing : mots FR/EN et synthese vocale locale.')
    parser.add_argument('--mode', choices=('words', 'letters'), default='words')
    run(parser.parse_args().mode)
