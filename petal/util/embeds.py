"""Dedicated Module for the creation of various standardized Embeds."""

from datetime import datetime as dt, timedelta as td
from typing import Dict, List, Union

from discord import Embed, Guild, Member, Message, User

from .cdn import get_avatar
from .format import bold, escape, italic, mono, underline, userline
from .messages import member_message_history


Muser = Union[Member, User]


def membership_card(member: Muser, *, colour: int = None) -> Embed:
    """Create an Embed Object showing Member/User Details."""
    created_at: dt = member.created_at.replace(microsecond=0)
    joined_at: dt = member.joined_at.replace(microsecond=0)
    now: dt = dt.utcnow().replace(microsecond=0)

    since_created: td = now - created_at
    since_joined: td = now - joined_at

    guild: Guild = member.guild

    em = (
        Embed(
            title=member.display_name,
            description=f"Member of {bold(guild.name)}\n{member.mention}",
            colour=member.colour if colour is None else colour,
            timestamp=now,
        )
        .set_thumbnail(url=get_avatar(member))
        .set_footer(text=f"{member.name}#{member.discriminator} / {member.id}")
    )
    em.add_field(
        name="Account Created", value=f"{created_at}\n({bold(since_created)} ago)"
    )
    em.add_field(name="Joined Server", value=f"{joined_at}\n({bold(since_joined)} ago)")

    # TODO: There is a faster way to get the last message; Find it.
    last: Message = await member_message_history(
        member, limit=1, oldest_first=False
    ).__anext__()

    if last:
        em.add_field(
            name="Last Message",
            value=f"{dt.utcnow() - last.created_at} ago in"
            f" `#{last.channel.name}` ({last.channel.mention}):"
            f"\n{escape(repr(last.content))}",
        )
    else:
        em.add_field(
            name="Last Message", value=f"Member has no Message History in {guild.name}."
        )

    return em


minecraft_suspension = {
    True: "Nonspecific suspension",
    False: "Not suspended",
    000: "Not suspended",
    # Trivial suspensions
    101: "Joke suspension",
    102: "Self-sequested suspension",
    103: "Old account",
    104: "User not in Discord",
    # Minor suspensions
    201: "Minor trolling",
    203: "Compromised account",
    # Moderate suspensions
    301: "Major trolling",
    302: "Stealing",
    # Major suspensions
    401: "Use of slurs",
    402: "Griefing",
    403: "Discord banned",
}
APPROVE: str = underline(mono("--- APPROVED ---"))
PENDING: str = italic(mono("-#- PENDING -#-"))
SUSPEND: str = bold(mono("#!# SUSPENDED #!#"))


def minecraft_card(
    profile: Dict[str, Union[int, str, List[int], List[str]]],
    member: Muser = None,
    verbose: bool = False,
) -> Embed:
    suspended: int = profile.get("suspended", 0)
    approved: List[int] = profile.get("approved", [])

    if suspended:
        col = 0x_AA_22_00
        status = f"{SUSPEND}\n{minecraft_suspension.get(suspended, 'Unknown Code')}"
    elif approved:
        col = 0x_00_CC_00
        status = "\n".join((APPROVE, *(f"<@{i}>" for i in approved)))
    else:
        col = 0x_FF_FF_00
        status = PENDING

    em = Embed(
        title="Minecraft User",
        description=f"Minecraft Username: {escape(repr(profile.get('name')))}"
        f"\nMinecraft UUID: {repr(profile.get('uuid'))}"
        f"\nDiscord Identity: {mono(escape(userline(member)))}"
        f"\nDiscord Tag: {member.mention}",  # TODO: Handle missing Member
        colour=col,
    ).add_field(name="Application Status", value=status)

    # TODO: Add fields for Date, Operator Status, Name History, and Notes

    return em
