import time
from typing import Iterable, Optional, Protocol


class TranslatorAPI(Protocol):
    def translate(self, text: str, scr: str, dest: str, *args, **kwargs):
        ...


class Translator:
    def __init__(
        self, api: TranslatorAPI, source: str, dest: str, max_retries: int = 3
    ) -> None:
        self.api = api
        self.source_language = source
        self.destination_language = dest
        self.max_retries = max_retries
        self.last_translation: Optional[tuple[str, str]] = None

    def translate(self, text: str) -> str:
        return self.api.translate(
            text, src=self.source_language, dest=self.destination_language
        ).text

    def try_translate(self, text: str) -> Optional[str]:
        for _ in range(self.max_retries + 1):
            try:
                translated_text = self.translate(text)
                self.last_translation = (
                    text,
                    translated_text,
                )
                return translated_text
            except Exception:
                time.sleep(1)
        return

    def try_translate_sequence(self, sequence: Iterable[str]) -> list[Optional[str]]:
        return [self.try_translate(original_text) for original_text in sequence]

    def get_last_translation(
        self,
    ) -> Optional[tuple[str, str]]:
        return self.last_translation
