from __future__ import annotations

import contextvars
import json
import logging
import threading
from collections.abc import Generator
from contextlib import contextmanager
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Final, NamedTuple

logger = logging.getLogger(__name__)
TranslationKey = str
TranslationMap = dict[str, str]
LocaleData = dict[TranslationKey, TranslationMap]


class Lang(str, Enum):
    EN = "en"
    ES = "es"
    EU = "eu"


DEFAULT_LANGUAGE: Final[Lang] = Lang.EN
SUPPORTED_LANGUAGES: Final[frozenset[Lang]] = frozenset(Lang)
_LANG_LOOKUP: Final[dict[str, Lang]] = {lang.value: lang for lang in Lang}
_ASSET_PATH: Final[Path] = Path(__file__).parent.parent.parent / "config" / "translations.json"
_TRANSLATIONS: LocaleData = {}
_LOAD_LOCK: Final[threading.Lock] = threading.Lock()
_LOCALT_CONTEXT: contextvars.ContextVar[Lang | None] = contextvars.ContextVar("cortex_locale", default=None)
__all__ = [
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "CacheStats",
    "Lang",
    "TranslationKey",
    "clear_cache",
    "get_cache_info",
    "get_supported_languages",
    "get_trans",
    "has_translation",
    "override_locale",
    "register_translation",
]
_OVERLAYS: LocaleData = {}
_OVERLAY_LOCK: Final[threading.Lock] = threading.Lock()
_REPORTED_MISSING: set[tuple[str, str]] = set()


def _load_translations() -> LocaleData:
    global _TRANSLATIONS
    if _TRANSLATIONS:
        return _TRANSLATIONS
    with _LOAD_LOCK:
        if _TRANSLATIONS:
            return _TRANSLATIONS
        try:
            path = _ASSET_PATH.resolve()
            if not path.is_file():
                logger.error("I18N Sovereign Failure: Asset missing or invalid at %s", path)
                return {}
            raw_data = path.read_text(encoding="utf-8")
            data: LocaleData = json.loads(raw_data)
            _TRANSLATIONS = data
            logger.debug("I18N: Synchronized %d keys from assets", len(_TRANSLATIONS))
        except (json.JSONDecodeError, OSError) as exc:
            logger.critical("I18N: Fatal failure loading assets: %s", exc)
            return {}
    return _TRANSLATIONS


def register_translation(key: TranslationKey, lang: Lang | str, value: str) -> None:
    normalized_lang = _normalize_lang(lang)
    with _OVERLAY_LOCK:
        if key not in _OVERLAYS:
            _OVERLAYS[key] = {}
        _OVERLAYS[key][normalized_lang.value] = value
        _cached_trans.cache_clear()
    logger.info("I18N: Registered dynamic overlay for [%s] in [%s]", key, normalized_lang)


def get_supported_languages() -> frozenset[Lang]:
    return SUPPORTED_LANGUAGES


def _normalize_lang(lang: str | Lang | None) -> Lang:
    if isinstance(lang, Lang):
        return lang
    if not lang or not isinstance(lang, str):
        return DEFAULT_LANGUAGE
    code = lang.lower().strip()
    if match := _LANG_LOOKUP.get(code):
        return match
    primary = code.split("-", 1)[0][:2]
    return _LANG_LOOKUP.get(primary, DEFAULT_LANGUAGE)


@lru_cache(maxsize=4096)
def _cached_trans(key: TranslationKey, lang_code: Lang) -> str | None:
    with _OVERLAY_LOCK:
        if (entry := _OVERLAYS.get(key)) is not None:
            if (text := entry.get(lang_code.value)) is not None:
                return text
            if lang_code != DEFAULT_LANGUAGE and (text := entry.get(DEFAULT_LANGUAGE.value)) is not None:
                return text
    translations = _load_translations()
    entry = translations.get(key)
    if entry is None:
        return None
    if (text := entry.get(lang_code.value)) is not None:
        return text
    if lang_code != DEFAULT_LANGUAGE:
        if (text := entry.get(DEFAULT_LANGUAGE.value)) is not None:
            logger.debug("I18N: Key [%s] falling back to [%s]", key, DEFAULT_LANGUAGE.value)
            return text
    return None


