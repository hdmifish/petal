"""
An all around bot for discord
loosely based on functionality provided by leaf for Patch Gaming
written by isometricramen
"""

import asyncio
from datetime import datetime, timedelta
import random
import re
import time
from traceback import format_exc
from typing import AsyncGenerator, Coroutine, Generator, List, Optional

import discord

from petal import grasslands
from petal.commands import CommandRouter as Commands
from petal.commands.core import CommandPending
from petal.config import cfg
from petal.dbhandler import DBHandler
from petal.etc import mash
from petal.exceptions import TunnelHobbled, TunnelSetupError
from petal.tunnel import Tunnel
from petal.types import PetalClientABC, Src
from petal.util.cdn import get_avatar
from petal.util.embeds import membership_card
from petal.util.format import escape, mono_block, userline
from petal.util.grammar import pluralize
from petal.util.numbers import word_number


short_time: timedelta = timedelta(seconds=10)
log = grasslands.Peacock()

version = "<UNSET>"
with open("version_info.sh", "r") as f:
    for _line in f:
        if _line.startswith("VERSION="):
            version = _line.split("=", 1)[1].split("#")[0].strip(" \n\"'")

grasslands.version = version


def first_role_named(name: str, guild: discord.Guild):
    for role in guild.roles:
        if role.name == name:
            return role


