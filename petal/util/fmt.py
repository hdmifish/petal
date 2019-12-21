"""Small utility module for wrapping text in Discord Markdown Formatting."""

from re import compile
from typing import Any, Callable, List, Union

import discord


bold = "**{}**".format
italic = "*{}*".format
italic_bold = "***{}***".format
mono = "`{}`".format
no_preview = "<{}>".format
quote = "> {}".format
quote_block = ">>> {}".format
spoiler = "||{}||".format
strike = "~~{}~~".format
underline = "__{}__".format


def mask(url: str, text: str) -> str:
    """Mask a Hyperlink with clickable text.

    NOTE: In Discord, this only works on text in Descriptions and Field Values
        of Embeds. Titles and Field Names will NOT have it.
    """
    return f"[{text}]({url})"


def mono_block(text: str, syntax: str = "") -> str:
    """Wrap a String in a Multi-Line block of Monospace text, optionally with
        Syntax Highlighting.
    """
    return f"```{syntax}\n{text}```"


def smallid(n: Any, seglen: int = 3, sep: str = "...") -> str:
    """Reduce a String into the first and last `seglen` characters, on either
        side of `sep`.

        smallid(1234567890, 3, "...") -> "123...890"
    """
    ns = str(n)
    return f"{ns[:seglen]}{sep}{ns[-seglen:]}"


def unwrap(text: str) -> List[str]:
    """Undo text-wrapping in things like Docstrings.

    Split a long String into Paragraphs by double-newlines. Then, for each
        Paragraph, split it into lines, strip Whitespace from each line and
        rejoin it with single Spaces. Return a List of all the Paragraphs as
        Strings, with no newlines.
    """
    return [
        " ".join((line.strip() for line in paragraph.splitlines()))
        for paragraph in text.split("\n\n")
    ]


def userline(user: Union[discord.Member, discord.User], idf: Callable = None) -> str:
    """Given a Discord User, return "Name#Discrim / ID"."""
    return (
        f"{user.name}#{user.discriminator} /"
        f" {idf(user.id) if callable(idf) else user.id}"
    )


_spec = compile(r"(?=[\\\[\]*>~_|`])")


def escape(text: str) -> str:
    return _spec.sub(r"\\", str(text))