def _report_missing_key(key: str, lang: Lang) -> None:
    signature = (key, lang.value)
    if signature in _REPORTED_MISSING:
        return
    _REPORTED_MISSING.add(signature)
    logger.warning("I18N: Missing translation for key [%s] in [%s]", key, lang.value)
    _report_as_ghost_fact(key, lang)
    _trigger_adaptive_repair(key, lang)


def _report_as_ghost_fact(key: str, lang: Lang) -> None:
    try:
        from babylon60.facts import store_fact

        store_fact("cortex", f"MISSING_I18N: Key '{key}' missing for lang '{lang.value}'", type="ghost")
    except ImportError:
        logger.debug("I18N: Periodic report skipped - cortex.facts not available yet")


def _trigger_adaptive_repair(key: str, lang: Lang) -> None:
    try:
        from babylon60.extensions.llm.manager import LLMManager
    except ImportError:
        return
    if not hasattr(_report_missing_key, "_llm"):
        _report_missing_key._llm = LLMManager()  # type: ignore[attr-defined]
    llm = _report_missing_key._llm  # type: ignore[attr-defined]
    if not llm.available:
        return
    import asyncio

    async def _repair() -> None:
        logger.info("I18N: Adaptive repair triggered for [%s] in [%s]", key, lang.value)
        prompt = f"Translate the following I18N key to {lang.name} ({lang.value}). Context: It's a UI key for CORTEX (Agentic AI Memory System).\nKey: {key}\nTranslate only the value, be concise and professional."
        try:
            from babylon60.extensions.llm.router import IntentProfile

            translation = await llm.complete(
                prompt, system="You are a professional translator.", intent=IntentProfile.CREATIVE
            )
            if translation:
                register_translation(key, lang, translation.strip())
        except (OSError, RuntimeError, ValueError) as exc:
            logger.debug("I18N: Adaptive repair failed: %s", exc)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_repair())
    except RuntimeError:
        threading.Thread(target=asyncio.run, args=(_repair(),), daemon=True).start()


def get_trans(key: TranslationKey, lang: Lang | str | None = None, **kwargs: Any) -> str:
    target_lang = lang or _LOCALT_CONTEXT.get() or Lang.EN
    normalized_lang = _normalize_lang(target_lang)
    text = _cached_trans(key, normalized_lang)
    if text is None:
        _report_missing_key(key, normalized_lang)
        text = key
    if kwargs and text != key:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError, IndexError):
            logger.exception("I18N Formatting Error [%s] with data %s", key, kwargs)
    return text


def has_translation(key: str) -> bool:
    with _OVERLAY_LOCK:
        if key in _OVERLAYS:
            return True
    translations = _load_translations()
    return key in translations


@contextmanager
def override_locale(lang: str | Lang) -> Generator[None, None, None]:
    normalized = _normalize_lang(lang)
    token = _LOCALT_CONTEXT.set(normalized)
    try:
        yield
    finally:
        _LOCALT_CONTEXT.reset(token)


class CacheStats(NamedTuple):
    hits: int
    misses: int
    maxsize: int | None
    currsize: int


def get_cache_info() -> CacheStats:
    info = _cached_trans.cache_info()
    return CacheStats(info.hits, info.misses, info.maxsize, info.currsize)


def clear_cache() -> None:
    global _TRANSLATIONS, _OVERLAYS
    with _LOAD_LOCK, _OVERLAY_LOCK:
        _cached_trans.cache_clear()
        _TRANSLATIONS.clear()
        _OVERLAYS.clear()
        _REPORTED_MISSING.clear()
