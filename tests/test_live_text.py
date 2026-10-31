"""Editing and async integration tests; no downloaded weights/camera required."""
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import cv2
import numpy as np

from src.editor import LiveTextEditor
from src.gestures import HeldGesture, language_gesture
from src.speech import SpeechPlayer
from src.text_recognition import TextPrediction, TextRecognizer, RecognitionWorker, prepare_canvas
from src.words import WordComposer


class FakeWorker:
    def __init__(self):
        self.busy = False
        self.response = None
        self.requests = []

    def poll(self):
        result, self.response = self.response, None
        if result is not None:
            self.busy = False
        return result

    def submit(self, token, canvas, language):
        if self.busy:
            return False
        self.busy = True
        self.requests.append((token, language))
        return True

    def complete(self, text='', error='', confidence=.9):
        self.response = (self.requests[-1][0], TextPrediction(text, confidence, error))


class EditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.composer = WordComposer()

    def setUp(self):
        self.composer.clear()
        self.composer.set_language('fr')
        self.editor = LiveTextEditor(self.composer)
        self.worker = FakeWorker()
        self.canvas = np.ones((60, 200), dtype=np.uint8)*255
        self.editor.changed()

    def tick(self, now=0):
        return self.editor.tick(now, self.canvas, self.worker)

    def test_live_preview_does_not_commit_or_speak(self):
        self.tick()
        self.worker.complete('BONJOUR')
        event = self.tick(.2)
        self.assertEqual(self.editor.preview, 'BONJOUR')
        self.assertEqual(self.composer.text, '')
        self.assertFalse(event.clear_canvas)
        self.assertEqual(event.speak_text, '')

    def test_space_commits_a_whole_line_and_preserves_accents(self):
        self.editor.finish('space')
        self.tick()
        self.worker.complete('Bonjour à tous')
        event = self.tick(.1)
        self.assertEqual(self.composer.text, 'Bonjour à tous ')
        self.assertTrue(event.clear_canvas)
        self.assertEqual(event.speak_text, '')
        self.assertFalse(self.editor.locked)

    def test_enter_commits_pending_then_reads_entire_sentence_once(self):
        self.composer.append_text('Bonjour')
        self.editor.finish('speak')
        self.tick()
        self.worker.complete('le monde')
        event = self.tick(.2)
        self.assertEqual(event.speak_text, 'Bonjour le monde ')
        self.assertFalse(event.automatic)
        self.assertEqual(self.tick(.3).speak_text, '')

    def test_auto_speech_only_reads_new_committed_text(self):
        self.composer.append_text('Already written')
        self.editor.continuous_speech = True
        self.editor.finish('space')
        self.tick()
        self.worker.complete('hello world')
        event = self.tick(.2)
        self.assertEqual(event.speak_text, 'hello world')
        self.assertTrue(event.automatic)

    def test_clear_discards_in_flight_final_result(self):
        self.editor.finish('speak')
        self.tick()
        self.editor.reset_ink()
        self.worker.complete('GHOST')
        event = self.tick(.2)
        self.assertFalse(event.clear_canvas)
        self.assertEqual(event.speak_text, '')
        self.assertEqual(self.composer.text, '')
        self.assertEqual(self.editor.preview, '')

    def test_new_ink_invalidates_old_preview(self):
        self.tick()
        self.editor.changed()
        self.worker.complete('OLD')
        self.tick(.2)
        self.assertEqual(self.editor.preview, '')
        self.assertEqual(self.composer.text, '')

    def test_language_switch_discards_old_result(self):
        self.tick()
        self.composer.set_language('en')
        self.worker.complete('BONJOUR')
        self.tick(.2)
        self.assertEqual(self.editor.preview, '')

    def test_enter_waits_for_busy_preview_then_requests_final_snapshot(self):
        self.tick()
        self.editor.changed()
        self.editor.finish('speak')
        self.tick(.1)
        self.assertEqual(len(self.worker.requests), 1)
        self.worker.complete('OUTDATED')
        self.tick(.2)
        self.assertEqual(self.worker.requests[-1][0][-1], 'speak')
        self.worker.complete('FINAL')
        event = self.tick(.3)
        self.assertEqual(self.composer.text, 'FINAL ')
        self.assertEqual(event.speak_text, 'FINAL ')

    def test_uncertain_prediction_keeps_canvas_and_text(self):
        self.editor.finish('space')
        self.tick()
        self.worker.complete('', confidence=.2)
        event = self.tick(.2)
        self.assertFalse(event.clear_canvas)
        self.assertEqual(self.composer.text, '')
        self.assertGreater(self.editor.revision, 0)
        self.assertFalse(self.editor.locked)

    def test_missing_ocr_error_is_reported_and_can_be_cancelled(self):
        self.editor.finish('speak')
        self.tick()
        self.worker.complete(error='Missing weights')
        event = self.tick(.2)
        self.assertIn('Missing', event.status)
        self.assertFalse(event.clear_canvas)
        self.editor.finish('speak')
        self.assertIn('Missing', self.tick(.3).status)
        self.editor.reset_ink()
        self.assertEqual(self.editor.ocr_error, '')

    def test_punctuation_attaches_to_last_word(self):
        self.editor.finish('.')
        self.tick()
        self.worker.complete('Hello world')
        self.tick(.1)
        self.assertEqual(self.composer.text, 'Hello world. ')
        self.composer.punctuate('?')
        self.assertEqual(self.composer.text, 'Hello world.? ')


