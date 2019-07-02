"""Module for "shared" commands, providing Factories for slightly-adjustable
    Command Methods.
"""

import asyncio
from typing import Dict, Union

import discord

from petal import checks


def factory_send(idents: Dict[str, Dict[str, Union[int, str]]], default: str):
    async def cmd_send(
        self, args, src: discord.Message, _identity: str = None, _i: str = None, **_
    ):
        """Broadcast an official-looking message into another channel.

        By using the Identity Option, you can specify who the message is from.
        Valid Identities:```\n{}```

        Syntax: `{{p}}send [OPTIONS] <channel-id> ["<message>"]`
        """
        if 2 < len(args) < 1:
            return "Must provide a Channel ID and, optionally, a quoted message."
        elif not args[0].isdigit():
            return "Channel ID must be integer."

        destination = self.client.get_channel(int(args.pop(0)))
        if not destination:
            return "Invalid Channel."

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
                return "Timed out while waiting for message."
            else:
                text = msg.content
        else:
            text = args[0]

        identity = (_identity or _i or default).lower()
        ident = idents.get(identity, list(idents.values())[0])
        ident["description"] = text

        try:
            em = discord.Embed(**ident)
            await src.channel.send(
                content="Confirm sending this message to {} on behalf of {}?"
                " (Say `yes` to confirm)".format(destination.mention, identity),
                embed=em,
            )
            try:
                confirm = await self.client.wait_for(
                    "message",
                    check=checks.all_checks(
                        checks.Messages.by_user(src.author),
                        checks.Messages.in_channel(src.channel),
                    ),
                    timeout=10,
                )
            except asyncio.TimeoutError:
                return "Timed out."
            if confirm.content.lower() != "yes":
                return "Message cancelled."
            else:
                await self.client.embed(destination, em)

        except discord.errors.Forbidden:
            return "Failed to send message: Access Denied"
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
