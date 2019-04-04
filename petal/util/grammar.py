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


def sequence_words(words, o=""):
    o1 = ""
    if type(words) != list:
        return str(words)
    while None in words:
        words.remove(None)
    words = [str(word) for word in words]
    if len(words) == 0:
        pass
    elif len(words) == 1:
        o += "{}".format(words.pop(0))
    elif len(words) > 1:
        o += "{}".format(words.pop(0))
        if len(words) > 1:
            o1 = ", and {}".format(words.pop(-1))
        else:
            o1 = " and {}".format(words.pop(-1))
        for p in words:
            o += ", {}".format(p)
    return o + o1