class GestureTests(unittest.TestCase):
    def test_choice_ignores_thumb_and_requires_exact_fingers(self):
        self.assertEqual(language_gesture([False, True, False, False, False]), 'fr')
        self.assertEqual(language_gesture([True, True, True, False, False]), 'en')
        self.assertIsNone(language_gesture([True]*5))
        self.assertIsNone(language_gesture([]))

    def test_stable_hold_fires_once_until_release(self):
        held = HeldGesture(1)
        self.assertIsNone(held.update('space', 0))
        self.assertIsNone(held.update('space', .8))
        self.assertEqual(held.update('space', 1.1), 'space')
        self.assertIsNone(held.update('space', 10))
        held.update(None, 11)
        self.assertIsNone(held.update('space', 12))
        self.assertEqual(held.update('space', 13.1), 'space')
        self.assertIsNone(held.update('fr', 14))
        self.assertIsNone(held.update('en', 14.8))
        self.assertIsNone(held.update('en', 15))


class OCRTests(unittest.TestCase):
    def setUp(self):
        self.canvas = np.zeros((160, 500), np.uint8)
        cv2.putText(self.canvas, 'HELLO', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 2, 255, 4)

    def test_blank_rejected_and_white_background_preserves_geometry(self):
        self.assertIsNone(prepare_canvas(np.zeros_like(self.canvas)))
        image = prepare_canvas(self.canvas)
        self.assertTrue(np.all(image[:24] == 255))
        self.assertEqual(image.min(), 0)
        self.assertGreater(image.shape[1], image.shape[0])
        with self.assertRaises(ValueError):
            prepare_canvas(np.zeros((20, 20, 3), np.uint8))

    def test_reader_receives_full_line_and_language_alphabet(self):
        box = [[0, 0], [100, 0], [100, 20], [0, 20]]
        reader = Mock()
        reader.readtext.return_value = [(box, 'ÉTÉ', .9)]
        rec = TextRecognizer(reader=reader)
        self.assertEqual(rec.predict(self.canvas, 'fr').text, 'ÉTÉ')
        self.assertIn('É', reader.readtext.call_args.kwargs['allowlist'])
        rec.predict(self.canvas, 'en')
        self.assertNotIn('É', reader.readtext.call_args.kwargs['allowlist'])
        self.assertFalse(reader.readtext.call_args.kwargs['paragraph'])

    def test_order_and_low_confidence_do_not_silently_drop_words(self):
        left = [[0, 0], [80, 0], [80, 20], [0, 20]]
        right = [[100, 2], [180, 2], [180, 22], [100, 22]]
        below = [[0, 70], [80, 70], [80, 90], [0, 90]]
        reader = Mock()
        reader.readtext.return_value = [(right, 'world', .9), (below, 'again', .9), (left, 'Hello', .8)]
        rec = TextRecognizer(reader=reader)
        self.assertEqual(rec.predict(self.canvas, 'en').text, 'Hello world again')
        reader.readtext.return_value = [(left, 'Hello', .9), (right, 'world', .1)]
        self.assertEqual(rec.predict(self.canvas, 'en').text, '')
        self.assertAlmostEqual(rec.predict(self.canvas, 'en').confidence, .1)

    def test_missing_optional_dependency_is_nonfatal(self):
        with patch.dict('sys.modules', {'easyocr': None}):
            result = TextRecognizer().predict(self.canvas, 'fr')
        self.assertIn('OCR indisponible', result.error)
        self.assertEqual(result.text, '')

    def test_worker_owns_a_copy_and_survives_inference_error(self):
        recognizer = Mock()
        recognizer.predict.side_effect = [RuntimeError('boom'), TextPrediction('OK', .9)]
        worker = RecognitionWorker(recognizer)
        try:
            self.assertTrue(worker.submit('first', self.canvas, 'en'))
            self.assertFalse(worker.submit('discarded', self.canvas, 'en'))
            result = self.wait_for(worker)
            self.assertIn('boom', result[1].error)
            self.assertTrue(worker.submit('second', self.canvas, 'fr'))
            result = self.wait_for(worker)
            self.assertEqual(result[1].text, 'OK')
            self.assertIsNot(recognizer.predict.call_args.args[0], self.canvas)
        finally:
            worker.close()
        self.assertFalse(worker.submit('closed', self.canvas, 'fr'))

    @staticmethod
    def wait_for(worker):
        deadline = time.monotonic()+2
        while time.monotonic() < deadline:
            result = worker.poll()
            if result is not None:
                return result
            time.sleep(.005)
        raise AssertionError('Worker did not return')


