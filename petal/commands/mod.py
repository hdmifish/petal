"""Commands module for MODERATION UTILITIES.
Access: Role-based"""

import asyncio
from datetime import datetime as dt, timedelta
from operator import attrgetter
import time

import discord

from petal import checks
from petal.commands import core, shared
from petal.etc import lambdall, mash
from petal.exceptions import (
    CommandArgsError,
    CommandExit,
    CommandInputError,
    CommandOperationError,
)
from petal.menu import confirm_action, Menu
from petal.types import Src
from petal.util.embeds import membership_card
from petal.util.format import bold, escape, mono, underline, userline


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
            raise CommandOperationError(
                "Database is not configured correctly (or at all)."
                " Contact your bot developer and tell them if you think"
                " this is an error."
            )

        if member is None:
            raise CommandOperationError(
                "Could not find that member in the guild.\n\nJust a note,"
                " I may have record of them, but it's Iso's policy to not"
                " display userinfo without consent. If you are staff and"
                " have a justified reason for this request, please"
                " ask whoever hosts this bot to manually look up the"
                " records in their database."
            )

        self.db.add_member(member)

        alias = self.db.get_attribute(member, "aliases")
        if not alias:
            yield "This member has no known aliases."
        else:
            yield underline(f"Aliases of User `{member.id}`:")

            for a in alias:
                yield bold(a)

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
        `--reason <str>` :: Provide a reason immediately, rather than typing a reason in a subsequent message.
        `--noconfirm` :: Perform the action immediately, without asking to make sure. ***This can get you in trouble if you mess up with it.***
        """
        if not args:
            raise CommandArgsError("No User specified.")

        if not lambdall(args, lambda x: x.isdigit()):
            raise CommandInputError("All IDs must be positive Integers.")

        guild: discord.Guild = self.client.main_guild
        target: discord.Member = guild.get_member(int(args[0]))
        if target is None:
            raise CommandInputError("Could not get user with that ID.")
        elif target.id == self.client.user.id:
            raise CommandOperationError(
                f"I'm sorry, {src.author.mention}. I'm afraid I can't let you do that."
            )

        if _reason is None:
            await self.client.send_message(
                src.author, src.channel, "Please give a reason (just reply below): "
            )
            try:
                reason = await self.client.wait_for(
                    "message",
                    check=checks.all_checks(
                        checks.Messages.by_user(src.author),
                        checks.Messages.in_channel(src.channel),
                    ),
                    timeout=30,
                )
            except asyncio.TimeoutError:
                raise CommandOperationError("Timed out while waiting for reason.")
            _reason = reason.content

        targline: str = mono(userline(target))

        if not _noconfirm:
            confirm = await confirm_action(
                self.client,
                src,
                "Member Kick",
                f"Confirm kicking {targline} from {target.guild.name}?",
            )
            if confirm is not True:
                if confirm is False:
                    raise CommandExit("Kick was cancelled.")
                else:
                    raise CommandExit("Confirmation timed out.")

        try:
            await target.kick(reason=_reason)
        except discord.errors.Forbidden:
            raise CommandOperationError(
                "It seems I don't have perms to kick this user."
            )

        else:
            logEmbed = (
                discord.Embed(title="User Kick", description=_reason, colour=0xFF7900)
                .set_author(
                    name=src.author.display_name, icon_url=src.author.avatar_url
                )
                .add_field(name="Issuer", value=mono(userline(src.author)))
                .add_field(name="Recipient", value=targline)
                .add_field(name="Guild", value=target.guild.name)
                .add_field(name="Timestamp", value=str(dt.utcnow())[:-7])
                .set_thumbnail(url=target.avatar_url)
            )

            await self.client.log_moderation(embed=logEmbed)
            return f"Successfully Kicked: {targline}"

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
        `--reason <str>` :: Provide a reason immediately, rather than typing a reason in a subsequent message.
        `--purge <int>` :: Determine how many days of messages by the banned user to delete. Default is 1. Can be between 0 and 7, inclusive.
        `--noconfirm` :: Perform the action immediately, without asking to make sure. ***This can get you in trouble if you mess up with it.***
        """
        if not args:
            return

        if not lambdall(args, lambda x: x.isdigit()):
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
                    "message",
                    check=checks.all_checks(
                        checks.Messages.by_user(src.author),
                        checks.Messages.in_channel(src.channel),
                    ),
                    timeout=30,
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
                    "message",
                    check=checks.all_checks(
                        checks.Messages.by_user(src.author),
                        checks.Messages.in_channel(src.channel),
                    ),
                    timeout=30,
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
        `--reason <str>` :: Provide a reason immediately, rather than typing a reason in a subsequent message.
        `--purge <int>` :: Determine how many days of messages by the banned user to delete. Default is 1. Can be between 0 and 7, inclusive.
        `--days <int>` :: Provide a ban duration immediately, rather than typing a number of days in a subsequent message.
        """
        if not args:
            return

        if not lambdall(args, lambda x: x.isdigit()):
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
                    "message",
                    check=checks.all_checks(
                        checks.Messages.by_user(src.author),
                        checks.Messages.in_channel(src.channel),
                    ),
                    timeout=30,
                )
            except asyncio.TimeoutError:
                return "Timed out while waiting for reason."
            _reason = reason.content

        if not _days:
            await self.client.send_message(src.author, src.channel, "How long? (days) ")
            try:
                msg2 = await self.client.wait_for(
                    "message",
                    check=(
                        lambda x: checks.all_checks(
                            checks.Messages.by_user(src.author),
                            checks.Messages.in_channel(src.channel),
                        )(x)
                        and x.content.isdigit()
                    ),
                    timeout=30,
                )
            except asyncio.TimeoutError:
                return "Timed out while waiting for input"
            _days = int(msg2.content)

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

        if not lambdall(args, lambda x: x.isdigit()):
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
            raise CommandArgsError("Must provide User ID.")

        if not lambdall(args, lambda x: x.isdigit()):
            raise CommandArgsError("All IDs must be positive Integers.")

        target: discord.Member = self.client.main_guild.get_member(int(args[0]))
        if target is None:
            raise CommandInputError(f"Could not get user with ID `{int(args[0])}`.")
        elif target.id == self.client.user.id:
            raise CommandInputError(
                f"I'm sorry, {src.author.mention}. I'm afraid I can't let you do that."
            )

        await self.client.send_message(
            src.author,
            src.channel,
            "Please give a reason for the mute (just reply below): ",
        )
        try:
            reason = await self.client.wait_for(
                "message",
                check=checks.all_checks(
                    checks.Messages.by_user(src.author),
                    checks.Messages.in_channel(src.channel),
                ),
                timeout=30,
            )
        except asyncio.TimeoutError:
            raise CommandOperationError("Timed out while waiting for reason.")

        role_mute: discord.Role = discord.utils.get(src.guild.roles, name="mute")
        if role_mute is None:
            raise CommandOperationError(
                "This guild does not have a `mute` role. To enable the mute "
                "function, set up the roles and name one `mute`."
            )
        else:
            try:
                if role_mute in target.roles:
                    await target.remove_roles(role_mute, reason)
                    # await self.client.guild_voice_state(target, mute=False)

                    warnEmbed = discord.Embed(
                        title="User Unmute",
                        description=f"You have been unmuted by {src.author.name}.",
                        colour=0x00FF11,
                    )
                    warnEmbed.set_author(
                        name=self.client.user.name,
                        icon_url="https://puu.sh/tB2KH/cea152d8f5.png",
                    )
                    # warnEmbed.add_field(name="Reason", value=reason.content)
                    warnEmbed.add_field(
                        name="Issuing Server", value=src.guild.name, inline=False
                    )
                    muteswitch = "Unmute"

                else:
                    await target.add_roles(role_mute, reason)
                    # await self.client.guild_voice_state(target, mute=True)

                    warnEmbed = discord.Embed(
                        title="User Mute",
                        description=f"You have been muted by {src.author.name}.",
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

            except discord.errors.Forbidden:
                raise CommandOperationError(
                    "It seems I don't have permission to mute this user."
                )
            else:
                yield f"{target.name}  (ID: {target.id}) was successfully {muteswitch}d"

                try:
                    await target.send(embed=warnEmbed)
                except discord.errors.Forbidden:
                    yield (
                        f"  (FAILED to send a DM notification to user `{target.id}`.)",
                        True,
                    )
                else:
                    yield (
                        f"  (A notification was sent in DM to user `{target.id}`.)",
                        True,
                    )

                logEmbed = discord.Embed(
                    title=f"User {muteswitch}",
                    description=reason.content,
                    colour=0x1200FF,
                )

                logEmbed.add_field(
                    name="Issuer", value=src.author.name + "\n" + src.author.id
                )
                logEmbed.add_field(
                    name="Recipient", value=target.name + "\n" + target.id
                )
                logEmbed.add_field(name="Server", value=target.guild.name)
                logEmbed.add_field(name="Timestamp", value=str(dt.utcnow())[:-7])
                logEmbed.set_thumbnail(url=target.avatar_url)

                await self.client.log_moderation(embed=logEmbed)

    async def cmd_purge(self, args, src: Src, **_):
        """Purge up to 200 messages in the current channel.

        Syntax: `{p}purge <number of messages to delete>`
        """
        if len(args) < 1:
            raise CommandArgsError("Please provide a number between 1 and 200")
        try:
            delete_num = int(args[0].strip())
        except ValueError:
            raise CommandInputError("Please make sure your input is a number")
        if not 0 < delete_num <= 200:
            raise CommandInputError("Can only delete between 0 and 200 Messages.")

        confirm_menu: Menu = Menu(
            self.client,
            src.channel,
            "Confirm Purge",
            f"Really delete the last {delete_num} Messages in this Channel?\n"
            f"(This Menu and your Invocation will also be deleted.)",
            src.author,
        )
        confirmed = await confirm_menu.get_bool()

        if confirmed is True:
            try:
                await src.channel.purge(limit=delete_num + 2, check=None)
            except discord.errors.Forbidden:
                raise CommandOperationError(
                    "I don't have permissions to purge messages."
                )
            else:
                logEmbed = discord.Embed(
                    title="Purge Event",
                    description=f"{delete_num} messages were purged from "
                    f"`#{src.channel.name}` in {src.guild.name} by "
                    f"`{src.author.name}#{src.author.discriminator}`.",
                    color=0x0ACDFF,
                )
                await self.client.log_moderation(embed=logEmbed)

        elif confirmed is False:
            await confirm_menu.add_section("Purge Cancelled.")
            await confirm_menu.post()
        else:
            await confirm_menu.add_section("Confirmation Timed Out.")
            await confirm_menu.post()

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

            ct = escape(message.content if _preserve or _p else message.clean_content)
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

    cmd_send = shared.factory_send(
        {
            "mods": {"colour": 0xE67E22, "title": "Moderation Message"},
            "staff": {"colour": 0x4CCDDF, "title": "Staff Signal"},
        },
        "mods",
    )

    async def cmd_userinfo(self, args, src: Src, **_):
        """Toggle the mute tag on a user if your guild supports that role.

        Syntax: `{p}mute <user tag/id>`
        """
        if not args:
            raise CommandArgsError("Must provide User ID.")

        if not all(map(lambda x: x.isdigit(), args)):
            raise CommandArgsError("All IDs must be positive Integers.")

        for userid in args:
            target: discord.Member = src.guild.get_member(
                int(userid)
            ) or self.client.main_guild.get_member(int(userid))

            if target is None:
                raise CommandInputError(f"Could not get user with ID `{int(args[0])}`.")
            else:
                await src.channel.trigger_typing()
                yield membership_card(target)


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMod
