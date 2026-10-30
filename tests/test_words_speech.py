import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from src.words import WordComposer, ascii_text
from src.speech import SpeechPlayer, find_voice, speak


class WordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.composer = WordComposer()

    def setUp(self):
        self.c = self.composer
        self.c.language = 'fr'
        self.c.clear()

    def write(self, word):
        for letter in word:
            self.c.add_letter(letter)

    def test_french_and_english(self):
        self.write('BONJOUR')
        self.assertTrue(self.c.recognized)
        self.c.space()
        self.c.toggle_language()
        self.write('HELLO')
        self.assertTrue(self.c.recognized)
        self.assertEqual(self.c.text, 'BONJOUR HELLO')

    def test_correction_requires_selection(self):
        self.write('BONJDR')
        original = self.c.text
        self.c.space()
        self.assertEqual(self.c.text, original + ' ')
        self.c.clear()
        self.write('BONJOU')
        self.assertIn('BONJOUR', self.c.suggestions)
        self.c.accept(self.c.suggestions.index('BONJOUR'))
        self.assertEqual(self.c.text, 'BONJOUR ')

    def test_spaces_backspace_clear_and_unknown_word(self):
        self.c.space()
        self.assertEqual(self.c.text, '')
        self.write('ZZZXQ')
        self.c.space()
        self.c.space()
        self.assertEqual(self.c.text, 'ZZZXQ ')
        self.c.backspace()
        self.c.backspace()
        self.assertEqual(self.c.text, 'ZZZX')
        self.c.clear()
        self.assertEqual(self.c.suggestions, [])
        self.assertFalse(self.c.accept(0))
        self.assertFalse(self.c.accept(-1))

    def test_accent_suggestion_preserved_for_speech(self):
        self.write('ELEPHANT')
        self.assertIn('ÉLÉPHANT', self.c.suggestions)
        self.c.accept(self.c.suggestions.index('ÉLÉPHANT'))
        self.assertEqual(self.c.text, 'ÉLÉPHANT ')
        self.assertEqual(ascii_text(self.c.text), 'ELEPHANT ')

    def test_switch_recalculates_and_long_input_is_bounded(self):
        self.write('BONJOUR')
        self.c.toggle_language()
        self.assertEqual(self.c.language, 'en')
        self.assertFalse(self.c.recognized)
        self.c.clear()
        self.write('Z'*40)
        self.assertEqual(self.c.suggestions, [])


class SpeechTests(unittest.TestCase):
    def test_voice_metadata(self):
        voices = [SimpleNamespace(id='fr', languages=[b'\x05fr-fr']),
                  SimpleNamespace(id='en', languages=['en_US'])]
        self.assertEqual(find_voice(voices, 'fr'), 'fr')
        self.assertEqual(find_voice(voices, 'en'), 'en')
        self.assertIsNone(find_voice([], 'fr'))
        self.assertEqual(find_voice([SimpleNamespace(id='sapi-fr', languages=['40c'])], 'fr'), 'sapi-fr')

    @patch('src.speech.subprocess.Popen')
    def test_background_play_busy_poll_and_error(self, popen):
        player = SpeechPlayer()
        self.assertEqual(player.play('', 'fr'), 'Aucun texte a lire')
        popen.assert_not_called()
        proc = popen.return_value
        proc.poll.return_value = None
        self.assertEqual(player.play('BONJOUR', 'fr'), 'Lecture en cours')
        self.assertEqual(player.play('HELLO', 'en'), 'Lecture deja en cours')
        self.assertIsNone(player.poll())
        proc.poll.return_value = 0
        proc.returncode = 0
        proc.communicate.return_value = (None, b'')
        self.assertEqual(player.poll(), 'Lecture terminee')
        player.play('HELLO', 'en')
        proc.returncode = 1
        proc.poll.return_value = 1
        proc.communicate.return_value = (None, b'Missing voice')
        with patch('sys.stderr'):
            self.assertIn('indisponible', player.poll())
        self.assertIsNone(player.process)

    @patch('src.speech.subprocess.Popen')
    def test_shutdown_stops_speech(self, popen):
        player = SpeechPlayer()
        player.play('bonjour', 'fr')
        popen.return_value.poll.return_value = None
        player.close()
        popen.return_value.terminate.assert_called_once()
        self.assertIsNone(player.process)

    def test_engine_language_selection_and_missing_voice(self):
        engine = Mock()
        engine.getProperty.return_value = [SimpleNamespace(id='french', languages=['fr-FR'])]
        with patch.dict('sys.modules', {'pyttsx3': SimpleNamespace(init=lambda: engine)}):
            speak('ÉLÉPHANT', 'fr')
            engine.setProperty.assert_any_call('voice', 'french')
            engine.say.assert_called_once_with('ÉLÉPHANT')
            engine.runAndWait.assert_called_once()
            with self.assertRaises(RuntimeError):
                speak('HELLO', 'en')


if __name__ == '__main__':
    unittest.main()
