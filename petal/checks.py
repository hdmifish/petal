import asyncio
from typing import Optional, Tuple, Union

import discord


def all_checks(*checks):
    """Specialized Predicate Factory. Return a Predicate that serves as an "AND"
        gate for all passed Predicates.

    Will probably end up raising an Exception if the Signatures do not match.
    """

    def check(*a):
        return all([p(*a) for p in checks])

    return check


def any_checks(*checks):
    """Specialized Predicate Factory. Return a Predicate that serves as an "OR"
        gate for all passed Predicates.

    Will probably end up raising an Exception if the Signatures do not match.
    """

    def check(*a):
        return any([p(*a) for p in checks])

    return check


class Messages:
    """Factory Methods to generate Predicate Checks.

    With the exception of the `waitfor` staticmethod, ALL of these Factory
        Methods MUST return a function that follows this Signature:
        #       method(message):
    It will be passed one param of type discord.Message.
    """

    @staticmethod
    async def waitfor(
        client,
        check,
        default=None,
        timeout: int = 30,
        channel: discord.abc.Messageable = None,
        prompt: str = "",
    ) -> Optional[discord.Message]:
        if channel and prompt:
            try:
                await channel.send(prompt)
            except (discord.Forbidden, discord.HTTPException):
                pass
        try:
            return await client.wait_for("message", check=check, timeout=timeout)
        except asyncio.TimeoutError:
            return default

    @classmethod
    def by_user(cls, user: discord.User):
        def check(_message: discord.Message):
            return _message.author.id == user.id

        return check

    @classmethod
    def in_channel(cls, channel: discord.TextChannel):
        def check(_message: discord.Message):
            return _message.channel.id == channel.id

        return check


class Reactions:
    """Factory Methods to generate Predicate Checks.

    With the exception of the `waitfor` staticmethod, ALL of these Factory
        Methods MUST return a function that follows this Signature:
        #       method(reaction, user):
    It will be passed two params of types `discord.Reaction` and `discord.User`.
    """

    @staticmethod
    async def waitfor(
        client,
        check,
        default=(None, None),
        timeout: int = 30,
        channel: discord.abc.Messageable = None,
        prompt: str = "",
    ) -> Union[Tuple[discord.Reaction, discord.User], Tuple[None, None]]:
        if channel and prompt:
            try:
                await channel.send(prompt)
            except (discord.Forbidden, discord.HTTPException):
                pass
        try:
            return (
                await client.wait_for("react_add", check=check, timeout=timeout)
                or default
            )
        except asyncio.TimeoutError:
            return default

    @classmethod
    def by_user(cls, user: discord.User):
        def check(_reaction1, _user):
            return _user.id == user.id

        return check

    @classmethod
    def on_message(cls, message: discord.Message):
        def check(_reaction, _user):
            return _reaction.message.id == message.id

        return check
