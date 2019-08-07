"""Dedicated Module for the creation of various standardized Embeds."""

from datetime import datetime as dt, timedelta as td
from typing import Union

from discord import Embed, Member, User

from .format import bold


Muser = Union[Member, User]


def membership_card(member: Muser, *, colour: int = None) -> Embed:
    """Create an Embed Object showing Member/User Details."""
    created_at: dt = member.created_at.replace(microsecond=0)
    joined_at: dt = member.joined_at.replace(microsecond=0)
    now: dt = dt.utcnow().replace(microsecond=0)

    since_created: td = now - created_at
    since_joined: td = now - joined_at

    em = (
        Embed(
            title=member.display_name,
            description=f"Member of {bold(member.guild.name)}\n{member.mention}",
            colour=member.colour if colour is None else colour,
            timestamp=now,
        )
        .set_thumbnail(url=member.avatar_url)
        .set_footer(text=f"{member.name}#{member.discriminator} / {member.id}")
    )
    em.add_field(name="Account Created", value=f"{created_at}\n({bold(since_created)} ago)")
    em.add_field(name="Joined Server", value=f"{joined_at}\n({bold(since_joined)} ago)")

    return em
