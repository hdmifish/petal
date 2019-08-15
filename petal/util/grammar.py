"""
Function library for grammatical correctness
"""

def get_a(word: str, include: bool = False) -> str:
    word = word.lstrip()
    loword = word.lower()
    if loword[0] in "aeiou" or (loword[0] == "y" and loword[1] not in "aeiou"):
        return f"an {word}" if include else "an"
    else:
        return f"a {word}" if include else "a"


_zer = ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"]
_ord = [_zer, ["th"] * 10] + [_zer] * 8

def ordinal(num: int, lone: bool = False) -> str:
    num = str(num)
    one = int(num[-1])
    ten = int(num[-2]) if len(num) > 1 else 0
    return _ord[ten][one] if lone else f"{num}{_ord[ten][one]}"


def pluralize(num: int, root: str = "", end_plural: str = "s", end_single: str = "") -> str:
    """Given grammar and a number, return the appropriate singular or plural form."""
    return f"{root}{(end_single if num == 1 else end_plural)}"


def sequence_words(words: list) -> str:
    if not words:
        return ""
    words = [str(s) for s in words]
    last = words.pop(-1)
    most = ", ".join(words)
    return (", and " if len(words) > 1 else " and ").join([most, last]) if most else last
