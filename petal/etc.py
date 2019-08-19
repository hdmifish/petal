"""Miscellaneous functions which are not from external libraries/projects."""

from hashlib import sha256
import shlex
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional as Opt,
    Sequence,
    Tuple,
)

from petal.types import kwopt, T1, T2
from petal.exceptions import CommandArgsError


def any_(sample: Dict[str, T1], *allowed: str) -> T1:
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


def check_types(opts: Dict[str, kwopt], hints: Dict[str, T1]) -> Dict[str, T1]:
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


def enforce_quoted_args(args: Sequence[str], wanted: int, text: str = None):
    """We want only a few Arguments, but one of them is likely to contain
        whitespace. If we get too many, it indicates that the user probably
        meant many of them to be one. However, we cannot be SURE, so fail softly
        with a reminder.
    """
    if len(args) > wanted:
        raise CommandArgsError(
            text
            or "Sorry, it looks like you might have meant for an Argument to be"
            " multiple words, but I cannot be sure. Could you put it in quotes?"
        )


def lambdall(values: Sequence[T1], func: Callable[[T1], T2], mustbe: T2 = True) -> bool:
    """Return True if ALL values, run through `func`, are equal to `mustbe`."""
    for v in values:
        if func(v) != mustbe:
            return False
    return True


def mash(*data: Any, digits: int = 4, base: int = 10) -> int:
    """MultiHash function: Generate a small numeric "name" given arbitrary
        inputs.
    """
    sha = sha256()
    sha.update(bytes("".join(str(d) for d in data), "utf-8"))

    hashval: int = int(sha.hexdigest(), 16)
    diff: int = base ** (digits - 1)
    ceiling: int = (base ** digits) - diff  # 10^4 - 10^3 = 9000

    hashval %= ceiling  # 0000 <= N <= 8999
    hashval += diff  # 1000 <= N <= 9999
    return hashval


def split(line: str) -> Tuple[List[str], str]:
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
