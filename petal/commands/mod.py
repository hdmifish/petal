"""Commands module for MODERATION UTILITIES.
Access: Role-based"""

import asyncio
from datetime import datetime as dt, timedelta
from hashlib import sha256
from operator import attrgetter
import time

import discord

from petal.commands import core


# MultiHash function: Generate a small numeric "name" given arbitrary inputs.
def mash(*data, digits=4, base=10):
    sha = sha256()
    sha.update(bytes("".join(str(d) for d in data), "utf-8"))
    hashval = int(sha.hexdigest(), 16)
    ceiling = (base ** digits) - (base ** (digits - 1))  # 10^4 - 10^3 = 9000
    hashval %= ceiling  # 0000 <= N <= 8999
    hashval += base ** (digits - 1)  # 1000 <= N <= 9999
    return hashval


class CommandsMod(core.Commands):
    auth_fail = "This command requires the `{role}` role."
    role = "RoleMod"

    async def cmd_alias(self, args, src, **_):
        """Return a list of all previous names a user has had.

        Syntax: `{p}alias <tag/id>`
        """
        if not args:
            member = src.author
        else:
            member = self.get_member(src, args[0])

        if not self.db.useDB:
            return (
                "Database is not configured correctly (or at all). "
                "Contact your bot developer and tell them if you think "
                "this is an error"
            )

        if member is None:
            return (
                "Could not find that member in the server.\n\nJust a note, "
                "I may have record of them, but it's Iso's policy to not "
                "display userinfo without consent. If you are staff and "
                "have a justified reason for this request, please "
                "ask whoever hosts this bot to manually look up the "
                "records in their database."
            )

        self.db.add_member(member)

        alias = self.db.get_attribute(member, "aliases")
        if not alias:
            return "This member has no known aliases."
        else:
            await self.client.send_message(
                src.author, src.channel, "__Aliases for " + member.id + "__"
            )
            msg = ""

            for a in alias:
                msg += "**" + a + "**\n"

            return msg

    async def cmd_kick(
        self, args, src, _reason: str = None, _noconfirm: bool = False, **_
    ):
        """Kick a user from a server.

        Syntax: `{p}kick [OPTIONS] <user tag/id>`

        Options:
        `--reason=<str>` :: Provide a reason immediately, rather than typing a reason in a subsequent message.
        `--noconfirm` :: Perform the action immediately, without asking to make sure. ***This can get you in trouble if you mess up with it.***
        """
        if not args:
            return

        logChannel = src.server.get_channel(self.config.get("logChannel"))

        if logChannel is None:
            return (
                "I'm sorry, you must have logging enabled to use"
                + " administrative functions"
            )

        if _reason is None:
            await self.client.send_message(
                src.author, src.channel, "Please give a reason (just reply below): "
            )

            reason = await self.client.wait_for_message(
                channel=src.channel, author=src.author, timeout=30
            )
            if reason is None:
                return "Timed out while waiting for input"
            _reason = reason.content

        userToBan = self.get_member(src, args[0])
        if userToBan is None:
            return "Could not get user with that id"

        if not _noconfirm:
            await self.client.send_message(
                src.author,
                src.channel,
                "You are about to kick: "
                + userToBan.name
                + ". If this is correct, type `yes`.",
            )
            confmsg = await self.client.wait_for_message(
                channel=src.channel, author=src.author, timeout=10
            )
            if confmsg is None:
                return "Timed out. User was not kicked"
            elif confmsg.content.lower() != "yes":
                return userToBan.name + " was not kicked."

        try:
            # petal.logLock = True
            await self.client.kick(userToBan)
        except discord.errors.Forbidden:
            return "It seems I don't have perms to kick this user"
        else:
            logEmbed = (
                discord.Embed(title="User Kick", description=_reason, colour=0xFF7900)
                .set_author(
                    name=self.client.user.name,
                    icon_url="https:" + "//puu.sh/tAAjx/2d29a3a79c.png",
                )
                .add_field(name="Issuer", value=src.author.name + "\n" + src.author.id)
                .add_field(name="Recipient", value=userToBan.name + "\n" + userToBan.id)
                .add_field(name="Server", value=userToBan.server.name)
                .add_field(name="Timestamp", value=str(dt.utcnow())[:-7])
                .set_thumbnail(url=userToBan.avatar_url)
            )

            await self.client.embed(
                self.client.get_channel(self.config.modChannel), logEmbed
            )
            # # await self.client.send_message(message.author, message.channel, "Cleaning up...", )
            await self.client.send_typing(src.channel)
            await asyncio.sleep(4)
            # petal.lockLog = False
            return (
                userToBan.name + " (ID: " + userToBan.id + ") was successfully kicked"
            )

    async def cmd_ban(
        self,
        args,
        src,
        _reason: str = None,
        _purge: int = 1,
        _noconfirm: bool = False,
        **_,
    ):
        """Ban a user permenantly.

        Syntax: `{p}ban [OPTIONS] <user tag/id>`

        Options:
        `--reason=<str>` :: Provide a reason immediately, rather than typing a reason in a subsequent message.
        `--purge=<int>` :: Determine how many days of messages by the banned user to delete. Default is 1. Can be between 0 and 7, inclusive.
        `--noconfirm` :: Perform the action immediately, without asking to make sure. ***This can get you in trouble if you mess up with it.***
        """
        if not args:
            return

        logChannel = src.server.get_channel(self.config.get("logChannel"))

        if logChannel is None:
            return (
                "I'm sorry, you must have logging enabled "
                + "to use administrative functions"
            )

        if not 0 <= _purge <= 7:
            return "Can only purge between 0 and 7 days of messages, inclusive."

        if _reason is None:
            await self.client.send_message(
                src.author, src.channel, "Please give a reason (just reply below): "
            )

            reason = await self.client.wait_for_message(
                channel=src.channel, author=src.author, timeout=30
            )
            if reason is None:
                return "Timed out while waiting for input"

            _reason = reason.content

        userToBan = self.get_member(src, args[0])
        if userToBan is None:
            return "Could not get user with that id"

        if not _noconfirm:
            await self.client.send_message(
                src.author,
                src.channel,
                "You are about to ban: "
                + userToBan.name
                + ". If this is correct, type `yes`.",
            )
            msg = await self.client.wait_for_message(
                channel=src.channel, author=src.author, timeout=10
            )
            if msg is None:
                return "Timed out... user was not banned."
            elif msg.content.lower() != "yes":
                return userToBan.name + " was not banned."

        try:
            # petal.logLock = True
            await asyncio.sleep(1)
            self.client.db.update_member(
                userToBan, {"banned": True, "tempBanned": False, "banExpires": None}
            )
            await self.client.ban(userToBan, _purge)
        except discord.errors.Forbidden:
            return "It seems I don't have perms to ban this user"
        else:
            logEmbed = (
                discord.Embed(title="User Ban", description=_reason, colour=0xFF0000)
                .set_author(
                    name=self.client.user.name,
                    icon_url="https://" + "puu.sh/tACjX/fc14b56458.png",
                )
                .add_field(name="Issuer", value=src.author.name + "\n" + src.author.id)
                .add_field(name="Recipient", value=userToBan.name + "\n" + userToBan.id)
                .add_field(name="Server", value=userToBan.server.name)
                .add_field(name="Timestamp", value=str(dt.utcnow())[:-7])
                .set_thumbnail(url=userToBan.avatar_url)
            )

            await self.client.embed(
                self.client.get_channel(self.config.modChannel), logEmbed
            )
            await self.client.send_message(
                src.author, src.channel, "Clearing out messages... "
            )
            await asyncio.sleep(4)
            # petal.logLock = False
            response = await self.client.send_message(
                src.author,
                src.channel,
                userToBan.name
                + " (ID: "
                + userToBan.id
                + ") was successfully banned\n\n",
            )
            try:
                # Post-processing webhook for ban command
                return self.generate_post_process_URI(
                    src.author.name + src.author.discriminator,
                    _reason,
                    response.content,
                    userToBan.name + userToBan.discriminator,
                )
            except Exception as e:
                self.log.err(
                    "Could not generate post_process_message for ban: " + str(e)
                )
                return "Error occurred trying to generate webhook URI"

    async def cmd_tempban(
        self, args, src, _reason: str = None, _purge: int = 1, _days: int = None, **_
    ):
        """Temporarily ban a user.

        Syntax: `{p}tempban [OPTIONS] <user tag/id>`

        Options:
        `--reason=<str>` :: Provide a reason immediately, rather than typing a reason in a subsequent message.
        `--purge=<int>` :: Determine how many days of messages by the banned user to delete. Default is 1. Can be between 0 and 7, inclusive.
        `--days=<int>` :: Provide a ban duration immediately, rather than typing a number of days in a subsequent message.
        """
        if not args:
            return

        logChannel = src.server.get_channel(self.config.get("logChannel"))
        if logChannel is None:
            return (
                "I'm sorry, you must have logging enabled to"
                + " use administrative functions"
            )

        if not 0 <= _purge <= 7:
            return "Can only purge between 0 and 7 days of messages, inclusive."

        if _reason is None:
            await self.client.send_message(
                src.author, src.channel, "Please give a reason (just reply below): "
            )
            msg = await self.client.wait_for_message(
                channel=src.channel, author=src.author, timeout=30
            )
            if msg is None:
                return "Timed out while waiting for input"
            _reason = msg.content

        if not _days:
            await self.client.send_message(src.author, src.channel, "How long? (days) ")
            msg2 = await self.client.wait_for_message(
                channel=src.channel, author=src.author, check=str.isnumeric, timeout=30
            )
            if msg2 is None:
                return "Timed out while waiting for input"
            _days = msg2.content

        userToBan = self.get_member(src, args[0])
        if userToBan is None:
            return "Could not get user with that id"

        try:
            # petal.logLock = True
            timex = time.time() + timedelta(days=int(_days)).total_seconds()
            self.client.db.update_member(
                userToBan,
                {
                    "banned": True,
                    "bannedFrom": userToBan.server.id,
                    "banExpires": str(timex).split(".")[0],
                    "tempBanned": True,
                },
            )
            await self.client.ban(userToBan)
        except discord.errors.Forbidden:
            return "It seems I don't have perms to ban this user"
        else:
            logEmbed = discord.Embed(
                title="User Ban", description=_reason, colour=0xFF0000
            )

            logEmbed.add_field(
                name="Issuer", value=src.author.name + "\n" + src.author.id
            )
            logEmbed.add_field(
                name="Recipient", value=userToBan.name + "\n" + userToBan.id
            )
            logEmbed.add_field(name="Server", value=userToBan.server.name)
            logEmbed.add_field(name="Timestamp", value=str(dt.utcnow())[:-7])
            logEmbed.set_thumbnail(url=userToBan.avatar_url)

            await self.client.embed(
                self.client.get_channel(self.config.modChannel), logEmbed
            )
            await self.client.send_message(
                src.author, src.channel, "Clearing out messages... "
            )
            await asyncio.sleep(4)
            # petal.logLock = False
            return (
                userToBan.name
                + " (ID: "
                + userToBan.id
                + ") was successfully temp-banned\n\nThey will be unbanned on "
                + str(dt.utcnow() + timedelta(days=_days))[:-7]
            )

    async def cmd_warn(self, args, src, **_):
        """
        Send an official and logged warning to a user.

        Syntax: `{p}warn <user tag/id>`
        """
        if not args:
            return

        logChannel = src.server.get_channel(self.config.get("logChannel"))

        if logChannel is None:
            return (
                "I'm sorry, you must have logging enabled "
                + "to use administrative functions"
            )

        await self.client.send_message(
            src.author,
            src.channel,
            "Please give a message to send " + "(just reply below): ",
        )
        msg = await self.client.wait_for_message(
            channel=src.channel, author=src.author, timeout=30
        )
        if msg is None:
            return "Timed out while waiting for input"

        userToWarn = self.get_member(src, args[0])
        if userToWarn is None:
            return "Could not get user with that id"

        else:
            try:
                warnEmbed = discord.Embed(
                    title="Official Warning",
                    description="The server has sent " + " you an official warning",
                    colour=0xFFF600,
                )

                warnEmbed.add_field(name="Reason", value=msg.content)
                warnEmbed.add_field(
                    name="Issuing Server", value=src.server.name, inline=False
                )
                await self.client.embed(userToWarn, warnEmbed)

            except discord.errors.Forbidden:
                return "It seems I don't have perms to warn this user"
            else:
                logEmbed = discord.Embed(
                    title="User Warn", description=msg.content, colour=0xFF600
                )
                logEmbed.set_author(
                    name=self.client.user.name,
                    icon_url="https://puu.sh/tADFM/dc80dc3a5d.png",
                )
                logEmbed.add_field(
                    name="Issuer", value=src.author.name + "\n" + src.author.id
                )
                logEmbed.add_field(
                    name="Recipient", value=userToWarn.name + "\n" + userToWarn.id
                )
                logEmbed.add_field(name="Server", value=userToWarn.server.name)
                logEmbed.add_field(name="Timestamp", value=str(dt.utcnow())[:-7])
                logEmbed.set_thumbnail(url=userToWarn.avatar_url)

                await self.client.embed(
                    self.client.get_channel(self.config.modChannel), logEmbed
                )
                return (
                    userToWarn.name
                    + " (ID: "
                    + userToWarn.id
                    + ") was successfully warned"
                )

    async def cmd_mute(self, args, src, **_):
        """
        Toggle the mute tag on a user if your server supports that role.

        Syntax: `{p}mute <user tag/id>`
        """
        if not args:
            return

        muteRole = discord.utils.get(src.server.roles, name="mute")
        if muteRole is None:
            return (
                "This server does not have a `mute` role. "
                + "To enable the mute function, set up the "
                + "roles and name one `mute`."
            )
        logChannel = src.server.get_channel(self.config.get("logChannel"))

        if logChannel is None:
            return (
                "I'm sorry, you must have logging enabled to "
                + "use administrative functions"
            )

        await self.client.send_message(
            src.author,
            src.channel,
            "Please give a " + "reason for the mute " + "(just reply below): ",
        )
        msg = await self.client.wait_for_message(
            channel=src.channel, author=src.author, timeout=30
        )
        if msg is None:
            return "Timed out while waiting for input"

        userToWarn = self.get_member(src, args[0])
        if userToWarn is None:
            return "Could not get user with that id"

        else:
            try:

                if muteRole in userToWarn.roles:
                    await self.client.remove_roles(userToWarn, muteRole)
                    await self.client.server_voice_state(userToWarn, mute=False)
                    warnEmbed = discord.Embed(
                        title="User Unmute",
                        description="You have been unmuted by" + src.author.name,
                        colour=0x00FF11,
                    )

                    warnEmbed.add_field(name="Reason", value=msg.content)
                    warnEmbed.add_field(
                        name="Issuing Server", value=src.server.name, inline=False
                    )
                    muteswitch = "Unmute"
                else:
                    await self.client.add_roles(userToWarn, muteRole)
                    await self.client.server_voice_state(userToWarn, mute=True)
                    warnEmbed = discord.Embed(
                        title="User Mute",
                        description="You have been " + "muted by" + src.author.name,
                        colour=0xFF0000,
                    )
                    warnEmbed.set_author(
                        name=self.client.user.name,
                        icon_url="https://puu.sh/tB2KH/" + "cea152d8f5.png",
                    )
                    warnEmbed.add_field(name="Reason", value=msg.content)
                    warnEmbed.add_field(
                        name="Issuing Server", value=src.server.name, inline=False
                    )
                    muteswitch = "Mute"
                await self.client.embed(userToWarn, warnEmbed)

            except discord.errors.Forbidden:
                return "It seems I don't have perms to mute this user"
            else:
                logEmbed = discord.Embed(
                    title="User {}".format(muteswitch),
                    description=msg.content,
                    colour=0x1200FF,
                )

                logEmbed.add_field(
                    name="Issuer", value=src.author.name + "\n" + src.author.id
                )
                logEmbed.add_field(
                    name="Recipient", value=userToWarn.name + "\n" + userToWarn.id
                )
                logEmbed.add_field(name="Server", value=userToWarn.server.name)
                logEmbed.add_field(name="Timestamp", value=str(dt.utcnow())[:-7])
                logEmbed.set_thumbnail(url=userToWarn.avatar_url)

                await self.client.embed(
                    self.client.get_channel(self.config.modChannel), logEmbed
                )
                return (
                    userToWarn.name
                    + " (ID: "
                    + userToWarn.id
                    + ") was successfully {}d".format(muteswitch)
                )

    async def cmd_purge(self, args, src, **_):
        """
        Purge up to 200 messages in the current channel.

        Syntax: `{p}purge <number of messages to delete>`
        """
        if len(args) < 1:
            return "Please provide a number between 1 and 200"
        try:
            numDelete = int(args[0].strip())
        except ValueError:
            return "Please make sure your input is a number"
        else:
            if numDelete > 200 or numDelete < 0:
                return "That is an invalid number of messages to delete"
        await self.client.send_message(
            src.author,
            src.channel,
            "You are about to delete {} messages ".format(str(numDelete + 3))
            + "(including these confirmations) in "
            + "this channel. Type: confirm if this "
            + "is correct.",
        )
        msg = await self.client.wait_for_message(
            channel=src.channel, content="confirm", author=src.author, timeout=10
        )
        if msg is None:
            return "Purge event cancelled"
        try:
            # petal.logLock = True
            await self.client.purge_from(
                channel=src.channel, limit=numDelete + 3, check=None
            )
        except discord.errors.Forbidden:
            return "I don't have enough perms to purge messages"
        else:
            await asyncio.sleep(2)

            logEmbed = discord.Embed(
                title="Purge Event",
                description="{} messages were purged "
                + "from {} in {} by {}#{}".format(
                    str(numDelete),
                    src.channel.name,
                    src.server.name,
                    src.author.name,
                    src.author.discriminator,
                ),
                color=0x0ACDFF,
            )
            await self.client.embed(
                self.client.get_channel(self.config.modChannel), logEmbed
            )
            await asyncio.sleep(4)
            # petal.logLock = False
            return

    async def cmd_quote(
        self,
        args,
        src,
        _channel: int = None,
        _c: int = None,
        _author: bool = False,
        _a: bool = False,
        _image: bool = False,
        _i: bool = False,
        _preserve: bool = False,
        _p: bool = False,
        _short: bool = False,
        _s: bool = False,
        **_,
    ):
        """Display a quoted message from elsewhere.

        Provide a URL to a Discord message, accessed via `Copy Message Link` in
        the context menu, or simply a slash-separated string of
        `channel-id`/`message-id`. To copy a message link, you may need to enable
        Developer Mode.
        Lone Message IDs will be looked for in the current channel.

        Syntax: `{p}quote [OPTIONS] <URL>...`

        Options:
        `--channel <int>`, `-c <int>` :: Specify a Channel ID to be used for Message IDs provided without a Channel ID.
        `--author`, `-a` :: Display extra information about the Member being quoted.
        `--image`, `-i` :: Display the image, if any, attached to the message being quoted.
        `--preserve`, `-p` :: Do not "simplify" or "clean up" message content.
        `--short`, `-s` :: Display less detail, for a more compact embed. Overrides `--author`, `-a`.
        """
        if not args:
            return "Must provide at least one URL or ID pair."

        for arg in args:
            id_c = _channel or _c or src.channel.id
            p = arg.split("/")
            id_m = p.pop(-1)
            if p:
                id_c = int(p[-1])

            channel: discord.TextChannel = self.client.get_channel(id_c)
            if not channel:
                await self.client.send_message(
                    channel=src.channel,
                    message="Cannot find Channel with id `{}`.".format(id_c),
                )
                continue
            try:
                message: discord.Message = await channel.fetch_message(id_m)
            except discord.NotFound:
                await self.client.send_message(
                    channel=src.channel,
                    message="Cannot find Message with id `{}` in channel `{}`.".format(id_m, id_c),
                )
                continue
            member: discord.Member = message.author

            ct = message.content if _preserve or _p else message.clean_content
            if len(ct) > 1000:
                ct = ct[:997] + "..."

            e = (
                discord.Embed(
                    colour=member.colour,
                    description=ct,
                    timestamp=message.created_at,
                    title="Message __{}__ by {}{} ({} char)".format(
                        mash(member.id, channel.id, message.id),
                        "`[BOT]` " if member.bot else "",
                        member.nick or member.name,
                        len(message.clean_content),
                    )
                    # + (" ({})".format(member.nick) if member.nick else "")
                    + (" (__EDITED__)" if message.edited_at else ""),
                )
                .set_author(icon_url=channel.guild.icon_url, name="#" + channel.name)
                .set_footer(text=f"{member.name}#{member.discriminator} / {member.id}")
                .set_thumbnail(url=member.avatar_url or member.default_avatar_url)
            )

            # Add a field for EMBEDS (mostly for bots).
            if message.embeds:
                e.add_field(
                    name=f"Embed Titles ({len(message.embeds)})",
                    value="\n".join(
                        [
                            (
                                '#{}. ({} char) "{}"'.format(
                                    i + 1,
                                    len(e.get("description", "")),
                                    e.get("title", "(No Title)"),
                                )
                            )
                            for i, e in enumerate(message.embeds)
                        ]
                    ),
                    inline=False,
                )

            # Add a field for ATTACHED FILES (if any).
            if message.attachments:
                if _image or _i:
                    e.set_image(url=message.attachments[0]["url"])
                e.add_field(
                    name="Attached Files",
                    value="\n".join(
                        [
                            "**`{filename}`:** ({size} bytes)\n{url}\n".format(**x)
                            for x in message.attachments
                        ]
                    ),
                    inline=False,
                )

            # Add fields for EXTRA INFORMATION (maybe).
            if not (_short or _s):
                e.add_field(
                    name="Author",
                    value="Nickname: {}\nTag: {}\nRole: {}\nType: {}".format(
                        member.nick or "",
                        member.mention,
                        member.top_role if member.top_role != "@everyone" else None,
                        "Bot" if member.bot else "User",
                    )
                    if _author or _a
                    else member.mention,
                    inline=True,
                ).add_field(
                    name="Location",
                    value=(
                        "{}\n".format(channel.guild.name, channel.mention)
                        if channel.guild
                        else ""
                    )
                    + channel.mention
                    + ("\n**(Pinned)**" if message.pinned else ""),
                    inline=True,
                ).add_field(
                    name="Link to original",
                    value="https://discordapp.com/channels/{}/{}/{}".format(
                        message.guild.id, message.channel.id, message.id
                    ),
                    inline=False,
                )
            if message.mentions:
                e.add_field(
                    name=f"User Tags ({len(message.mentions)})",
                    value="\n".join(
                        [
                            u.mention
                            for u in sorted(message.mentions, key=attrgetter("name"))
                        ]
                    ),
                    inline=False,
                )
            if message.reactions and not (_short or _s):
                e.add_field(
                    name=f"Reactions ({len(message.reactions)})",
                    value="\n".join(
                        [
                            "{} x{} (+1)".format(r.emoji, r.count - 1)
                            if r.me
                            else "{} x{}".format(r.emoji, r.count)
                            for r in message.reactions
                        ]
                    ),
                    inline=False,
                )

            try:  # Post it.
                await self.client.embed(src.channel, e)
            except discord.HTTPException:
                await self.client.send_message(
                    channel=src.channel,
                    message="Failed to post embed. Message may have been too long.",
                )


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMod
