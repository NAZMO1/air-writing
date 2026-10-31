"""Opt-in smoke tests with real local OCR weights, not webcam accuracy tests."""
import importlib.util
import unittest

import cv2
import numpy as np

from src.text_recognition import MODEL_DIRECTORY, TextRecognizer


@unittest.skipUnless(importlib.util.find_spec('easyocr') and list(MODEL_DIRECTORY.glob('*.pth')),
                     'Installer requirements-ocr.txt et preparer les poids OCR pour ce test facultatif.')
class RealOCRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        torch.set_num_threads(2)
        cls.recognizer = TextRecognizer()
        cls.recognizer.load()  # Offline: never download during tests.

    def check_line(self, text, language):
        canvas = np.zeros((180, 900), np.uint8)
        cv2.putText(canvas, text, (25, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.8, 255, 4, cv2.LINE_AA)
        result = self.recognizer.predict(canvas, language)
        self.assertEqual(result.error, '')
        self.assertEqual(result.text.upper(), text)
        self.assertGreaterEqual(result.confidence, .45)

    def test_french_printed_line(self):
        self.check_line('BONJOUR LE MONDE', 'fr')

    def test_english_printed_line(self):
        self.check_line('HELLO WORLD', 'en')


if __name__ == '__main__':
    unittest.main()
