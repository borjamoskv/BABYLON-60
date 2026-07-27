# C5-REAL EXERGY CERTIFIED
# scripts/translator_manager.py
"""Utility module to manage multilingual translation using deep-translator.
Provides a TranslatorManager class that can translate text from a source
language to multiple target languages, with optional back‑translation
verification using rapidfuzz.
"""

from typing import Dict, Tuple
from deep_translator import GoogleTranslator
from rapidfuzz import fuzz
import time

class TranslatorManager:
    """Manage translation across many languages with verification.
    ``LANGUAGE_CODES`` maps readable language names to ISO 639‑1 codes used
    by ``deep-translator``.
    """

    LANGUAGE_CODES = {
        "Arabic": "ar",
        "Catalan": "ca",
        "Danish": "da",
        "Dutch": "nl",
        "English": "en",
        "English (British)": "en-GB",
        "Finnish": "fi",
        "French": "fr",
        "German": "de",
        "Icelandic": "is",
        "Italian": "it",
        "Japanese": "ja",
        "Norwegian": "no",
        "Polish": "pl",
        "Portuguese (Brazilian)": "pt",
        "Portuguese (European)": "pt-PT",
        "Spanish": "es",
        "Swedish": "sv",
        "Turkish": "tr",
        "Basque": "eu",   # Euskera
        "Esperanto": "eo",
    }

    def __init__(self, src_lang: str = "es", verify: bool = True, similarity_thresh: int = 70, max_retries: int = 2):
        self.src_lang = src_lang
        self.verify = verify
        self.similarity_thresh = similarity_thresh
        self.max_retries = max_retries
        # Pre‑create translator objects for each target language (excluding source).
        self.translators: Dict[str, GoogleTranslator] = {}
        for name, code in self.LANGUAGE_CODES.items():
            if code != src_lang:
                self.translators[code] = GoogleTranslator(source=self.src_lang, target=code)

    def translate(self, text: str, dest_code: str) -> str:
        """Translate *text* from source language to *dest_code* with retries."""
        translator = self.translators.get(dest_code)
        if not translator:
            raise ValueError(f"Unsupported destination language code: {dest_code}")
        for attempt in range(self.max_retries + 1):
            try:
                return translator.translate(text)
            except Exception as e:
                if attempt < self.max_retries:
                    time.sleep(1)
                else:
                    raise e

    def back_translate(self, text: str, dest_code: str) -> str:
        """Perform forward then back translation to source language."""
        forward = self.translate(text, dest_code)
        back_translator = GoogleTranslator(source=dest_code, target=self.src_lang)
        for attempt in range(self.max_retries + 1):
            try:
                return back_translator.translate(forward)
            except Exception:
                if attempt < self.max_retries:
                    time.sleep(1)
                else:
                    raise

    def translate_with_verification(self, text: str, dest_code: str) -> Tuple[str, bool]:
        """Translate and verify via back‑translation, returning (text, passed)."""
        translated = self.translate(text, dest_code)
        if not self.verify:
            return translated, True
        back = self.back_translate(text, dest_code)
        similarity = fuzz.ratio(text, back)
        return translated, similarity >= self.similarity_thresh

    def translate_all(self, text: str) -> Dict[str, Tuple[str, bool]]:
        """Translate *text* into all target languages, returning a dict.
        ``dest_code -> (translated_text, verification_passed)``.
        """
        results: Dict[str, Tuple[str, bool]] = {}
        for code in self.translators.keys():
            results[code] = self.translate_with_verification(text, code)
        return results
