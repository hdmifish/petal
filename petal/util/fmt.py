"""Small utility module for wrapping text in Discord Markdown Formatting."""

from re import compile
from typing import Any, Callable, Union

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


def mono_block(text: str, syntax: str = None) -> str:
    return f"```{syntax or ''}\n{text}```"


def smallid(n: Any, seglen: int = 3, sep: str = "...") -> str:
    ns = str(n)
    return f"{ns[:seglen]}{sep}{ns[-seglen:]}"


def userline(user: Union[discord.Member, discord.User], idf: Callable = None) -> str:
    return (
        f"{user.name}#{user.discriminator} /"
        f" {idf(user.id) if callable(idf) else user.id}"
    )


_spec = compile(r"(?=[\\\[\]*>~_|`])")


def escape(text: str) -> str:
    return _spec.sub(r"\\", str(text))