class SpeechQueueTests(unittest.TestCase):
    @patch('src.speech.subprocess.Popen')
    def test_queue_keeps_language_order_and_close_cancels_everything(self, popen):
        proc = popen.return_value
        proc.poll.return_value = None
        player = SpeechPlayer()
        player.play('Bonjour', 'fr')
        player.play('Hello', 'en', enqueue=True)
        player.play('Encore', 'fr', enqueue=True)
        self.assertEqual(len(player.queue), 2)
        proc.poll.return_value = 0
        proc.returncode = 0
        proc.communicate.return_value = (None, b'')
        player.poll()
        self.assertIn('Hello', popen.call_args.args[0])
        self.assertIn('en', popen.call_args.args[0])
        self.assertEqual(len(player.queue), 1)
        player.close()
        self.assertFalse(player.queue)
        self.assertIsNone(player.process)

    @patch('src.speech.subprocess.Popen')
    def test_queue_bounded_and_failure_does_not_repeat_bad_voice(self, popen):
        player = SpeechPlayer()
        player.play('start', 'en')
        for _ in range(20):
            player.play('next', 'en', enqueue=True)
        self.assertIn('pleine', player.play('overflow', 'en', enqueue=True))
        proc = popen.return_value
        proc.poll.return_value = proc.returncode = 1
        proc.communicate.return_value = (None, b'voice failed')
        with patch('sys.stderr'):
            self.assertIn('indisponible', player.poll())
        self.assertEqual(len(player.queue), 0)
        self.assertEqual(popen.call_count, 1)


class AppIntegrationTests(unittest.TestCase):
    def test_draw_whole_phrase_enter_then_read_and_cleanup(self):
        import main

        class Tracker:
            def __init__(self): self.frame = -1
            def find_hand(self, frame): self.frame += 1
            def get_landmarks(self, frame):
                if 2 <= self.frame <= 6:
                    points = [(0, 0)]*21
                    points[8] = (50+6*self.frame, 60)
                    return points
                return []
            def get_fingers_up(self, landmarks):
                return [False, bool(landmarks), False, False, False]
            def close(self): pass

        class ImmediateWorker(FakeWorker):
            def submit(self, token, canvas, language):
                accepted = super().submit(token, canvas, language)
                if accepted:
                    assert np.any(canvas), 'OCR must receive actual ink'
                    self.complete('Bonjour le monde')
                return accepted
            def close(self): pass

        cap = Mock()
        cap.isOpened.return_value = True
        cap.read.side_effect = [(True, np.zeros((180, 320, 3), np.uint8)) for _ in range(14)]
        keys = [ord('f'), 255, 255, 255, 255, 255, 255, 13, 255, 255, 255, 255, ord('q')]
        with patch.dict('sys.modules', {'src.hand_tracker': SimpleNamespace(HandTracker=Tracker)}), \
             patch('src.text_recognition.RecognitionWorker', ImmediateWorker), \
             patch('main.SpeechPlayer') as speech, \
             patch('main.cv2.VideoCapture', return_value=cap), \
             patch('main.cv2.waitKey', side_effect=keys), \
             patch('main.cv2.imshow'), patch('main.cv2.destroyAllWindows') as destroy, \
             patch('main.time.monotonic', side_effect=[i*.11 for i in range(20)]):
            speech.return_value.poll.return_value = None
            speech.return_value.play.return_value = "Lecture en cours"
            main.run('words')
            speech.return_value.play.assert_called_once_with('Bonjour le monde ', 'fr', enqueue=False)
            speech.return_value.close.assert_called()
            cap.release.assert_called_once()
            destroy.assert_called_once()


if __name__ == '__main__':
    unittest.main()
