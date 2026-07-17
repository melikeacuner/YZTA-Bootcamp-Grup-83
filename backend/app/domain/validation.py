def validate_problem_description(text: str) -> str:
    length = len(text)
    if not (20 <= length <= 2000):
        raise ValueError(
            f"Problem aciklamasi 20-2000 karakter araliginda olmalidir (su an: {length})"
        )
    return text


def validate_search_query(text: str) -> str:
    length = len(text)
    if not (10 <= length <= 500):
        raise ValueError(f"Arama sorgusu 10-500 karakter araliginda olmalidir (su an: {length})")
    return text
