"""Whole-line OCR on the drawing canvas; no camera image is sent to a service.

EasyOCR is optional. Download its models explicitly before offline use. This is
an experimental recognizer for separated, print-like letters, not cursive HTR.
"""
import argparse
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread

import cv2
import numpy as np

MODEL_DIRECTORY = Path(__file__).resolve().parents[1] / 'data' / 'easyocr'


@dataclass(frozen=True)
class TextPrediction:
    text: str = ''
    confidence: float = 0.0
    error: str = ''


def prepare_canvas(canvas):
    """Crop white ink, preserve aspect ratio, return dark text on white paper."""
    if canvas.ndim != 2:
        raise ValueError('Le canevas doit etre une image en niveaux de gris.')
    ys, xs = np.nonzero(canvas > 0)
    if len(xs) < 12 or max(xs.max()-xs.min(), ys.max()-ys.min()) < 20:
        return None
    image = 255-canvas[ys.min():ys.max()+1, xs.min():xs.max()+1]
    # Raise small text to a useful height without unbounded upscaling.
    scale = min(3.0, max(1.0, 96/image.shape[0]))
    image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return cv2.copyMakeBorder(image, 24, 24, 24, 24, cv2.BORDER_CONSTANT, value=255)


def reading_order(detections):
    """Group boxes into lines, then read each line from left to right."""
    rows = []
    for item in sorted(detections, key=lambda r: min(p[1] for p in r[0])):
        box = item[0]
        cy = sum(p[1] for p in box)/len(box)
        height = max(p[1] for p in box)-min(p[1] for p in box)
        row = next((r for r in rows if abs(r[0]-cy) <= max(r[1], height)*0.5), None)
        if row is None:
            row = [cy, height, []]
            rows.append(row)
        row[2].append(item)
    return [item for row in rows for item in sorted(row[2], key=lambda r: min(p[0] for p in r[0]))]


class TextRecognizer:
    def __init__(self, min_confidence=0.45, reader=None):
        self.min_confidence = min_confidence
        self.reader = reader

    def load(self, download=False):
        if self.reader is None:
            import easyocr
            import torch
            torch.set_num_threads(2)
            self.reader = easyocr.Reader(
                ['fr', 'en'], gpu=False, model_storage_directory=str(MODEL_DIRECTORY),
                download_enabled=download, verbose=download,
            )

    def predict(self, canvas, language):
        if language not in ('fr', 'en'):
            raise ValueError('Langue attendue : fr ou en.')
        image = prepare_canvas(canvas)
        if image is None:
            return TextPrediction()
        try:
            self.load()
            chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 '-.,!?"
            if language == 'fr':
                chars += 'ÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸŒÆàâäçéèêëîïôöùûüÿœæ'
            detections = self.reader.readtext(
                image, detail=1, paragraph=False, allowlist=chars,
                decoder='greedy', workers=0, batch_size=1,
            )
            tokens = [(box, ' '.join(text.split()), float(score))
                      for box, text, score in detections if text.strip()]
            if not tokens:
                return TextPrediction()
            confidence = min(item[2] for item in tokens)
            # Never silently omit a low-confidence word from a sentence.
            if confidence < self.min_confidence:
                return TextPrediction(confidence=confidence)
            text = ' '.join(item[1] for item in reading_order(tokens))
            return TextPrediction(text, confidence)
        except Exception as exc:
            return TextPrediction(error=f'OCR indisponible : {exc}. Voir README / requirements-ocr.txt.')


class RecognitionWorker:
    """One bounded request at a time; inference never blocks the camera loop."""
    def __init__(self, recognizer=None):
        self.recognizer = recognizer if recognizer is not None else TextRecognizer()
        self.requests = Queue(maxsize=1)
        self.results = Queue(maxsize=1)
        self.stopped = Event()
        self.busy = False
        self.thread = Thread(target=self._run, name='air-writing-ocr', daemon=True)
        self.thread.start()

    def submit(self, token, canvas, language):
        if self.busy or self.stopped.is_set():
            return False
        self.busy = True
        self.requests.put_nowait((token, canvas.copy(), language))
        return True

    def _run(self):
        while not self.stopped.is_set():
            try:
                token, canvas, language = self.requests.get(timeout=0.1)
            except Empty:
                continue
            if self.stopped.is_set():
                return
            try:
                result = self.recognizer.predict(canvas, language)
            except Exception as exc:
                result = TextPrediction(error=f'Erreur OCR : {exc}')
            self.results.put((token, result))

    def poll(self):
        try:
            result = self.results.get_nowait()
        except Empty:
            return None
        self.busy = False
        return result

    def close(self):
        self.stopped.set()
        # A daemon may finish its current inference; quitting never waits on it.


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Preparer les modeles OCR FR/EN en local.')
    parser.add_argument('--download-models', action='store_true', required=True)
    args = parser.parse_args()
    try:
        TextRecognizer().load(download=True)
        print(f'Modeles prets : {MODEL_DIRECTORY}')
    except Exception as exc:
        parser.exit(1, f'Preparation OCR impossible : {exc}\n')