class Petal(PetalClientABC):
    logLock = False

    def __init__(self, devmode=False):

        try:
            super().__init__()
        except Exception as e:
            log.err(f"Could not initialize client object: {str(e)}")
        else:
            log.info("Client object initialized")

        self.startup = datetime.utcnow()

        self.config = cfg
        self.db = DBHandler(self.config)
        self.startup = datetime.utcnow()
        self.commands = Commands(self)
        self.commands.version = version
        self.potential_typo = {}
        self.session_id = hex(mash(datetime.utcnow(), digits=5, base=16)).upper()
        self.tempBanFlag = False
        self.tunnels = []

        self.dev_mode = devmode
        log.info("Configuration object initalized")
        return

    def run(self):
        try:
            super().run(self.config.token, bot=not self.config.get("selfbot"))
        except AttributeError as e:
            log.err(f"Could not connect using the token provided: {str(e)}")
            exit(1)

        except discord.errors.LoginFailure as e:
            log.err(
                "Authenication Failure. Your auth: \n"
                + str(self.config.token)
                + " is invalid "
                + str(e)
            )
            exit(401)

    @property
    def uptime(self):
        return datetime.utcnow() - self.startup

    @staticmethod
    def is_pm(message):
        if message.channel.is_private:
            return True
        else:
            return False

    @staticmethod
    def remove_prefix(content):
        return content[len(content.split()[0]) :]

    @property
    def main_guild(self) -> discord.Guild:
        if len(self.guilds) == 0:
            log.err("This client is not a member of any guilds")
            exit(404)
        return self.get_guild(self.config.get("mainServer"))

    async def status_loop(self):
        interv = 32
        # times = {"start": self.startup.timestamp() * 1000}
        g_ses = discord.Activity(
            name=f"Session: {self.session_id[2:]}",
            # timestamps=times,
            type=discord.ActivityType.playing,
        )
        g_ver = discord.Activity(
            name=f"Version: {version}",
            # timestamps=times,
            type=discord.ActivityType.playing,
        )
        while True:
            await self.change_presence(
                activity=discord.Game(name=self.config.prefix + "info")
            )
            await asyncio.sleep(interv)
            await self.change_presence(activity=g_ses)
            await asyncio.sleep(interv)
            await self.change_presence(
                activity=discord.Game(name=f"Uptime: {str(self.uptime)[:-10]}")
            )
            await asyncio.sleep(interv)
            await self.change_presence(activity=g_ver)
            await asyncio.sleep(interv)

    async def save_loop(self):
        if self.dev_mode:
            return
        interval = self.config.get("autosaveInterval")
        while True:
            self.config.save()
            await asyncio.sleep(interval)

    async def ask_patch_loop(self):
        if self.dev_mode:
            return
        if self.config.get("motdInterval") is None:
            log.f("PA", "not using MOTD stuff...")
            return
        interval = self.config.get("motdInterval")
        while True:
            await self.commands.check_pa_updates()
            await asyncio.sleep(interval)

    async def ban_loop(self):
        # if self.dev_mode:
        #     return
        mainguild: discord.Guild = self.get_guild(self.config.get("mainServer"))
        interval = self.config.get("unbanInterval")
        log.f("BANS", f"Checking for temp unbans (Interval: {interval})")
        await asyncio.sleep(interval)
        while True:
            epoch = int(time.time())
            log.f("BANS", "Now Timestamp: " + str(epoch))

            for entry in await mainguild.bans():
                user = entry["user"]
                # log.f("UNBANS", m.name + "({})".format(m.id))
                ban_expiry = self.db.get_attribute(user, "banExpires", verbose=False)
                if ban_expiry is None or not self.db.get_attribute(user, "tempBanned"):
                    continue
                elif int(ban_expiry) <= int(epoch):
                    log.f(f"{ban_expiry} compared to {epoch}")
                    print(flush=True)
                    try:
                        await mainguild.unban(user, reason="Tempban Expired")
                    except discord.Forbidden:
                        log.f("BANS", f"Lacking permission to unban {user.id}.")
                    except discord.HTTPException as e:
                        log.f("BANS", f"FAILED to unban {user.id}: {e}")
                    else:
                        self.db.update_member(user, {"banned": False})
                        log.f("BANS", f"Unbanned {user.name} ({user.id}) ")
                else:
                    log.f(
                        "BANS",
                        user.name
                        + f" ({user.id}) has {int(ban_expiry) - int(epoch)} seconds left",
                    )
                await asyncio.sleep(0.5)

            await asyncio.sleep(interval)

    async def close_tunnels_to(self, channel):
        """Given a Channel, remove it from any/all Tunnels connecting to it."""
        for t in self.tunnels:
            await t.drop(channel)

    async def dig_tunnel(self, origin, *channels: List[int], anon=False):
        """Create a new Tunnel.
            The first Positional Argument is the Origin Channel, the Channel to
            which to report back in case of problems. All subsequent Positional
            Arguments are Integer IDs.
        """
        new = Tunnel(self, origin, *channels, anon)
        try:
            tunnel_coro = new.activate()
        except TunnelSetupError:
            return False
        else:
            self.tunnels.append(new)
            await tunnel_coro

    def get_tunnel(self, channel):
        """Given a Channel, return the first Tunnel connected to it, if any."""
        for t in self.tunnels:
            if channel in t.connected:
                return t

    async def kill_tunnel(self, t: Tunnel):
        """Given a Tunnel, kill it. Duh."""
        if t:
            await t.kill()

    def remove_tunnel(self, t: Tunnel):
        """Given a dead Tunnel, remove it from the Client Tunnels."""
        if t.active:
            raise TunnelHobbled("Cannot Remove a Tunnel which is still active.")
        while t in self.tunnels:
            self.tunnels.remove(t)

    async def on_member_ban(self, member):
        print("Giving database a chance to sync...")
        await asyncio.sleep(1)

        if not self.db.member_exists(member):
            return
        banstate = self.db.get_attribute(member, "tempBanned")
        if banstate:
            print(f"Member{member.name}({member.id}) tempbanned, ignoring")
            return

        self.db.update_member(member, {"tempBanned": False})
        print(f"Member {member.name} ({member.id}) was banned manually")

    async def on_ready(self):
        """
        Called once a connection has been established
        """
        log.ready(f"Running discord.py version: {discord.__version__}")
        log.ready("Connected to Discord!")
        log.info(
            f"Logged in as {self.user.name}#{self.user.discriminator} ({self.user.id})"
        )
        log.info(f"Prefix: {self.config.prefix}")
        log.info(f"SelfBot: {['true', 'false'][self.config.useToken]}")

        self.loop.create_task(self.status_loop())
        log.ready("Gamestatus coroutine running...")
        self.loop.create_task(self.save_loop())
        log.ready("Autosave coroutine running...")
        self.loop.create_task(self.ban_loop())
        log.ready("Auto-unban coroutine running...")
        if self.config.get("dbconf") is not None:
            self.loop.create_task(self.ask_patch_loop())
            log.ready("MOTD system running...")
            pass
        else:
            log.warn(
                "No dbconf configuration in config.yml, motd features are disabled"
            )
        return

    async def print_response(self, src: Src, response, to_edit: discord.Message = None):
        """Use a discrete method for this, so that it can be used recursively if
            needed.

        Return Types of Command Methods:
        def, return         ->  Any             - send(value)
        def, yield          ->  Generator       - for x in value: send(x)
        async def, return   ->  Coroutine       - recurse(await value)
        async def, yield    ->  AsyncGenerator  - async for x in value: send(x)
        """
        # print("Outputting Response:", repr(response))
        while isinstance(response, Coroutine):
            # Ensure that the Response is actually final.
            response = await response
            # print("Awaited Response:", repr(response))

        if response is None:
            # Ignore Void Responses.
            return

        elif isinstance(response, (AsyncGenerator, Generator, list, tuple)):
            # Response is a Generator, indicating the method used Yielding, or a
            #   List or Tuple, which should be treated the same. Yield command
            #   returns support flushing and clearing the List of Buffered
            #   Lines, with True and False, respectively.
            # print("Iterating Type:", type(response))
            if to_edit:
                # Due to the ability to chain multiple messages by yielding, we
                #   cannot cleanly take advantage of editing. Delete it.
                await to_edit.delete()

            buffer: list = []

            async def push(line):
                # print("  Reading Line:", repr(line))
                if line is True:
                    # Upon reception of True, "flush" the current "buffer" by
                    #   posting a Message.
                    # print("    Printing Buffer:", repr(buffer))
                    if buffer:
                        await self.print_response(src, "\n".join(map(str, buffer)))
                        buffer.clear()

                elif line is False:
                    # Upon reception of False, discard the buffer.
                    # print("    Discarding Buffer:", repr(buffer))
                    buffer.clear()

                elif isinstance(line, (dict, discord.Embed)):
                    # Upon reception of a Dict or an Embed, send it in a Message
                    #   immediately.
                    await self.print_response(src, line)

                elif isinstance(line, (list, tuple)):
                    # Upon reception of a List or Tuple, treat it the same as
                    #   reception of its elements in sequence.
                    for elem in line:
                        await push(elem)

                else:
                    # Anything else is added to the buffer.
                    # print("    Appending to Buffer.")
                    buffer.append(line)

            if isinstance(response, AsyncGenerator):
                async for y in response:
                    await push(y)

            elif isinstance(response, (Generator, list, tuple)):
                for y in response:
                    await push(y)

            # print("Iterator Exhausted; Flushing Buffer.")
            if buffer:
                # print("Printing Final Buffer:", repr(buffer))
                await push(True)
                # await self.print_response(message, "\n".join(map(str, buffer)))

            del buffer

        elif isinstance(response, dict):
            # If the response is a Dict, it is a series of keyword arguments
            #   intended to be passed directly to `Channel.send()`.
            # print("Building from Dict.")
            if to_edit:
                vals = {"content": None, "embed": None}
                vals.update(response)
                await to_edit.edit(**vals)
            else:
                await src.channel.send(**response)

        elif isinstance(response, discord.Embed):
            # If the response is an Embed, simply show it as normal.
            # print("Sending Embed.")
            if to_edit:
                await to_edit.edit(content=None, embed=response)
            else:
                await src.channel.send(embed=response)

        elif isinstance(response, str):
            # Same with String.
            # print("Sending String.")
            if to_edit:
                await to_edit.edit(content=response, embed=None)
            else:
                await self.send_message(src.author, src.channel, str(response))

        else:
            # And everything else.
            # print("Sending Other.")
            if to_edit:
                await to_edit.edit(content=repr(response), embed=None)
            else:
                await self.send_message(src.author, src.channel, str(response))

    async def execute_command(self, message):
        command = self.potential_typo.get(message.id) or CommandPending(
            self.potential_typo, self.print_response, self.commands, message
        )
        await asyncio.sleep(0.1)
        try:
            return await command.run()

        except Exception as e:
            if isinstance(command.channel, discord.TextChannel):
                await self.log_moderation(
                    embed=discord.Embed(
                        title="Unhandled Exception in Command",
                        description=escape(command.src.content),
                    )
                    .add_field(
                        name="Author",
                        value=f"{command.invoker.mention}"
                        f"\n`{command.invoker.name}#{command.invoker.discriminator}`"
                        f"\n`{command.invoker.id}`",
                    )
                    .add_field(
                        name="Location",
                        value=f"{command.channel.mention}"
                        f"\n`#{command.channel.name}`"
                        f"\n`{command.channel.guild.name}`",
                    )
                    .add_field(
                        name=type(e).__name__,
                        value=str(e) or "<No Details>",
                        inline=False,
                    )
                    .add_field(
                        name="Exception Traceback",
                        value=mono_block(format_exc()),
                        inline=False,
                    )
                )

    async def send_message(
        self, author=None, channel=None, message=None, *, embed=None, **_
    ):
        """
        Overload on the send_message function
        """
        if (not message or not str(message)) and not embed:
            # Without a message to send, dont even try; it would just error
            return None
        message = str(message)

        if (
            author is not None
            and self.db.get_member(author) is not None
            and self.db.get_attribute(author, "ac")
        ):
            try:
                ac = list(self.db.ac.find())
                ac = ac[random.randint(0, len(ac) - 1)]["ending"]
                i = 0
                while message[-(i + 1)] in " ,.…¿?¡!":
                    i += 1

                msg, end = (message[:-i], message[-i:]) if i > 0 else (message, "")
            except:
                pass
            else:
                message = msg + ", " + ac + end

        if self.dev_mode:
            message = "[DEV]  " + str(message) + "  [DEV]"
        try:
            return await channel.send(content=message, embed=embed)
        except discord.errors.InvalidArgument:
            log.err(
                "A message: " + message + " was unable to be sent in " + channel.name
            )
            return None
        except discord.errors.Forbidden:
            log.err(
                "A message: "
                + message
                + " was unable to be sent in channel: "
                + channel.name
            )
            return None

    async def log_membership(
        self, content: str = None, *, embed: discord.Embed = None
    ) -> Optional[discord.Message]:
        channel: discord.abc.Messageable = self.get_channel(
            self.config.get("logChannel", 0)
        )
        if not channel:
            log.err("Cannot post message to 'logChannel'.")
            return None
        else:
            if content is not None and embed is not None:
                return await channel.send(content, embed=embed)
            elif content is not None:
                return await channel.send(content)
            elif embed is not None:
                return await channel.send(embed=embed)
            else:
                return None

    async def log_moderation(
        self, content: str = None, *, embed: discord.Embed = None
    ) -> Optional[discord.Message]:
        channel: discord.abc.Messageable = self.get_channel(
            self.config.get("modChannel", 0)
        )
        if not channel:
            log.err("Cannot post message to 'modChannel'.")
            return None
        else:
            if content is not None and embed is not None:
                return await channel.send(content, embed=embed)
            elif content is not None:
                return await channel.send(content)
            elif embed is not None:
                return await channel.send(embed=embed)
            else:
                return None

    async def embed(
        self,
        channel: discord.abc.Messageable,
        embedded: discord.Embed,
        content: str = None,
    ):
        if self.dev_mode:
            embedded.add_field(name="DEV", value="DEV")

        if not channel:
            raise RuntimeError("Channel not provided.")

        if content is not None:
            return await channel.send(content=content, embed=embedded)
        else:
            return await channel.send(embed=embedded)

    async def on_member_join(self, member):
        """To be called When a new member joins the server"""
        card = membership_card(member, colour=0x_00_FF_00)

        if self.db.member_exists(member):
            # This User has been here before.
            card.set_author(name="Returning Member")
        else:
            # We have no previous record of this User.
            self.db.add_member(member)
            card.set_author(name="New Member")

        self.db.update_member(
            member, {"aliases": [member.name], "guilds": [member.guild.id]}
        )

        welcome = self.config.get("welcomeMessage", None)
        if welcome and welcome != "null":
            try:
                await member.send(welcome)
            except Exception as e:
                card.add_field(
                    name="Welcome",
                    value=f"User could not be sent a Welcome Message:"
                    f" {type(e).__name__}: {e}",
                )
            else:
                card.add_field(
                    name="Welcome", value="User was sent a Welcome Message in DM."
                )
        else:
            card.add_field(name="Welcome", value="No Welcome Message is configured.")

        # Wait a short time before posting. This should hopefully make the
        #   mention tag more reliable.
        await asyncio.sleep(3)
        await self.log_membership(embed=card)

    async def on_member_remove(self, member):
        """To be called when a member leaves"""
        card = membership_card(member, colour=0x_FF_00_00)
        card.set_author(
            name="Member Left", icon_url="https://puu.sh/tB7bp/f0bcba5fc5.png"
        )

        # Wait for at least as long as the Join delay, so that the Part Message
        #   will never be posted before the Join Message.
        await asyncio.sleep(4)
        await self.log_membership(embed=card)

    async def on_message_delete(self, message: discord.Message):
        try:
            if message.channel.id in self.config.get(
                "ignoreChannels", []
            ) or not isinstance(message.channel, discord.TextChannel):
                return

            now = datetime.utcnow()
            guild: discord.Guild = message.guild

            executor = None
            reason = None
            try:
                async for record in guild.audit_logs(
                    limit=10,
                    after=now - short_time,
                    oldest_first=False,
                    action=discord.AuditLogAction.message_delete,
                ):
                    if (
                        record.target == message.author
                        and record.extra.channel.id == message.channel.id
                    ):
                        executor = record.user
                        reason = record.reason
                        break
            except (discord.Forbidden, discord.HTTPException):
                can_audit = False
            else:
                can_audit = True

            em = discord.Embed(
                title="Message Deleted",
                description=f"A Message by {message.author.mention} was deleted."
                f"\nMessage URL: {message.jump_url}",
                colour=0xFC00A2,
            )
            em.set_author(
                name=message.author.display_name, icon_url=get_avatar(message.author)
            )
            em.set_footer(text=f"{userline(message.author)}")
            # em.set_thumbnail(url=get_avatar(message.author))

            if message.content:
                em.add_field(
                    name="Content", value=escape(message.content), inline=False
                )
            if message.embeds:
                n = len(message.embeds)
                em.add_field(
                    name="Embeds",
                    value=f"Message had {word_number(n)} ({n})"
                    f" {pluralize(n, 'Embed')}.",
                    inline=False,
                )
            if message.attachments:
                n = len(message.attachments)
                em.add_field(
                    name="Attachments",
                    value=f"Message had {word_number(n)} ({n})"
                    f" {pluralize(n, 'Attachment')}.",
                    inline=False,
                )

            em.add_field(name="Guild", value=guild.name)
            em.add_field(
                name="Channel",
                value=f"`#{message.channel.name}`\n{message.channel.mention}",
            )

            if can_audit:
                if executor is None:
                    em.add_field(
                        name="Deleter",
                        value="Message was probably deleted by __the Author__.",
                        inline=False,
                    )
                else:
                    em.add_field(
                        name="Deleter",
                        value=f"Message was probably deleted by:"
                        f"\n`{escape(userline(executor))}`"
                        f"\n{executor.mention}",
                        inline=False,
                    )
            else:
                em.add_field(
                    name="Deleter",
                    value="Insufficient Permissions to find Deleter.",
                    inline=False,
                )

            if reason is not None:
                em.add_field(name="Reason for Deletion", value=reason, inline=False)

            em.add_field(name="Time of Creation", value=str(message.created_at)[:-7])
            em.add_field(name="Time of Deletion", value=str(now)[:-7])

            await self.log_moderation(embed=em)
        except discord.errors.HTTPException:
            return

    async def on_message_edit(self, before: Src, after: Src):
        if (
            Petal.logLock
            or before.content == ""
            or not isinstance(before.channel, discord.TextChannel)
        ):
            return

        if before.guild.id in self.config.get(
            "ignoreServers"
        ) or before.channel.id in self.config.get("ignoreChannels"):
            return

        if after.content == "":
            return
        if before.content == after.content:
            return

        edit_time = datetime.utcnow()

        # If the message was marked as a possible typo by the command router,
        #   try running it again.
        executed = before.id in self.potential_typo and await self.execute_command(
            after
        )

        userEmbed = (
            discord.Embed(
                title="Message Edit with command execution"
                if executed
                else "Message Edit",
                description=before.author.name
                + "#"
                + before.author.discriminator
                + " edited their message",
                colour=0xAE00FE,
            )
            .add_field(name="Server", value=before.guild.name)
            .add_field(name="Channel", value=before.channel.name)
            .add_field(
                name="Previous message: ", value=escape(before.content), inline=False
            )
            .add_field(name="Edited message: ", value=escape(after.content))
            .add_field(name="Timestamp", value=str(edit_time)[:-7], inline=False)
            .set_footer(text=userline(before.author))
        )

        try:
            await self.log_moderation(embed=userEmbed)
        except discord.errors.HTTPException:
            log.warn(
                "HTTP 400 error from the edit statement. "
                + "Usually it's safe to ignore it"
            )

            return

    async def on_member_update(self, before, after):
        if Petal.logLock:
            return
        gained = None
        role = None

        for r in before.roles:
            if r not in after.roles:
                gained = "Lost"
                role = r
        for r in after.roles:
            if r not in before.roles:
                gained = "Gained"
                role = r

        if not role:
            return

        if gained is not None:
            userEmbed = discord.Embed(
                title=f"({role.guild.name}) User Role {gained}",
                description=f"{after.name}#{after.discriminator} {gained} role",
                colour=0x0093C3,
            )
            userEmbed.set_author(
                name=self.user.name, icon_url="https://puu.sh/tBpXd/ffba5169b2.png"
            )
            userEmbed.add_field(name="Role", value=role.name)
            userEmbed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7])
            await self.log_moderation(embed=userEmbed)

        if before.name != after.name:
            userEmbed = discord.Embed(
                title="User Name Change",
                description=f"{escape(before.name)} changed their name to {escape(after.name)}",
                colour=0x34F3AD,
            )

            userEmbed.add_field(name="UUID", value=str(before.id))

            userEmbed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7])

            await self.log_moderation(embed=userEmbed)

    # async def on_voice_state_update(self, before, after):
    #
    #     # FIXME: This needs to have a limiter. Use at own risk of spam.
    #     if self.config.tc is None:
    #         return
    #     else:
    #         return
    #     tc = self.config.tc
    #     trackedChan = self.get_channel(tc["monitoredChannel"])
    #     postChan = self.get_channel(tc["destinationChannel"])
    #     if trackedChan is None:
    #         log.err("Invalid tracking channel. Function disabled")
    #         self.config.tc = None
    #         return
    #     if postChan is None:
    #         log.err("Invalid posting channel. Function disabled")
    #         self.config.tc = None
    #         return
    #     if before.voice_channel != trackedChan and after.voice_channel == trackedChan:
    #         try:
    #             await self.send_message(None, after, tc["messageToUser"])
    #         except discord.errors.HTTPException:
    #             log.warn("Unable to PM {}".format(before.name))
    #         else:
    #             msg = await self.wait_for_message(
    #                 author=after, check=self.is_pm, timeout=200
    #             )
    #             if msg is None:
    #                 return
    #             else:
    #                 if msg.content.lower() in [
    #                     "yes",
    #                     "confirm",
    #                     "please",
    #                     "yeah",
    #                     "yep",
    #                     "mhm",
    #                 ]:
    #                     await self.send_message(
    #                         None,
    #                         postChan,
    #                         tc["messageFormat"].format(
    #                             user=after, channel=after.voice_channel
    #                         ),
    #                     )
    #                 else:
    #                     await self.send_message(
    #                         None,
    #                         channel,
    #                         "Alright, just to let"
    #                         + "you know. If you "
    #                         + "have a spotty "
    #                         + "connection, you may"
    #                         + " get PM'd more than "
    #                         + "once upon joining"
    #                         + " this channel",
    #                     )
    #                 return

    async def on_message(self, message: Src):
        await self.wait_until_ready()
        content = message.content.strip()
        if isinstance(message.channel, discord.TextChannel):
            self.db.update_member(
                message.author,
                {
                    "aliases": message.author.name,
                    "guilds": message.guild.id,
                    "last_message_channel": message.channel.id,
                    "last_active": message.created_at,
                    "last_message": message.created_at,
                },
                type=1,
            )

            self.db.update_member(
                message.author,
                {
                    "message_count": self.db.get_attribute(
                        message.author, "message_count"
                    )
                    + 1
                },
            )

        if (
            message.author == self.user
            or message.content == self.config.prefix
            or message.author.id in self.config.blacklist
        ):
            return

        for word in message.content.split():
            if message.channel.id in self.config.get("ignoreChannels"):
                break
            if word in self.config.wordFilter:
                embed = discord.Embed(
                    title="Word Filter Hit",
                    description="At least one filtered word was detected",
                    colour=0x9F00FF,
                )

                embed.add_field(
                    name="Author",
                    value=message.author.name + "#" + message.author.discriminator,
                )
                embed.add_field(name="Channel", value=message.channel.name)
                embed.add_field(name="Server", value=message.guild.name)
                embed.add_field(name="Content", value=message.content)
                embed.add_field(name="Detected word", value=word, inline=False)
                embed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7])
                embed.set_thumbnail(url=message.author.avatar_url)
                await self.log_moderation(embed=embed)
                break

        role_member = first_role_named(
            self.config.get("roleGrant")["role"], self.main_guild
        )
        if (
            role_member
            and message.channel.id == self.config.get("roleGrant")["chan"]
            and role_member not in message.author.roles
        ):
            try:
                if self.config.get("roleGrant")["ignorecase"]:
                    check = re.compile(
                        self.config.get("roleGrant")["regex"], re.IGNORECASE
                    )
                else:
                    check = re.compile(self.config.get("roleGrant")["regex"])

                if check.match(message.content):
                    await self.send_message(
                        None, message.channel, self.config.get("roleGrant")["response"]
                    )
                    await message.author.add_roles(
                        role_member, reason="Message matched the Agreement regex."
                    )
                    log.member(
                        message.author.name
                        + " (id: "
                        + str(message.author.id)
                        + ") was given access"
                    )
                    return

            except Exception as e:
                await self.send_message(
                    None,
                    message.channel,
                    "Something went wrong with granting"
                    + " your role. Pm a member of staff "
                    + str(e),
                )
                raise e

        if not self.config.pm and isinstance(
            message.channel, discord.abc.PrivateChannel
        ):
            if not message.author == self.user:
                # noinspection PyTypeChecker
                await self.send_message(
                    None,
                    message.channel,
                    "Petal has been configured by staff"
                    + " to not respond to PMs right now",
                )
            return

        replies = self.config.get("autoreplies") or {}
        if content in replies:
            if not message.author == self.user:
                reply = replies.get(content, "").format(
                    user=message.author, self=self.user
                )
                if reply:
                    await self.send_message(None, message.channel, reply)
            return

        # For now, do all the above checks and then run/route it.
        # This may result in repeating some checks, but these checks should
        #     eventually be moved into the commands module itself.
        if message.content.startswith(self.config.prefix):
            await self.execute_command(message)
