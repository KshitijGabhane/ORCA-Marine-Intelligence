from deep_translator import GoogleTranslator


SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "gu": "Gujarati",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "or": "Odia",
    "pa": "Punjabi"
}


def translate_to_english(text, source_language):
    """
    Translate user's question to English.
    """

    if not text:
        return ""

    if source_language == "en":
        return text

    try:
        return GoogleTranslator(
            source=source_language,
            target="en"
        ).translate(text)

    except Exception as e:
        print("Translation to English failed:", e)
        return text


def translate_from_english(text, target_language):
    """
    Translate ORCA answer back to user's language.
    """

    if not text:
        return ""

    if target_language == "en":
        return text

    try:
        return GoogleTranslator(
            source="en",
            target=target_language
        ).translate(text)

    except Exception as e:
        print("Translation from English failed:", e)
        return text