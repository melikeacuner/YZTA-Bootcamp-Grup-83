def validate_problem_description(text: str) -> str:
    length = len(text)
    if not (20 <= length <= 2000):
        raise ValueError(
            f"Problem aciklamasi 20-2000 karakter araliginda olmalidir (su an: {length})"
        )
    return text


def validate_search_query(text: str) -> str:
    length = len(text)
    if not (2 <= length <= 500):
        raise ValueError(f"Arama sorgusu 2-500 karakter araliginda olmalidir (su an: {length})")
    return text


def validate_lessons_learned(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("lessons_learned bos birakilamaz")
    word_count = len(text.split())
    if word_count > 1000:
        raise ValueError(
            f"lessons_learned en fazla 1000 kelime olmalidir (su an: {word_count})"
        )
    return text
