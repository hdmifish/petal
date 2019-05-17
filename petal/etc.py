"""Miscellaneous functions which are not from external libraries/projects."""

from hashlib import sha256
import shlex
from typing import Tuple, Optional as Opt


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


def check_types(opts: dict, hints: dict) -> dict:
    output = {}
    for opt_name, val in opts.items():
        # opt name back into kwarg name
        kwarg = "_" + opt_name.strip("-").replace("-", "_")
        want = hints[kwarg]
        err = TypeError(
            "Option `{}` wants {}, got {}, `{}`".format(
                opt_name, want, type(val).__name__, repr(val)
            )
        )

        if want == bool or want == Opt[bool]:
            print(repr(val))
            val = True

        elif want == int or want == Opt[int]:
            if val.lstrip("-").isdigit() and val.count("-") <= 1:
                val = int(val)
            else:
                raise err

        elif want == float or want == Opt[float]:
            if val.replace(".", "", 1).lstrip("-").isdigit() and val.count("-") <= 1:
                val = float(val)
            else:
                raise err

        elif want != type(val) and want != Opt[type(val)]:
            raise err

        output[kwarg] = val
    return output


async def get_output(output):
    """Transform returned value into something usable.

    A Command Method has been called. It may have returned a Coroutine, a
        Generator, or even an Asynchronous Generator. However, the last two
        cannot be used by simply awaiting. We need to compact them into a List,
        but of course first we need to know whether that is even necessary.
    """
    if hasattr(output, "__aiter__"):
        # Passed object is an Asynchronous Generator. Collect it.
        return [x async for x in output]
    elif hasattr(output, "__next__"):
        # Passed object is a Synchronous Generator. List it.
        return list(output)
    else:
        # Passed object is a Coroutine. Await it.
        return await output


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


class PreFunc:
    def __init__(self, func, *a, **kw):
        self.func = func
        self.a = a
        self.kw0 = kw

    def run(self, _pre=None, _post=None, **kw1):
        kw2 = self.kw0.copy()
        kw2.update(kw1)
        return self.func(*(_pre or []), *self.a, *(_post or []), **kw2)


def split(line: str) -> Tuple[list, str]:
    """Break an input line into a list of tokens, and a "regular" message."""
    # Split the full command line into a list of tokens, each its own arg.
    tokens = shlex.shlex(line, posix=False)
    tokens.quotes += "`"
    # Split the string only on whitespace.
    tokens.whitespace_split = True
    # However, consider a comma to be whitespace so it splits on them too.
    tokens.whitespace += ","
    # Consider a semicolon to denote a comment; Everything after a semicolon
    #   will then be ignored.
    tokens.commenters = ";"

    # Now, find the original string, but only up until the point of a semicolon.
    # Therefore, the following message:
    #   !help -s commands; @person, this is where to see the list
    # will yield a list:   ["help", "-s", "commands"]
    # and a string:         "help -s commands"
    # This will allow commands to consider "the rest of the line" without going
    #   beyond a semicolon, and without having to reconstruct the line from the
    #   list of arguments, which may or may not have been separated by spaces.
    original = shlex.shlex(line, posix=False)
    original.quotes += "`"
    original.whitespace_split = True
    original.whitespace = ""
    original.commenters = ";"

    # Return a list of all the tokens, and the first part of the "original".
    return list(tokens), original.read_token()


def unquote(string: str) -> str:
    for q in "'\"`":
        if string.startswith(q) and string.endswith(q):
            return string[1:-1]
    return string
