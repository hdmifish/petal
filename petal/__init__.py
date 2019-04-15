"""
An all around bot for discord
loosely based on functionality provided by leaf for Patch Gaming
written by isometricramen
"""

import asyncio
from collections import deque
from datetime import datetime
import random
import re
import time

import discord

from petal import grasslands
from petal.commands import CommandRouter as Commands
from petal.config import Config
from petal.dbhandler import DBHandler


# from random import randint
log = grasslands.Peacock()

version = "0.0.0"
with open("version_info.sh", "r") as f:
    inf = f.read()
    inf = inf.split("VERSION=", 1)[-1].split("\n", 1)[0]
    if inf:
        version = inf

grasslands.version = version


class Petal(discord.Client):
    logLock = False

    def __init__(self, devmode=False):

        try:
            super().__init__()
        except Exception as e:
            log.err("Could not initialize client object: " + str(e))
        else:
            log.info("Client object initialized")

        self.config = Config()
        self.db = DBHandler(self.config)
        self.commands = Commands(self)
        self.commands.version = version
        self.potential_typoed_commands = deque([], 3)
        self.tempBanFlag = False

        self.dev_mode = devmode
        log.info("Configuration object initalized")
        return

    def run(self):
        try:
            super().run(self.config.token, bot=not self.config.get("selfbot"))
        except AttributeError as e:
            log.err("Could not connect using the token provided: " + str(e))
            exit(1)

        except discord.errors.LoginFailure as e:
            log.err(
                "Authenication Failure. Your auth: \n"
                + str(self.config.token)
                + " is invalid "
                + str(e)
            )
            exit(401)
        return

    @staticmethod
    def is_pm(message):
        if message.channel.is_private:
            return True
        else:
            return False

    @staticmethod
    def remove_prefix(content):
        return content[len(content.split()[0]) :]

    def get_main_server(self):
        if len(self.servers) == 0:
            log.err("This client is not a member of any servers")
            exit(404)
        return self.config.get("mainServer")

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
        mainserver = self.get_server(self.config.get("mainServer"))
        interval = self.config.get("unbanInterval")
        log.f("BANS", "Checking for temp unbans (Interval: " + str(interval) + ")")
        await asyncio.sleep(interval)
        while True:
            epoch = int(time.time())
            log.f("BANS", "Now Timestamp: " + str(epoch))

            banlist = await self.get_bans(mainserver)

            for m in banlist:
                # log.f("UNBANS", m.name + "({})".format(m.id))
                ban_expiry = self.db.get_attribute(m, "banExpires", verbose=False)
                if ban_expiry is None:
                    continue
                if not self.db.get_attribute(m, "tempBanned"):
                    print(
                        "Member {}({}) was not tempbanned. Skipping".format(
                            m.name, m.id
                        )
                    )
                    continue
                elif int(ban_expiry) <= int(epoch):
                    log.f(str(ban_expiry) + " compared to " + str(epoch))
                    print(flush=True)
                    await self.unban(mainserver, m)
                    self.db.update_member(m, {"banned": False})
                    log.f("BANS", "Unbanned " + m.name + " ({}) ".format(m.id))

                else:
                    log.f(
                        "BANS",
                        m.name
                        + " ({}) has {} seconds left".format(
                            m.id, str((int(ban_expiry) - int(epoch)))
                        ),
                    )
                await asyncio.sleep(0.5)

            await asyncio.sleep(interval)

    async def on_member_ban(self, member):
        print("Giving database a chance ot sync...")
        await asyncio.sleep(1)

        if not self.db.member_exists(member):
            return
        banstate = self.db.get_attribute(member, "tempBanned")
        if banstate:
            print("Member{}({}) tempbanned, ignoring".format(member.name, member.id))
            return

        self.db.update_member(member, {"tempBanned": False})
        print("Member {} ({}) was banned manually".format(member.name, member.id))

    async def on_ready(self):
        """
        Called once a connection has been established
        """
        log.ready("Running discord.py version: " + discord.__version__)
        log.ready("Connected to Discord!")
        log.info("Logged in as {0.name}#{0.discriminator} ({0.id})".format(self.user))
        log.info("Prefix: " + self.config.prefix)
        log.info("SelfBot: " + ["true", "false"][self.config.useToken])

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
                "No dbconf configuration in config.yml," + "motd features are disabled"
            )
        await self.change_presence(game=discord.Game(name="with cats :3"))
        return

    async def execute_command(self, message):
        response = await self.commands.run(message)
        if response is not None:
            self.config.get("stats")["comCount"] += 1
            await self.send_message(message.author, message.channel, response)
            return True
        else:
            return False

    async def send_message(
        self, author=None, channel=None, message=None, timeout=0, **kwargs
    ):
        """
        Overload on the send_message function
        """
        if not message or not str(message):
            # Without a message to send, dont even try; it would just error
            return None
        if self.dev_mode:
            message = "[DEV]  " + str(message) + "  [DEV]"
        if author is not None:
            if self.db.get_member(author) is not None:
                if self.db.get_attribute(author, "ac", verbose=False) is not None:
                    if self.db.get_attribute(author, "ac"):
                        # message += " , " + self.commands.get_ac()
                        l = list(self.db.ac.find())
                        message += " , " + l[random.randint(0, len(l) - 1)]["ending"]
        try:
            return await super().send_message(channel, message)
        except discord.errors.InvalidArgument:
            log.err("A message: " + message + " was unable to be sent in " + channel)
            return None
        except discord.errors.Forbidden:
            log.err(
                "A message: "
                + message
                + " was unable to be sent in channel: "
                + channel.name
            )
            return None

    async def embed(self, channel, embedded):
        if self.dev_mode:
            embedded.add_field(name="DEV", value="DEV")
        return await super().send_message(channel, embed=embedded)

    async def on_member_join(self, member):
        """
        To be called When a new member joins the server
        """

        response = ""
        if self.config.get("welcomeMessage") != "null":
            try:
                await self.send_message(
                    channel=member, message=self.config.get("welcomeMessage")
                )
            except KeyError:
                response = " and was not PM'd :( "
            else:
                response = " and was PM'd :) "

        if Petal.logLock:
            return

        if self.db.add_member(member):
            user_embed = discord.Embed(
                title="User Joined",
                description="A new user joined: " + member.server.name,
                colour=0x00FF00,
            )
        else:
            if len(self.db.get_attribute(member, "aliases")) != 0:
                user_embed = discord.Embed(
                    title="User ReJoined",
                    description=self.db.get_attribute(member, "aliases")[-1]
                    + " rejoined "
                    + member.server.name
                    + " as "
                    + member.name,
                    colour=0x00FF00,
                )
            else:
                return

        self.db.update_member(
            member, {"aliases": [member.name], "servers": [member.server.id]}
        )

        user_embed.set_thumbnail(url=member.avatar_url)
        user_embed.add_field(name="Name", value=member.name)

        user_embed.add_field(name="ID", value=member.id)
        user_embed.add_field(name="Discriminator", value=member.discriminator)
        if member.game is None:
            game = "(nothing)"
        else:
            game = member.game.name
        user_embed.add_field(name="Currently Playing", value=game)
        user_embed.add_field(name="Joined: ", value=str(member.joined_at)[:-7])
        user_embed.add_field(
            name="Account Created: ", value=str(member.created_at)[:-7]
        )

        await self.embed(self.get_channel(self.config.logChannel), user_embed)
        if response != "":
            await self.send_message(
                None, self.get_channel(self.config.logChannel), response
            )

        age = datetime.utcnow() - member.created_at
        if age.days <= 6:
            # Account is less than a week old, mention its age
            timeago = [int(age.total_seconds() / 60), "minutes"]
            if timeago[0] >= 120:
                # 2 hours or more? Say it in hours
                timeago = [int(timeago[0] / 60), "hours"]
            elif timeago[0] == 1:
                # Only a single minute? Use the singular
                timeago[1] = "minute"

            await self.send_message(
                None,
                self.get_channel(self.config.logChannel),
                "This member's account was created only {} {} ago!".format(*timeago),
            )

        return

    async def on_member_remove(self, member):
        """To be called when a member leaves"""
        if Petal.logLock:
            return

        userEmbed = discord.Embed(
            title="User Leave",
            description="A user has left: " + member.server.name,
            colour=0xFF0000,
        )

        userEmbed.set_author(
            name=self.user.name, icon_url="https://puu.sh/tB7bp/f0bcba5fc5.png"
        )

        userEmbed.set_thumbnail(url=member.avatar_url)
        userEmbed.add_field(name="Name", value=member.name)
        userEmbed.add_field(name="ID", value=member.id)
        userEmbed.add_field(name="Discriminator", value=member.discriminator)
        userEmbed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7])

        await self.embed(self.get_channel(self.config.logChannel), userEmbed)
        return

    async def on_message_delete(self, message):
        try:
            if Petal.logLock:
                return
            if message.channel.id in self.config.get("ignoreChannels"):
                return

            if message.channel.is_private:
                return
            if message.channel.server.id == "126236346686636032":
                return

            userEmbed = discord.Embed(
                title="Message Delete",
                description=message.author.name
                + "#"
                + message.author.discriminator
                + "'s message was deleted",
                colour=0xFC00A2,
            )
            userEmbed.set_author(
                name=self.user.name, icon_url="https://puu.sh/tB7bp/f0bcba5fc5" + ".png"
            )
            userEmbed.add_field(name="Server", value=message.server.name)
            userEmbed.add_field(name="Channel", value=message.channel.name)
            userEmbed.add_field(
                name="Message content", value=message.content, inline=False
            )
            userEmbed.add_field(
                name="Message creation", value=str(message.timestamp)[:-7]
            )
            userEmbed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7])

            await self.embed(self.get_channel(self.config.modChannel), userEmbed)
            await asyncio.sleep(2)
        except discord.errors.HTTPException:
            pass
        else:
            return

    async def on_message_edit(self, before, after):
        if Petal.logLock:
            return
        if before.content == "":
            return
        if before.channel.is_private:
            return

        if before.server.id in self.config.get(
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
        executed = (
            before.id in self.potential_typoed_commands
            and await self.execute_command(after)
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
            .add_field(name="Server", value=before.server.name)
            .add_field(name="Channel", value=before.channel.name)
            .add_field(name="Previous message: ", value=before.content, inline=False)
            .add_field(name="Edited message: ", value=after.content)
            .add_field(name="Timestamp", value=str(edit_time)[:-7], inline=False)
        )

        try:
            await self.embed(self.get_channel(self.config.modChannel), userEmbed)
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
                title="({}) User Role ".format(role.server.name) + gained,
                description="{}#{} {} role".format(
                    after.name, after.discriminator, gained
                ),
                colour=0x0093C3,
            )
            userEmbed.set_author(
                name=self.user.name, icon_url="https://puu.sh/tBpXd/ffba5169b2.png"
            )
            userEmbed.add_field(name="Role", value=role.name)
            userEmbed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7])
            await self.embed(self.get_channel(self.config.modChannel), userEmbed)

        if before.name != after.name:
            userEmbed = discord.Embed(
                title="User Name Change",
                description=before.name + " changed their name to " + after.name,
                colour=0x34F3AD,
            )

            userEmbed.add_field(name="UUID", value=str(before.id))

            userEmbed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7])

            await self.embed(self.get_channel(self.config.modChannel), userEmbed)
        return

    async def on_voice_state_update(self, before, after):

        # FIXME: This needs to have a limiter. Use at own risk of spam.
        if self.config.tc is None:
            return
        else:
            return
        tc = self.config.tc
        trackedChan = self.get_channel(tc["monitoredChannel"])
        postChan = self.get_channel(tc["destinationChannel"])
        if trackedChan is None:
            log.err("Invalid tracking channel. Function disabled")
            self.config.tc = None
            return
        if postChan is None:
            log.err("Invalid posting channel. Function disabled")
            self.config.tc = None
            return
        if before.voice_channel != trackedChan and after.voice_channel == trackedChan:
            try:
                await self.send_message(None, after, tc["messageToUser"])
            except discord.errors.HTTPException:
                log.warn("Unable to PM {}".format(before.name))
            else:
                msg = await self.wait_for_message(
                    author=after, check=self.is_pm, timeout=200
                )
                if msg is None:
                    return
                else:
                    if msg.content.lower() in [
                        "yes",
                        "confirm",
                        "please",
                        "yeah",
                        "yep",
                        "mhm",
                    ]:
                        await self.send_message(
                            None,
                            postChan,
                            tc["messageFormat"].format(
                                user=after, channel=after.voice_channel
                            ),
                        )
                    else:
                        await self.send_message(
                            None,
                            channel,
                            "Alright, just to let"
                            + "you know. If you "
                            + "have a spotty "
                            + "connection, you may"
                            + " get PM'd more than "
                            + "once upon joining"
                            + " this channel",
                        )
                    return

    async def on_message(self, message):
        await self.wait_until_ready()
        content = message.content.strip()
        if not message.channel.is_private:
            self.db.update_member(
                message.author,
                {
                    "aliases": message.author.name,
                    "servers": message.server.id,
                    "last_message_channel": message.channel.id,
                    "last_active": message.timestamp,
                    "last_message": message.timestamp,
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

        if message.author == self.user:
            return
        if message.content == self.config.prefix:
            return

        if message.author.id in self.config.blacklist:
            return

        for word in message.content.split():
            if message.channel.id in self.config.get("ignoreChannels"):
                break
            if word in self.config.wordFilter:
                embed = discord.Embed(
                    title="Word Filter Hit",
                    description="At least one filtered " + "word was detected",
                    colour=0x9F00FF,
                )

                embed.add_field(
                    name="Author",
                    value=message.author.name + "#" + message.author.discriminator,
                )
                embed.add_field(name="Channel", value=message.channel.name)
                embed.add_field(name="Server", value=message.server.name)
                embed.add_field(name="Content", value=message.content)
                embed.add_field(name="Detected word", value=word, inline=False)
                embed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7])
                embed.set_thumbnail(url=message.author.avatar_url)
                await self.embed(self.get_channel(self.config.modChannel), embed)
                break

        if (
            message.channel.id == self.config.get("roleGrant")["chan"]
            and discord.utils.get(
                self.mainsvr.roles, id=self.config.get("roleGrant")["role"]
            )
            not in message.author.roles
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
                    await self.add_roles(
                        message.author,
                        discord.utils.get(
                            self.mainsvr.roles, id=self.config.get("roleGrant")["role"]
                        ),
                    )
                    log.member(
                        message.author.name
                        + " (id: "
                        + message.author.id
                        + ") was given access"
                    )
                    # Add logging later
                    return

            except Exception as e:
                await self.send_message(
                    None,
                    message.channel,
                    "Something went wrong with granting"
                    + " your role. Pm a member of staff "
                    + str(e),
                )

        if not self.config.pm and message.channel.is_private:
            if not message.author == self.user:
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
        await self.execute_command(message)
