"""
An all around bot for discord
loosely based on functionality provided by leaf for Patch Gaming
written by hdmifish
"""

import discord
import re
from .grasslands import Peacock
from .config import Config
from .commands import Commands
log = Peacock()


class Petal(discord.Client):
	def __init__(self):

		try:
			super().__init__()
		except Exception as e:
			log.err("Could not initialize client object: " + str(e), "r")
		else:
			log.info("Client object initialized")

		self.config = Config()
		self.commands = Commands(self)
		log.info("Configuration object initalized")
		return

	def run(self):
		try:
			super().run(self.config.token, bot=self.config.useToken)
		except AttributeError as e:
			log.err("Could not connect using the token provided: " + str(e))
			exit(1)

		except discord.errors.LoginFailure as e:
			log.err("Authenication Failure. Your auth: \n"
					+ str(self.config.token)
					+ " is invalid " + str(e))
			exit(401)
		return

	def removePrefix(self, input):
		return input[len(input.split()[0]):]

	def getMainServer(self):
		if len(self.servers) == 0:
			log.err("This client is not a member of any servers")
			exit(404)
		if len(self.servers) > 1:
			log.err("Petal only works as a member of one server per instance")
			exit(500)
		for server in self.servers:
			return server

	async def on_ready(self):
		"""
		Called once a connection has been established
		"""
		print(discord.__version__)
		log.ready("Connected to Discord!")
		log.info("Logged in as {0.name}.{0.discriminator} ({0.id})".format(self.user))
		log.info("Prefix: " + self.config.prefix)
		log.info("SelfBot: " + ['true', 'false'][self.config.useToken])
		log.info("Server Info: ")
		self.mainsvr = self.getMainServer()
		log.info("-  Name: " + self.mainsvr.name)
		log.info("-    ID: " + self.mainsvr.id)
		log.info("- Owner: " + self.mainsvr.owner.name)
		log.info("- Users: " + str(self.mainsvr.member_count))
		log.warn("Displaying Roles and ID's for your enjoyment")
		for s in self.mainsvr.roles:
			log.info("----" + s.name  + " - " + s.id)
		return

	async def send_message(self, channel, message, timeout=0):
		"""
		Overload on the send_message function"
		"""
		# TODO: Make this do things
		return await super().send_message(channel, message)

	async def embed(self,channel,  embedded):
		return await super().send_message(channel, embed=embedded)

	async def on_member_join(self, member):
		"""
		To be called When a new member joins the server
		"""
		if self.config.get("welcomeMessage") != "null":
			try:
				await self.send_message(member, self.config.get("welcomeMessage"))
			except KeyError:
				response = " and was not PM'd :( "
			else:
				response = " and was PM'd :) "
			finally:
				svr = self.mainsvr
				await self.send_message(discord.utils.get(svr.channels, id=str(self.config.get("logChannel"))), ":new: {0} (ID: {0.id}) joined the server ".format(member) + response)
				return

	async def on_member_remove(self, member):
		"""
		To be called when a member leaves
		"""
		if not self.config.useLog:
			return
		svr = self.mainsvr
		await self.send_message(discord.utils.get(svr.channels, id=str(self.config.get("logChannel"))), ":put_litter_in_its_place: {0} (ID: {0.id}) left the server ".format(member) )
		return


	async def on_message(self, message):
		await self.wait_until_ready()
		content = message.content.strip()
		if message.author == self.user:
			return
		if message.content == self.config.prefix:
			return


		if message.channel.id == self.config.get("roleGrant")["chan"] and discord.utils.get(self.mainsvr.roles, id=self.config.get("roleGrant")["role"]) not in message.author.roles:
			try:
				if re.match(self.config.get("roleGrant")["regex"], message.content):
					await self.send_message(message.channel, self.config.get("roleGrant")["response"])
					await self.add_roles(message.author, discord.utils.get(self.mainsvr.roles, id=self.config.get("roleGrant")["role"]))
					log.member(message.author.name + " (id: " + message.author.id + ") was given access")
					#Add logging later
					return

			except Exception as e:
				await self.send_message(message.channel, "Something went wrong will granting your role. Pm a member of staff " + str(e))


		if not self.config.pm and message.channel.is_private:
			if not message.author == self.user:
				await self.send_message(message.channel,
										"Petal has been configured by staff" +
										" to not respond to PMs right now")
			return
		if not content.startswith(self.config.prefix):
			return
		com = content[len(self.config.prefix):].lower().strip()

		if com.split()[0] in dir(self.commands):
			methodToCall = getattr(self.commands, com.split()[0])
			if methodToCall.__doc__ is None:
				log.warn("All commands require a docstring to not be ignored. If you dont know what caused this, it's safe to ignore the warning.\nHowever, ")
				return
			log.com("[{0}] [{1}] [{1.id}] [{2}] ".format(message.channel, message.author, com))
			response = await methodToCall(message)
			if response:
				await self.send_message(message.channel, response)
				return

		else:
			if com.split()[0] in self.config.aliases:
				aliased = self.config.aliases[com.split()[0]]
				methodToCall = getattr(self.commands, aliased)
				log.com("[{0}] [{1}] [{1.id}] [{2}] ".format(message.channel, message.author, com))
				response = await methodToCall(message)
				if response:
					await self.send_message(message.channel, response)
					return

			if com.split()[0] in self.config.commands:
				response = await self.commands.parseCustom(com, message)
				await self.send_message(message.channel, response)

			else:
				response = await self.commands.load(message)
				if response:
					log.com("[{0}] [{1}] [{1.id}] [Cleverbot][{2}]".format(message.channel, message.author, message.content.lstrip(self.config.prefix) ))
					response = await self.commands.cleverbot(message)
					await self.send_message(message.channel, response)
			return
