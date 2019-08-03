"""Module for "shared" commands, providing Factories for slightly-adjustable
    Command Methods.
"""

import asyncio
from typing import Dict, Union

import discord

from petal import checks
from petal.exceptions import (
    CommandArgsError,
    CommandExit,
    CommandInputError,
    CommandOperationError,
)
from petal.menu import Menu


def factory_send(idents: Dict[str, Dict[str, Union[int, str]]], default: str):
    async def cmd_send(
        self,
        args,
        src: discord.Message,
        _everyone: bool = False,
        _here: bool = False,
        _identity: str = None,
        _i: str = None,
        _image: str = None,
        _I: str = None,
        **_
    ):
        """Broadcast an official-looking message into another channel.

        By using the Identity Option, you can specify who the message is from.
        Valid Identities:```\n{}```

        Syntax: `{{p}}send [OPTIONS] <channel-id> ["<message>"]`

        Parameters
        ----------
        _ : dict
            Dict of additional Keyword Args.
        self
            self
        args : List[str]
            List of Positional Arguments supplied after Command.
        src : discord.Message
            The Discord Message that invoked this Command.
        _everyone : bool
            Include an `@everyone` ping in the message. Overrides `--here`.
        _here : bool
            Include a `@here` ping in the message.
        _identity, _i : str
            Select the group/team on whose behalf this message is being sent.
        _image, _I : str
            Provide the URL of an image to be included in the embed.
        """
        if 2 < len(args) < 1:
            raise CommandArgsError(
                "Must provide a Channel ID and, optionally, a quoted message."
            )
        elif not args[0].isdigit():
            raise CommandArgsError("Channel ID must be integer.")

        destination: discord.TextChannel = self.client.get_channel(int(args.pop(0)))
        if not destination:
            raise CommandArgsError("Invalid Channel.")

        if not args:
            await self.client.send_message(
                src.author,
                src.channel,
                "Please give a message to send (just reply below):",
            )
            try:
                msg = await self.client.wait_for(
                    "message",
                    check=checks.all_checks(
                        checks.Messages.by_user(src.author),
                        checks.Messages.in_channel(src.channel),
                    ),
                    timeout=30,
                )
            except asyncio.TimeoutError:
                raise CommandInputError("Timed out while waiting for message.")
            else:
                text = msg.content
        else:
            text = args[0]

        identity = (_identity or _i or default).lower()
        ident = idents.get(identity, idents[list(sorted(idents.keys()))[0]])
        ident["description"] = text
        img = _image or _I

        try:
            preview = discord.Embed(**ident)
            if img:
                preview.set_image(url=img)
            menu = Menu(self.client, src.channel, "", "", user=src.author)
            menu.em = preview

            confirm = await menu.get_bool(
                prompt="Send this message to {} on behalf of {}?\n"
                "(This section will not be sent.)".format(destination.mention, identity)
                + (
                    "\n***NOTE: THIS MESSAGE WILL SEND A MASS PING!***"
                    if _everyone or _here
                    else ""
                ),
                title="Confirm",
            )

            if confirm is True:
                em = discord.Embed(**ident)
                if img:
                    em.set_image(url=img)
                if _everyone:
                    await destination.send("(@everyone)", embed=em)
                elif _here:
                    await destination.send("(@here)", embed=em)
                else:
                    await destination.send(embed=em)
                # await self.client.embed(destination, em)
            elif confirm is False:
                raise CommandExit("Message cancelled.")
            else:
                raise CommandExit("Confirmation timed out.")

        except discord.errors.Forbidden:
            raise CommandOperationError("Failed to send message: Access Denied")
        else:
            return (
                "{} (ID: `{}`) sent the following message to {}"
                " on behalf of `{}`:\n{}".format(
                    src.author.name,
                    str(src.author.id),
                    destination.mention,
                    identity,
                    text,
                )
            )

    cmd_send.__doc__ = (
        cmd_send.__doc__.decode()
        if hasattr(cmd_send.__doc__, "decode")
        else cmd_send.__doc__
    ).format("\n".join(list(idents.keys())))

    return cmd_send
