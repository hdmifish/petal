"""
An all around bot for discord
loosely based on functionality provided by leaf for Patch Gaming
written by isometricramen
"""

import discord
import re
import asyncio
from datetime import datetime
from .grasslands import Peacock
from .config import Config
from .commands import Commands
from .members import Members
from .dbhandler import DBHandler

from random import randint
log = Peacock()


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
        self.members = Members(self)

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
            log.err("Authenication Failure. Your auth: \n"
                    + str(self.config.token)
                    + " is invalid " + str(e))
            exit(401)
        return

    def is_pm(self, message):
        if message.channel.is_private:
            return True
        else:
            return False

    def remove_prefix(self, input):
        return input[len(input.split()[0]):]

    def get_main_server(self):
        if len(self.servers) == 0:
            log.err("This client is not a member of any servers")
            exit(404)

    async def save_loop(self):
        if self.dev_mode:
            return
        interval = self.config.get("autosaveInterval")
        while True:
            self.members.save()
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
            await self.commands.checkUpdate()

            await asyncio.sleep(interval)

    async def ban_loop(self):
        if self.dev_mode:
            return
        interval = self.config.get("unbanInterval")
        while True:
            for mem in self.members.doc:
                if len(self.members.doc[mem]["tempBan"]) > 0:
                    for case in self.members.doc[mem]["tempBan"]:
                        if self.members.doc[mem]["tempBan"][case]["active"]:
                            if (datetime.utcnow() <
                                datetime.strptime(self.members.doc[mem]
                                                  ["tempBan"][case]
                                                  ["expires"].strip(),
                                                  "%Y-%m-%d %H:%M:%S.%f")):
                                self.members.doc[mem]["isBanned"] = False
                                self.members.doc[mem]["tempBan"][case]["active"] = False
                                svr = self.get_server(
                                      self.members.doc[mem]["tempBan"][case]
                                                      ["server"])
                                bans = svr.get_bans()
                                for banned in bans:
                                    if banned.id == mem:
                                        await self.unban(svr, banned)
                                        log.member(banned.name + " " +
                                                   banned.id + " was unbanned")
                                self.members.save()

            await asyncio.sleep(interval)

    async def on_ready(self):
        """
        Called once a connection has been established
        """
        log.ready("Running discord.py version: " + discord.__version__)
        log.ready("Connected to Discord!")
        log.info("Logged in as {0.name}.{0.discriminator} ({0.id})"
                 .format(self.user))
        log.info("Prefix: " + self.config.prefix)
        log.info("SelfBot: " + ['true', 'false'][self.config.useToken])

        self.loop.create_task(self.save_loop())
        log.ready("Autosave coroutine running...")
        # self.loop.create_task(self.banloop())
        log.ready("Auto-unban coroutine running...")
        if self.config.get("mysql") is not None:
            self.loop.create_task(self.ask_patch_loop())
            log.ready("MOTD system running...")
            pass
        else:
            log.warn("No mysql configuration in config.yaml,"
                     + "motd features are disabled")

        return

    async def send_message(self, channel, message, timeout=0, **kwargs):
        """
        Overload on the send_message function
        """
        if self.dev_mode:
            message = "[DEV]" + message + "[DEV]"
        return await super().send_message(channel, message)

    async def embed(self, channel,  embedded):
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
                await self.send_message(member, self.config.get("welcomeMessage"), )
            except KeyError:
                response = " and was not PM'd :( "
            else:
                response = " and was PM'd :) "

        if Petal.logLock:
            return

        self.db.update_member(member, {"aliases": [member.name],
                                       "servers": [member.server.id]})



        if self.members.addMember(discord.utils.get(member.server.members,
                                  id=member.id)):
            userEmbed = discord.Embed(title="User Joined",
                                      description="A new user joined: "
                                      + member.server.name, colour=0x00FF00)
        else:
            if len(self.members.getMember(member.id)["aliases"]) != 0:

                userEmbed = discord.Embed(title="User ReJoined",
                                          description=self.members.
                                          getMember(member.id)["aliases"][-1]
                                          + " rejoined " + member.server.name
                                          + " as " + member.name,
                                          colour=0x00FF00)
            else:
                pass


        userEmbed.set_thumbnail(url=member.avatar_url)
        userEmbed.add_field(name="Name", value=member.name)

        userEmbed.add_field(name="ID", value=member.id)
        userEmbed.add_field(name="Discriminator", value=member.discriminator)
        if member.game is None:
            game = "(nothing)"
        else:
            game = member.game.name
        userEmbed.add_field(name="Currently Playing", value=game)
        userEmbed.add_field(name="Joined: ", value=str(member.joined_at)[:-7])
        userEmbed.add_field(name="Account Created: ",
                            value=str(member.created_at)[:-7])

        await self.embed(self.get_channel(self.config.logChannel), userEmbed)
        if response != "":
            await self.send_message(self.get_channel(self.config.logChannel), response, )

        if (datetime.utcnow() - member.created_at).days <= 6:
            await self.send_message(self.get_channel(self.config.logChannel), + "This member's account "
                                    + "was created less than 7 days ago!", )

        return

    async def on_member_remove(self, member):
        """To be called when a member leaves"""
        if Petal.logLock:
            return


        userEmbed = discord.Embed(title="User Leave",
                                  description="A user has left: "
                                  + member.server.name, colour=0xff0000)

        userEmbed.set_author(name=self.user.name,
                             icon_url="https://puu.sh/tB7bp/f0bcba5fc5.png")

        userEmbed.set_thumbnail(url=member.avatar_url)
        userEmbed.add_field(name="Name", value=member.name)
        userEmbed.add_field(name="ID", value=member.id)
        userEmbed.add_field(name="Discriminator", value=member.discriminator)
        userEmbed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7]
                            )

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

            userEmbed = discord.Embed(title="Message Delete",
                                      description=message.author.name + "#" +
                                      message.author.discriminator +
                                      "'s message was deleted",
                                      colour=0xFC00a2)
            userEmbed.set_author(name=self.user.name,
                                 icon_url="https://puu.sh/tB7bp/f0bcba5fc5" +
                                 ".png")
            userEmbed.add_field(name="Server",
                                value=message.server.name)
            userEmbed.add_field(name="Channel",
                                value=message.channel.name)
            userEmbed.add_field(name="Message content",
                                value=message.content,
                                inline=False)
            userEmbed.add_field(name="Message creation",
                                value=str(message.timestamp)[:-7])
            userEmbed.add_field(name="Timestamp",
                                value=str(datetime.utcnow())[:-7])

            await self.embed(self.get_channel(self.config.modChannel),
                             userEmbed)
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

        if before.server.id in self.config.get("ignoreServers") or \
           before.channel.id in self.config.get("ignoreChannels"):
            return

        if after.content == "":
            return
        if before.content == after.content:
            return

        userEmbed = discord.Embed(title="Message Edit",
                                  description=before.author.name + "#" +
                                  before.author.discriminator +
                                  " edited their message", colour=0xae00fe)

        userEmbed.add_field(name="Server",
                            value=before.server.name)
        userEmbed.add_field(name="Channel",
                            value=before.channel.name)
        userEmbed.add_field(name="Previous message: ",
                            value=before.content,
                            inline=False)
        userEmbed.add_field(name="Edited message: ",
                            value=after.content)
        userEmbed.add_field(name="Timestamp",
                            value=str(datetime.utcnow())[:-7], inline=False)

        try:
            await self.embed(self.get_channel(
                             self.config.modChannel), userEmbed)
        except discord.errors.HTTPException:
            log.warn("HTTP 400 error from the edit statement. " +
                     "Usually it's safe to ignore it")

            return

    async def on_member_update(self, before, after):
        if Petal.logLock:
            return
        gained = None

        for r in before.roles:
            if r not in after.roles:
                gained = "Lost"
                role = r
        for r in after.roles:
            if r not in before.roles:
                gained = "Gained"
                role = r

        if gained is not None:
            userEmbed = discord.Embed(title="({}) User Role "
                                      .format(role.server.name) + gained,
                                      description="{}#{} {} role"
                                      .format(after.name, after.discriminator,
                                              gained), colour=0x0093c3)
            userEmbed.set_author(name=self.user.name,
                                 icon_url="https://puu.sh/tBpXd/ffba5169b2.png"
                                 )
            userEmbed.add_field(name="Role", value=role.name)
            userEmbed.add_field(name="Timestamp",
                                value=str(datetime.utcnow())[:-7])
            await self.embed(self.get_channel(self.config.modChannel),
                             userEmbed)

        if before.name != after.name:
            userEmbed = discord.Embed(title="User Name Change",
                                      description=before.name +
                                      " changed their name to " +
                                      after.name, colour=0x34f3ad)

            userEmbed.add_field(name="Timestamp",
                                value=str(datetime.utcnow())[:-7])

            await self.embed(self.get_channel(self.config.modChannel),
                             userEmbed)
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
        if (before.voice_channel != trackedChan
           and after.voice_channel == trackedChan):
            try:
                await self.send_message(after, tc["messageToUser"], )
            except discord.errors.HTTPException:
                log.warn("Unable to PM {}".format(before.name))
            else:
                msg = await self.wait_for_message(author=after,
                                                  check=self.is_pm,
                                                  timeout=200)
                if msg is None:
                    return
                else:
                    if msg.content.lower() in ["yes", "confirm", "please",
                                               "yeah", "yep", "mhm"]:
                        await self.send_message(postChan, tc["messageFormat"]
                                                .format(user=after,
                                                        channel=after.
                                                        voice_channel), )
                    else:
                        await self.send_message(after, "Alright, just to let" +
                                                "you know. If you " +
                                                "have a spotty " +
                                                "connection, you may" +
                                                " get PM'd more than " +
                                                "once upon joining" +
                                                " this channel", )
                    return

    async def on_message(self, message):
        await self.wait_until_ready()
        content = message.content.strip()
        if not message.channel.is_private:
            self.db.update_member(message.author,
                                  {"aliases": message.author.name,
                                   "servers": message.server.id,
                                   "last_message_channel": message.channel.id,
                                   "last_active": message.timestamp,
                                   "last_message": message.timestamp}, type=1)
            self.members.addMember(discord.utils.get(message.server.members,
                                                     id=message.author.id))
            self.members.getMember(message.author.id)["messageCount"] += 1

        if message.author == self.user:
            return
        if message.content == self.config.prefix:
            return

        if message.author.id in self.config.blacklist:
            return

        for word in message.content.split():
            if word in self.config.wordFilter:
                embed = discord.Embed(title="Word Filter Hit",
                                      description="At least one filtered " +
                                                  "word was detected",
                                      colour=0x9f00ff)

                embed.add_field(name="Author",
                                value=message.author.name + "#" +
                                     message.author.discriminator)
                embed.add_field(name="Channel", value=message.channel.name)
                embed.add_field(name="Server", value=message.server.name)
                embed.add_field(name="Content", value=message.content)
                embed.add_field(name="Detected word", value=word, inline=False)
                embed.add_field(name="Timestamp",
                                value=str(datetime.utcnow())[:-7])
                embed.set_thumbnail(url=message.author.avatar_url)
                await self.embed(self.get_channel(self.config.modChannel),
                                 embed)
                break

        if (message.channel.id == self.config.get("roleGrant")["chan"]
           and discord.utils.get(self.mainsvr.roles,
                                 id=self.config.get("roleGrant")["role"])
           not in message.author.roles):
            try:
                if self.config.get("roleGrant")["ignorecase"]:
                    check = re.compile(self.config.get("roleGrant")["regex"],
                                       re.IGNORECASE)
                else:
                    check = re.compile(self.config.get("roleGrant")["regex"])

                if check.match(message.content):
                    await self.send_message(message.channel, self.config.get("roleGrant")
                    ["response"], )
                    await self.add_roles(message.author,
                                         discord.utils.get(self.mainsvr.roles,
                                                           id=self.config
                                                           .get("roleGrant")
                                                           ["role"]))
                    log.member(message.author.name + " (id: " +
                               message.author.id + ") was given access")
                    # Add logging later
                    return

            except Exception as e:
                await self.send_message(message.channel, "Something went wrong will granting" +
                                        " your role. Pm a member of staff " +
                                        str(e), )

        if not self.config.pm and message.channel.is_private:
            if not message.author == self.user:
                await self.send_message(message.channel, "Petal has been configured by staff" +
                                        " to not respond to PMs right now", )
            return

        if not content.startswith(self.config.prefix):
            return
        com = content[len(self.config.prefix):].lower().strip()

        if com.split()[0] in dir(self.commands):
            methodToCall = getattr(self.commands, com.split()[0])
            if methodToCall.__doc__ is None:
                log.warn("All commands require a docstring to not be " +
                         "ignored. If you dont know what caused this, " +
                         "it's safe to ignore the warning.")
                return
            log.com("[{0}] [{1}] [{1.id}] [{2}] ".format(message.channel,
                                                         message.author,
                                                         com))
            if not message.channel.is_private:
                self.db.update_member(message.author,
                                      {"aliases": message.author.name,
                                       "servers": message.author.server.id,
                                       "last_message_channel": message.channel.id,
                                       "last_active": message.timestamp,
                                       "last_message": message.timestamp}, type=2)
            response = await methodToCall(message)
            if response:
                self.config.get("stats")["comCount"] += 1
                await self.send_message(message.channel, response, )
                return

        else:
            if com.split()[0] in self.config.aliases:
                aliased = self.config.aliases[com.split()[0]]
                methodToCall = getattr(self.commands, aliased)
                log.com("[{0}] [{1}] [{1.id}] [{2}] ".format(message.channel,
                                                             message.author,
                                                             com))
                response = await methodToCall(message)
                if response:
                    self.config.get("stats")["comCount"] += 1
                    await self.send_message(message.channel, response, )
                    return

            if com.split()[0] in self.config.commands:
                response = await self.commands.parseCustom(com, message)
                await self.send_message(message.channel, response, )

            # else:
            #    return
            #
            #    log.com("[{0}] [{1}] [{1.id}] [Cleverbot][{2}]"
            #            .format(message.channel, message.author,
            #                    message.content.lstrip(self.config.prefix)))
            #    response = await self.commands.cleverbot(message)
            #    await self.send_message(message.channel, response, )
            return
