"""Small utility module for wrapping text in Discord Markdown Formatting."""

from re import compile
from typing import Union

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


def mono_block(text: str, syntax: str = None) -> str:
    return f"```{syntax or ''}\n{text}```"


def smallid(n: int, seglen: int = 3) -> str:
    ns = str(n)
    return f"{ns[:seglen]}..{ns[-seglen:]}"


def userline(user: Union[discord.Member, discord.User]) -> str:
    return f"{user.name}#{user.discriminator} / {user.id}"


_spec = compile(r"(?=[\\*>~_|`])")


def escape(text: str) -> str:
    return _spec.sub(r"\\", text)
