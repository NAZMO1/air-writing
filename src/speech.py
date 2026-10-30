"""Offline speech in a separate process so camera capture never waits for audio."""
import argparse
import locale
from pathlib import Path
import subprocess
import sys


def find_voice(voices, language):
    for voice in voices:
        for value in getattr(voice, 'languages', ()):
            if isinstance(value, bytes):
                value = value.decode('utf-8', errors='ignore')
            tag = str(value).lstrip(''.join(chr(i) for i in range(33))).lower()
            # Windows SAPI voices may expose hexadecimal LCIDs (409, 40c).
            try:
                tag = locale.windows_locale.get(int(tag, 16), tag).lower()
            except ValueError:
                pass
            if tag.replace('_', '-').split('-')[0] == language:
                return voice.id
    return None


def speak(text, language):
    import pyttsx3
    engine = pyttsx3.init()
    try:
        voice = find_voice(engine.getProperty('voices'), language)
        if voice is None:
            raise RuntimeError(f'Installez une voix {language.upper()} dans votre systeme.')
        engine.setProperty('voice', voice)
        engine.setProperty('rate', 165)
        engine.say(text)
        engine.runAndWait()
    finally:
        engine.stop()


class SpeechPlayer:
    def __init__(self):
        self.process = None

    def play(self, text, language):
        if self.process is not None:
            return 'Lecture deja en cours'
        if not text.strip():
            return 'Aucun texte a lire'
        if len(text) > 2000:
            return 'Texte trop long pour la lecture (maximum 2000 caracteres)'
        try:
            self.process = subprocess.Popen(
                [sys.executable, '-m', 'src.speech', '--language', language, '--text', text.strip()],
                cwd=str(Path(__file__).resolve().parents[1]),
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            )
        except OSError as exc:
            print(f'Synthese vocale : {exc}', file=sys.stderr)
            return 'Impossible de demarrer la voix : voir terminal'
        return 'Lecture en cours'

    def poll(self):
        if self.process is None or self.process.poll() is None:
            return None
        _, error = self.process.communicate()
        failed = self.process.returncode != 0
        self.process = None
        if failed:
            print(error.decode('utf-8', errors='replace'), file=sys.stderr)
            return 'Voix indisponible : voir terminal / README'
        return 'Lecture terminee'

    def close(self):
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            self.process.communicate()
            self.process = None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', choices=('fr', 'en'), default='fr')
    parser.add_argument('--text', required=True)
    args = parser.parse_args()
    try:
        speak(args.text, args.language)
    except Exception as exc:
        print(f'Synthese vocale indisponible : {exc}', file=sys.stderr)
        sys.exit(1)
