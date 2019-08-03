_ones = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
_tens = [
    "{}",
    "{}teen",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
]
_spec = {
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
    15: "fifteen",
    18: "eighteen",
}
_high = [
    "thousand",
    "million",
    "billion",
    "trillion",
    "quadrillion",
    "quintillion",
    "sextillion",
    "septillion",
    "octillion",
    "nonillion",
    "decillion",
    "undecillion",
    "duodecillion",
]


def _cluster(term) -> str:
    term = str(int(term))
    hundreds, small = term[:-2] or "0", term[-2:]
    if len(small) == 1:
        small = "0" + small
    out = (
        ["{} hundred".format(_ones[int(hundreds)])]
        if hundreds and int(hundreds)
        else []
    )

    if int(small) in _spec:
        out.append(_spec[int(small)])
    else:
        if 0 < int(small) < 10:
            out.append(_ones[int(small)])
        else:
            tens, ones = small
            tens_s = _tens[int(tens)]
            if int(ones) == 0:
                out.append(tens_s.format(""))
            else:
                if "{}" in tens_s:
                    out.append(tens_s.format(_ones[int(ones)]))
                else:
                    out.append("-".join([tens_s, _ones[int(ones)]]))

    return " ".join(out)


def word_number(num) -> str:
    num_s = str(num)
    if "." in num_s:
        left_s, right_s = num_s.split(".")
    else:
        left_s, right_s = num_s, ""

    left_list = []
    while left_s:
        left_list.append(left_s[-3:])
        left_s = left_s[:-3]

    if left_list:
        first = left_list.pop(0)
        if int(first) == 0 and left_list:
            out = []
        else:
            out = [_cluster(first)]
    else:
        out = ["zero"]

    for i, cluster in enumerate(left_list):
        if int(cluster):
            out.insert(0, " ".join((_cluster(cluster), _high[i])))

    if right_s:
        out.append("point")
        for char in right_s:
            out.append(_ones[int(char)])

    assembled = " ".join(out).strip()
    while "  " in assembled:
        assembled = assembled.replace("  ", " ")
    return assembled
