"""
Function library for grammatical correctness
"""


def pluralize(n, p="s", s="", w=""):
    # Given grammar and a number, return the appropriate singular or plural form
    return w + {True: p, False: s}[n != 1]


def get_a(word, include=False):
    word = word.lstrip()
    loword = word.lower()
    b = (" " + word) if include else ""
    if loword[0] in "aeiou" or (loword[0] == "y" and loword[1] not in "aeiou"):
        return "an" + b
    else:
        return "a" + b


def sequence_words(words: list) -> str:
    if not words:
        return ""
    words = [str(s) for s in words]
    last = words.pop(-1)
    most = ", ".join(words)
    return (", and " if len(words) > 1 else " and ").join([most, last]) if most else last
