"""Letter-by-letter word composition with explicit, optional dictionary corrections."""
from functools import lru_cache
import unicodedata


def ascii_text(text):
    """OpenCV's built-in font cannot render French accents."""
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()


class WordComposer:
    def __init__(self, language='fr'):
        from spellchecker import SpellChecker
        self.dictionaries = {lang: SpellChecker(language=lang, distance=1)
                             for lang in ('fr', 'en')}
        self.accented = {}
        for lang, spell in self.dictionaries.items():
            index = {}
            for word in spell.word_frequency:
                folded = ascii_text(word)
                if folded != word:
                    index.setdefault(folded, set()).add(word)
            self.accented[lang] = index
        self.language = language
        self.text = ''
        self.suggestions = []
        self.recognized = False

    @property
    def current_word(self):
        return self.text.rsplit(' ', 1)[-1]

    @lru_cache(maxsize=256)
    def _lookup(self, word, language):
        spell = self.dictionaries[language]
        word = word.lower()
        if not word or len(word) > 32:
            return False, ()
        known = bool(spell.known([word]))
        candidates = (spell.candidates(word) or set()) | self.accented[language].get(word, set())
        ordered = sorted(candidates, key=lambda item: (-spell.word_frequency[item], item))
        return known, tuple(item.upper() for item in ordered[:3])

    def refresh(self):
        self.recognized, suggestions = self._lookup(self.current_word, self.language)
        self.suggestions = list(suggestions)

    def add_letter(self, letter):
        if len(letter) == 1 and letter.isascii() and letter.isalpha():
            self.text += letter.upper()
            self.refresh()

    def space(self):
        # Preserve unknown words and names; never silently auto-correct.
        if self.text and not self.text.endswith(' '):
            self.text += ' '
        self.refresh()

    def accept(self, index):
        if 0 <= index < len(self.suggestions):
            self.text = self.text[:-len(self.current_word)] + self.suggestions[index]
            self.space()
            return True
        return False

    def backspace(self):
        self.text = self.text[:-1]
        self.refresh()

    def clear(self):
        self.text = ''
        self.refresh()

    def toggle_language(self):
        self.language = 'en' if self.language == 'fr' else 'fr'
        self.refresh()
