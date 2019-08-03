"""Small utility module for wrapping text in Discord Markdown Formatting."""


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
