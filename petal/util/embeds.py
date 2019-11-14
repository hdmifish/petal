"""Dedicated Module for the creation of various standardized Embeds."""

from datetime import datetime as dt, timedelta as td
from enum import IntEnum
from typing import Optional, Tuple, Union

from discord import Activity, Embed, Game, Guild, Member, Spotify, Streaming, User

from .cdn import get_avatar
from .fmt import bold, escape, smallid
from .grammar import sequence_words


Muser = Union[Member, User]


class Color(IntEnum):
    """An Enumeration of some "standard" RGB colors for use in Embeds."""

    info = 0x_0A_CD_FF  # For when Petal provides help or information.
    tech = 0x_FF_CD_0A  # For information which is a bit more advanced.

    question = 0x_8738F  # AskPatch
    wiki = 0x_F8_F9_FA  # Wiki
    wiki_vague = 0x_FF_CC_33  # Wiki (Disambiguation)
    xkcd = 0x_96_A8_C8  # XKCD

    message_delete = 0x_FC_00_A2
    message_edit = 0x_AE_00_FE

    alert = 0x_9F_00_FF
    mod_kick = 0x_FF_79_00
    mod_mute = 0x_12_00_FF
    mod_warn = 0x_FF_F6_00

    user_join = 0x_00_FF_00
    user_part = 0x_FF_00_00
    user_promote = 0x_00_93_C3
    user_update = 0x_34_F3_AD


def simple_activity(member: Muser) -> Tuple[str, Optional[str]]:
    a = member.activity

    if not isinstance(a, Activity):
        return "Activity", "None"

    elif isinstance(a, Game) or a.to_dict().get("type", -1) == 0:
        return "In-Game", escape(a.name)

    elif isinstance(a, Streaming):
        return (
            "Streaming",
            "{}\n{}\n\n{}".format(
                escape(repr(a.twitch_name or a.name)), a.details, a.url
            ),
        )

    elif isinstance(a, Spotify):
        return (
            "Spotify",
            "{}\nby {}\non {}".format(
                escape(repr(a.title)),
                sequence_words([escape(repr(x)) for x in a.artists]),
                escape(repr(a.album)),
            ),
        )

    else:
        try:
            return a.name, escape(a.details or a.state or "None")
        except:
            return "Activity: UNKNOWN", f"```python\n{a.to_dict()!r}```"


def membership_card(member: Muser, *, colour: int = None) -> Embed:
    """Create an Embed Object showing Member/User Details."""
    created_at: dt = member.created_at.replace(microsecond=0)
    joined_at: dt = member.joined_at.replace(microsecond=0)
    now: dt = dt.utcnow().replace(microsecond=0)

    since_created: td = now - created_at
    since_joined: td = now - joined_at

    guild: Guild = member.guild
    act_name, act_desc = simple_activity(member)

    em = (
        Embed(
            title=member.display_name,
            description=f"Member of {bold(guild.name)}"
            f"\n{member.mention}"
            f"\n{escape(ascii(member.display_name))}"
            f"\n`{smallid(member.id)}`",
            colour=member.colour if colour is None else colour,
            # timestamp=now,
        )
        .set_thumbnail(url=get_avatar(member))
        .set_footer(text=f"{member.name}#{member.discriminator} / {member.id}")
        .add_field(name=act_name, value=act_desc, inline=False)
        .add_field(
            name="Account Created", value=f"{created_at}\n({bold(since_created)} ago)"
        )
        .add_field(
            name="Joined Guild", value=f"{joined_at}\n({bold(since_joined)} ago)"
        )
    )

    return em
