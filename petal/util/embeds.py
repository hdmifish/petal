"""Dedicated Module for the creation of various standardized Embeds."""

from datetime import datetime as dt, timedelta as td
from enum import IntEnum
from typing import Union

from discord import Embed, Guild, Member, User

from .cdn import get_avatar
from .fmt import bold, escape, smallid


Muser = Union[Member, User]


class Color(IntEnum):
    """An Enumeration of some "standard" RGB colors for use in Embeds."""

    info = 0x_0A_CD_FF  # For when Petal provides help or information.
    tech = 0x_FF_CD_0A  # For information which is a bit more advanced.

    question = 0x_8738F  # AskPatch
    wiki = 0x_F8_F9_FA  # Wiki
    wiki_vague = 0x_FF_CC_33  # Wiki (Disambiguation)
    xkcd = 0x_96_A8_C8  # XKCD


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
            description=f"Member of {bold(guild.name)}"
            f"\n{member.mention}"
            f"\n{escape(ascii(member.display_name))}"
            f"\n`[{smallid(member.id)}]`",
            colour=member.colour if colour is None else colour,
            timestamp=now,
        )
        .set_thumbnail(url=get_avatar(member))
        .set_footer(text=f"{member.name}#{member.discriminator} / {member.id}")
    )
    em.add_field(
        name="Account Created", value=f"{created_at}\n({bold(since_created)} ago)"
    )
    em.add_field(name="Joined Guild", value=f"{joined_at}\n({bold(since_joined)} ago)")

    return em
