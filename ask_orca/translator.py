from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException


# Indian languages ORCA supports for replies (ISO 639-1 codes used by
# deep_translator / GoogleTranslator).
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ur": "Urdu",
    "or": "Odia",
    "as": "Assamese",
}


def detect_language(text):
    """
    Detect the language of the incoming question so ORCA can reply in
    that same language, even if the caller didn't pass a language code.
    Falls back to English if detection fails or the detected language
    isn't one ORCA supports.
    """

    if not text or not text.strip():
        return "en"

    try:
        detected = detect(text)
    except LangDetectException:
        return "en"

    if detected in SUPPORTED_LANGUAGES:
        return detected

    return "en"


def translate_to_english(text, language):
    if language == "en":
        return text

    try:
        return GoogleTranslator(
            source=language,
            target="en"
        ).translate(text)
    except Exception:
        return text


def translate_from_english(text, language):
    if language == "en":
        return text

    try:
        return GoogleTranslator(
            source="en",
            target=language
        ).translate(text)
    except Exception:
        return text