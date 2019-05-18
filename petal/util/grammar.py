"""
Function library for grammatical correctness
"""

def pluralize(num: int, root="", end_plural="s", end_single=""):
    """Given grammar and a number, return the appropriate singular or plural form."""
    return root + (end_single if num == 1 else end_plural)


def get_a(word, include=False):
    word = word.lstrip()
    loword = word.lower()
    b = (" " + word) if include else ""
    if loword[0] in "aeiou" or (loword[0] == "y" and loword[1] not in "aeiou"):
        return "an" + b
    else:
        return "a" + b


_zer = ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"]
_ord = [_zer, ["th"] * 10] + [_zer] * 8

def ordinal(num: int) -> str:
    num = str(num)
    one = int(num[-1])
    ten = int(num[-2]) if len(num) > 1 else 0
    return num + _ord[ten][one]


def sequence_words(words: list) -> str:
    if not words:
        return ""
    words = [str(s) for s in words]
    last = words.pop(-1)
    most = ", ".join(words)
    return (", and " if len(words) > 1 else " and ").join([most, last]) if most else last
