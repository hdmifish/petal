"""Miscellaneous functions which are not from external libraries/projects."""

from hashlib import sha256


# MultiHash function: Generate a small numeric "name" given arbitrary inputs.
def mash(*data, digits=4, base=10):
    sha = sha256()
    sha.update(bytes("".join(str(d) for d in data), "utf-8"))
    hashval = int(sha.hexdigest(), 16)
    ceiling = (base ** digits) - (base ** (digits - 1))  # 10^4 - 10^3 = 9000
    hashval %= ceiling  # 0000 <= N <= 8999
    hashval += base ** (digits - 1)  # 1000 <= N <= 9999
    return hashval
