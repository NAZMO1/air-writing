"""Camera-independent editing state and stale-result protection for live OCR."""
from dataclasses import dataclass


@dataclass(frozen=True)
class EditorEvent:
    status: str = ''
    clear_canvas: bool = False
    speak_text: str = ''
    automatic: bool = False


class LiveTextEditor:
    def __init__(self, composer):
        self.composer = composer
        self.continuous_speech = False
        self.reset_ink()

    def reset_ink(self):
        self.generation = getattr(self, 'generation', 0)+1
        self.revision = 0
        self.preview = ''
        self.confidence = 0.0
        self.pending_action = None
        self.last_request = float('-inf')
        self.ocr_error = ''

    @property
    def locked(self):
        return self.pending_action is not None

    def changed(self):
        self.revision += 1
        self.preview = ''

    def finish(self, action='space'):
        if action not in ('space', 'speak', '.', '!', '?'):
            raise ValueError('Action de validation inconnue.')
        if not self.locked:
            self.pending_action = action

    def tick(self, now, canvas, worker):
        response = worker.poll()
        if response is not None:
            (generation, revision, language, action), prediction = response
            if (generation, revision, language) == (self.generation, self.revision, self.composer.language):
                self.preview = prediction.text
                self.confidence = prediction.confidence
                self.ocr_error = prediction.error
                if action is not None and action == self.pending_action:
                    self.pending_action = None
                    if prediction.error or not prediction.text:
                        return EditorEvent(prediction.error or 'Incertain : ajustez le trace ou x pour effacer')
                    self.composer.append_text(prediction.text)
                    if action in ('.', '!', '?'):
                        self.composer.punctuate(action)
                    else:
                        self.composer.space()
                    spoken = self.composer.text if action == 'speak' else prediction.text
                    automatic = action != 'speak'
                    say = spoken if not automatic or self.continuous_speech else ''
                    self.reset_ink()
                    return EditorEvent('Texte valide', True, say, automatic)
        if self.revision and not self.ocr_error and (self.locked or now-self.last_request >= 1.0):
            token = (self.generation, self.revision, self.composer.language, self.pending_action)
            if worker.submit(token, canvas, self.composer.language):
                self.last_request = now
        elif self.ocr_error and self.locked:
            self.pending_action = None
            return EditorEvent(self.ocr_error)
        return EditorEvent()
