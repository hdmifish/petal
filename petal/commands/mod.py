"""Commands module for MODERATION UTILITIES.
Access: Role-based"""

import asyncio
from datetime import datetime as dt, timedelta
from operator import attrgetter
import time

import discord

from petal.commands import core
from petal.etc import mash


same_author = lambda m0: lambda m1: m0.author == m1.author and m0.channel == m1.channel


class CommandsMod(core.Commands):
    auth_fail = "This command requires the `{role}` role."
    role = "RoleMod"

    async def cmd_alias(self, args, src: discord.Message, **_):
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
                "Could not find that member in the guild.\n\nJust a note, "
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
        self,
        args,
        src: discord.Message,
        _reason: str = None,
        _noconfirm: bool = False,
        **_,
    ):
        """Kick a user from a guild.

        Syntax: `{p}kick [OPTIONS] <user tag/id>`

        Options:
        `--reason=<str>` :: Provide a reason immediately, rather than typing a reason in a subsequent message.
        `--noconfirm` :: Perform the action immediately, without asking to make sure. ***This can get you in trouble if you mess up with it.***
        """
        if not args:
            return

        if not self.lambdall(args, lambda x: x.isdigit()):
            return "All IDs must be positive Integers."

        guild = self.client.main_guild
        userToBan = guild.get_member(int(args[0]))
        if userToBan is None:
            return "Could not get user with that ID."
        elif userToBan.id == self.client.user.id:
            return (
                f"I'm sorry, {src.author.mention}. I'm afraid I can't let you do that."
            )

        if _reason is None:
            await self.client.send_message(
                src.author, src.channel, "Please give a reason (just reply below): "
            )
            try:
                reason = await self.client.wait_for(
                    "message", check=same_author(src), timeout=30
                )
            except asyncio.TimeoutError:
                return "Timed out while waiting for reason."
            _reason = reason.content

        if not _noconfirm:
            await self.client.send_message(
                src.author,
                src.channel,
                "You are about to kick: "
                + userToBan.name
                + ". If this is correct, type `yes`.",
            )
            try:
                confmsg = await self.client.wait_for(
                    "message", check=same_author(src), timeout=10
                )
            except asyncio.TimeoutError:
                return "Timed out. User was not kicked"
            if confmsg.content.lower() != "yes":
                return userToBan.name + " was not kicked."

        try:
            # petal.logLock = True
            await userToBan.kick(reason=_reason)
        except discord.errors.Forbidden:
            return "It seems I don't have perms to kick this user"
        else:
            logEmbed = (
                discord.Embed(title="User Kick", description=_reason, colour=0xFF7900)
                .set_author(
                    name=self.client.user.name,
                    icon_url="https://puu.sh/tAAjx/2d29a3a79c.png",
                )
                .add_field(
                    name="Issuer", value=src.author.name + "\n" + str(src.author.id)
                )
                .add_field(
                    name="Recipient", value=userToBan.name + "\n" + str(userToBan.id)
                )
                .add_field(name="Server", value=userToBan.guild.name)
                .add_field(name="Timestamp", value=str(dt.utcnow())[:-7])
                .set_thumbnail(url=userToBan.avatar_url)
            )

            await self.client.embed(
                self.client.get_channel(self.config.modChannel), logEmbed
            )
            return (
                userToBan.name
                + " (ID: "
                + str(userToBan.id)
                + ") was successfully kicked"
            )

    async def cmd_ban(
        self,
        args,
        src: discord.Message,
        _reason: str = None,
        _purge: int = 1,
        _noconfirm: bool = False,
        **_,
    ):
        """Ban a user permanently.

        Syntax: `{p}ban [OPTIONS] <user tag/id>`

        Options:
        `--reason=<str>` :: Provide a reason immediately, rather than typing a reason in a subsequent message.
        `--purge=<int>` :: Determine how many days of messages by the banned user to delete. Default is 1. Can be between 0 and 7, inclusive.
        `--noconfirm` :: Perform the action immediately, without asking to make sure. ***This can get you in trouble if you mess up with it.***
        """
        if not args:
            return

        if not self.lambdall(args, lambda x: x.isdigit()):
            return "All IDs must be positive Integers."

        guild = self.client.main_guild
        userToBan = guild.get_member(int(args[0]))
        if userToBan is None:
            return "Could not get user with that ID."
        elif userToBan.id == self.client.user.id:
            return (
                f"I'm sorry, {src.author.mention}. I'm afraid I can't let you do that."
            )

        if not 0 <= _purge <= 7:
            return "Can only purge between 0 and 7 days of messages, inclusive."

        if _reason is None:
            await self.client.send_message(
                src.author, src.channel, "Please give a reason (just reply below): "
            )
            try:
                reason = await self.client.wait_for(
                    "message", check=same_author(src), timeout=30
                )
            except asyncio.TimeoutError:
                return "Timed out while waiting for reason."

            _reason = reason.content

        if not _noconfirm:
            await self.client.send_message(
                src.author,
                src.channel,
                "You are about to ban: "
                + userToBan.name
                + ". If this is correct, type `yes`.",
            )
            try:
                msg = await self.client.wait_for(
                    "message", check=same_author(src), timeout=30
                )
            except asyncio.TimeoutError:
                return "Timed out... user was not banned."
            if msg.content.lower() != "yes":
                return userToBan.name + " was not banned."

        try:
            # petal.logLock = True
            self.client.db.update_member(
                userToBan, {"banned": True, "tempBanned": False, "banExpires": None}
            )
            await userToBan.ban(reason=_reason, delete_message_days=_purge)
        except discord.errors.Forbidden:
            return "It seems I don't have perms to ban this user."
        else:
            logEmbed = (
                discord.Embed(title="User Ban", description=_reason, colour=0xFF0000)
                .set_author(
                    name=self.client.user.name,
                    icon_url="https://" + "puu.sh/tACjX/fc14b56458.png",
                )
                .add_field(
                    name="Issuer", value=src.author.name + "\n" + str(src.author.id)
                )
                .add_field(
                    name="Recipient", value=userToBan.name + "\n" + str(userToBan.id)
                )
                .add_field(name="Server", value=userToBan.guild.name)
                .add_field(name="Timestamp", value=str(dt.utcnow())[:-7])
                .set_thumbnail(url=userToBan.avatar_url)
            )

            await self.client.embed(
                self.client.get_channel(self.config.modChannel), logEmbed
            )
            await asyncio.sleep(4)
            # petal.logLock = False
            response = await self.client.send_message(
                src.author,
                src.channel,
                userToBan.name
                + " (ID: "
                + str(userToBan.id)
                + ") was successfully banned.",
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
        self,
        args,
        src: discord.Message,
        _reason: str = None,
        _purge: int = 1,
        _days: int = None,
        **_,
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

        if not self.lambdall(args, lambda x: x.isdigit()):
            return "All IDs must be positive Integers."

        guild = self.client.main_guild
        userToBan = guild.get_member(int(args[0]))
        if userToBan is None:
            return "Could not get user with that ID."
        elif userToBan.id == self.client.user.id:
            return (
                f"I'm sorry, {src.author.mention}. I'm afraid I can't let you do that."
            )

        if not 0 <= _purge <= 7:
            return "Can only purge between 0 and 7 days of messages, inclusive."

        if _reason is None:
            await self.client.send_message(
                src.author, src.channel, "Please give a reason (just reply below): "
            )
            try:
                reason = await self.client.wait_for(
                    "message", check=same_author(src), timeout=30
                )
            except asyncio.TimeoutError:
                return "Timed out while waiting for reason."
            _reason = reason.content

        if not _days:
            await self.client.send_message(src.author, src.channel, "How long? (days) ")
            try:
                msg2 = await self.client.wait_for(
                    "message",
                    check=(lambda x: same_author(src)(x) and x.content.isdigit()),
                    timeout=30,
                )
            except asyncio.TimeoutError:
                return "Timed out while waiting for input"
            _days = msg2.content

        try:
            # petal.logLock = True
            timex = time.time() + timedelta(days=int(_days)).total_seconds()
            self.client.db.update_member(
                userToBan,
                {
                    "banned": True,
                    "bannedFrom": userToBan.guild.id,
                    "banExpires": str(timex).split(".")[0],
                    "tempBanned": True,
                },
            )
            await userToBan.ban(reason=_reason, delete_message_days=_purge)
        except discord.errors.Forbidden:
            return "It seems I don't have perms to ban this user"
        else:
            logEmbed = discord.Embed(
                title="User Ban", description=_reason, colour=0xFF0000
            )

            logEmbed.add_field(
                name="Issuer", value=src.author.name + "\n" + str(src.author.id)
            )
            logEmbed.add_field(
                name="Recipient", value=userToBan.name + "\n" + str(userToBan.id)
            )
            logEmbed.add_field(name="Server", value=userToBan.guild.name)
            logEmbed.add_field(name="Timestamp", value=str(dt.utcnow())[:-7])
            logEmbed.set_thumbnail(url=userToBan.avatar_url)

            await self.client.embed(
                self.client.get_channel(self.config.modChannel), logEmbed
            )
            return (
                userToBan.name
                + " (ID: "
                + str(userToBan.id)
                + ") was successfully temp-banned.\n\nThey will be unbanned on "
                + str(dt.utcnow() + timedelta(days=_days))[:-7]
            )

    async def cmd_warn(self, args, src: discord.Message, **_):
        """Send an official and logged warning to a user.

        Syntax: `{p}warn <user tag/id>`
        """
        if not args:
            return

        if not self.lambdall(args, lambda x: x.isdigit()):
            return "All IDs must be positive Integers."

        guild = self.client.main_guild
        userToWarn = guild.get_member(int(args[0]))
        if userToWarn is None:
            return "Could not get user with that ID."
        elif userToWarn.id == self.client.user.id:
            return (
                f"I'm sorry, {src.author.mention}. I'm afraid I can't let you do that."
            )

        await self.client.send_message(
            src.author, src.channel, "Please give a message to send (just reply below):"
        )
        try:
            msg = await self.client.wait_for(
                "message", check=same_author(src), timeout=30
            )
        except asyncio.TimeoutError:
            return "Timed out while waiting for message."

        else:
            try:
                warnEmbed = discord.Embed(
                    title="Official Warning",
                    description="The guild has sent you an official warning",
                    colour=0xFFF600,
                )

                warnEmbed.add_field(name="Reason", value=msg.content)
                warnEmbed.add_field(
                    name="Issuing Server", value=src.guild.name, inline=False
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
                    name="Issuer", value=src.author.name + "\n" + str(src.author.id)
                )
                logEmbed.add_field(
                    name="Recipient", value=userToWarn.name + "\n" + str(userToWarn.id)
                )
                logEmbed.add_field(name="Server", value=userToWarn.guild.name)
                logEmbed.add_field(name="Timestamp", value=str(dt.utcnow())[:-7])
                logEmbed.set_thumbnail(url=userToWarn.avatar_url)

                await self.client.embed(
                    self.client.get_channel(self.config.modChannel), logEmbed
                )
                return (
                    userToWarn.name
                    + " (ID: "
                    + str(userToWarn.id)
                    + ") was successfully warned"
                )

    async def cmd_mute(self, args, src: discord.Message, **_):
        """Toggle the mute tag on a user if your guild supports that role.

        Syntax: `{p}mute <user tag/id>`
        """
        if not args:
            return

        if not self.lambdall(args, lambda x: x.isdigit()):
            return "All IDs must be positive Integers."

        guild = self.client.main_guild
        userToMute = guild.get_member(int(args[0]))
        if userToMute is None:
            return "Could not get user with that ID."
        elif userToMute.id == self.client.user.id:
            return (
                f"I'm sorry, {src.author.mention}. I'm afraid I can't let you do that."
            )

        await self.client.send_message(
            src.author,
            src.channel,
            "Please give a reason for the mute (just reply below): ",
        )
        try:
            reason = await self.client.wait_for(
                "message", check=same_author(src), timeout=30
            )
        except asyncio.TimeoutError:
            return "Timed out while waiting for reason."

        muteRole = discord.utils.get(src.guild.roles, name="mute")
        if muteRole is None:
            return (
                "This guild does not have a `mute` role. To enable the mute "
                "function, set up the roles and name one `mute`."
            )
        else:
            try:

                if muteRole in userToMute.roles:
                    await self.client.remove_roles(userToMute, muteRole)
                    await self.client.guild_voice_state(userToMute, mute=False)
                    warnEmbed = discord.Embed(
                        title="User Unmute",
                        description="You have been unmuted by" + src.author.name,
                        colour=0x00FF11,
                    )

                    # warnEmbed.add_field(name="Reason", value=reason.content)
                    warnEmbed.add_field(
                        name="Issuing Server", value=src.guild.name, inline=False
                    )
                    muteswitch = "Unmute"
                else:
                    await self.client.add_roles(userToMute, muteRole)
                    await self.client.guild_voice_state(userToMute, mute=True)
                    warnEmbed = discord.Embed(
                        title="User Mute",
                        description="You have been muted by" + src.author.name,
                        colour=0xFF0000,
                    )
                    warnEmbed.set_author(
                        name=self.client.user.name,
                        icon_url="https://puu.sh/tB2KH/cea152d8f5.png",
                    )
                    warnEmbed.add_field(name="Reason", value=reason.content)
                    warnEmbed.add_field(
                        name="Issuing Server", value=src.guild.name, inline=False
                    )
                    muteswitch = "Mute"
                await self.client.embed(userToMute, warnEmbed)

            except discord.errors.Forbidden:
                return "It seems I don't have perms to mute this user"
            else:
                logEmbed = discord.Embed(
                    title="User {}".format(muteswitch),
                    description=reason.content,
                    colour=0x1200FF,
                )

                logEmbed.add_field(
                    name="Issuer", value=src.author.name + "\n" + src.author.id
                )
                logEmbed.add_field(
                    name="Recipient", value=userToMute.name + "\n" + userToMute.id
                )
                logEmbed.add_field(name="Server", value=userToMute.guild.name)
                logEmbed.add_field(name="Timestamp", value=str(dt.utcnow())[:-7])
                logEmbed.set_thumbnail(url=userToMute.avatar_url)

                await self.client.embed(
                    self.client.get_channel(self.config.modChannel), logEmbed
                )
                return (
                    userToMute.name
                    + " (ID: "
                    + userToMute.id
                    + ") was successfully {}d".format(muteswitch)
                )

    async def cmd_purge(self, args, src: discord.Message, **_):
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
        try:
            msg = await self.client.wait_for(
                "message", check=same_author(src), timeout=10
            )
        except asyncio.TimeoutError:
            msg = None

        if not msg or msg.content.lower() != "confirm":
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
                    src.guild.name,
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
        src: discord.Message,
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
                    message="Cannot find Message with id `{}` in channel `{}`.".format(
                        id_m, id_c
                    ),
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

    async def cmd_send(
        self, args, src: discord.Message, _identity: str = None, _i: str = None, **_
    ):
        """Broadcast an official-looking message into another channel.

        By using the Identity Option, you can specify who the message is from.
        Valid Identities:```\nadmins\nmods\nstaff```

        Syntax: `{p}send [OPTIONS] <channel-id> ["<message>"]`
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
                    "message", check=same_author(src), timeout=30
                )
            except asyncio.TimeoutError:
                return "Timed out while waiting for message."
            else:
                text = msg.content
        else:
            text = args[0]

        identity = (_identity or _i or "staff").lower()
        idents = {
            "admins": {"colour": 0xA2E46D, "title": "Administrative Alert"},
            "mods": {"colour": 0xE67E22, "title": "Moderation Message"},
            "staff": {"colour": 0x4CCDDF, "title": "Staff Signal"},
        }
        ident = idents.get(identity, idents["staff"])
        ident["description"] = text

        try:
            em = discord.Embed(**ident)
            await src.channel.send(
                content="Confirm sending this message to {} on behalf of {}? (Say `yes` to confirm)".format(
                    destination.mention, identity
                ), embed=em
            )
            try:
                confirm = await self.client.wait_for(
                    "message", check=same_author(src), timeout=10
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
            # logEmbed = discord.Embed(
            #     title="User Warn", description=msg.content, colour=0xFF600
            # )
            # logEmbed.set_author(
            #     name=self.client.user.name,
            #     icon_url="https://puu.sh/tADFM/dc80dc3a5d.png",
            # )
            # logEmbed.add_field(
            #     name="Issuer", value=src.author.name + "\n" + str(src.author.id)
            # )
            # logEmbed.add_field(
            #     name="Recipient", value=userToWarn.name + "\n" + str(userToWarn.id)
            # )
            # logEmbed.add_field(name="Server", value=userToWarn.guild.name)
            # logEmbed.add_field(name="Timestamp", value=str(dt.utcnow())[:-7])
            # logEmbed.set_thumbnail(url=userToWarn.avatar_url)
            #
            # await self.client.embed(
            #     self.client.get_channel(self.config.modChannel), logEmbed
            # )
            return (
                src.author.name
                + " (ID: `"
                + str(src.author.id)
                + "`) sent the following message to {} on behalf of `{}`:\n".format(
                    destination.mention, identity
                )
                + text
            )


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMod
