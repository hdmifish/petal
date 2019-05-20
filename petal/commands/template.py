"""TEMPLATE COMMANDS MODULE; FILL IT WITH REAL CODE
SHOULD NOT BE USED AS-IS"""

import discord

from petal.commands import core


class CommandsTEMPLATE(core.Commands):
    auth_fail = "This command is implemented incorrectly."

    async def cmd_example(self, args: list, msg: str, src: discord.Message, **_: dict):
        """This FIRST segment of the Docstring is the SUMMARY. It is shown first
        in the output of the `{p}help` Command.

        Any non-first segments lacking qualification are assumed by `{p}help` to
        be part of the DETAILS section. The next segment begins with `Syntax:`,
        which indicates to `{p}help` that it makes up the SYNTAX section of the
        output. It can be on one line or multiple.

        Syntax: `{p}example` - Specific function can be described here.

        The final segment, Parameters, is used by `{p}help` to automatically
        generate, as needed, the text shown for the OPTIONS section.

        Parameters
        ----------
        _ : dict
            Dict of additional Keyword Args.
        args : list
            List of Positional Arguments supplied after Command.
        msg : str
            The TEXT of the Message that invoked this Command, minux the Prefix.
        src : discord.Message
            The Discord Message that invoked this Command.

        Also, take note of the fact that the source components of the DETAILS
        section are spread throughout the Docstring.
        """
        pass


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsTEMPLATE
