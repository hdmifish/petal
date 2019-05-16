"""Miscellaneous functions which are not from external libraries/projects."""

from hashlib import sha256


def any_(sample: dict, *allowed: str):
    """Try to find any specifically non-None (rather than simple logically
        True) value in a dict.
    """
    if not allowed:
        # If no values are supplied, search all.
        allowed = list(sample)

    for key in allowed:
        if sample.get(key, None) is not None:
            return sample[key]

    return None


def lambdall(values, func, mustbe=True):
    """Return True if ALL values, run through `func`, are equal to `mustbe`."""
    for v in values:
        if func(v) != mustbe:
            return False
    return True


def mash(*data, digits=4, base=10):
    """MultiHash function: Generate a small numeric "name" given arbitrary
        inputs.
    """
    sha = sha256()
    sha.update(bytes("".join(str(d) for d in data), "utf-8"))
    hashval = int(sha.hexdigest(), 16)
    ceiling = (base ** digits) - (base ** (digits - 1))  # 10^4 - 10^3 = 9000
    hashval %= ceiling  # 0000 <= N <= 8999
    hashval += base ** (digits - 1)  # 1000 <= N <= 9999
    return hashval
