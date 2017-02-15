"""
An all around bot for discord
loosely based on functionality provided by leaf for Patch Gaming
written by hdmifish
"""

import discord
import re
import asyncio
from datetime import datetime 
from .grasslands import Peacock
from .config import Config
from .commands import Commands  
from .members import Members
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
		self.members = Members(self)
		

		log.info("Configuration object initalized")
		return

	def run(self):
		try:
			super().run(self.config.token, bot=not self.config.get("selfBot"))
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

	async def saveloop(self):
		while True:
			self.members.save(vb=True)
			self.config.save(vb=True)
			await asyncio.sleep(3000)

		
	async def on_ready(self):
		"""
		Called once a connection has been established
		"""
		log.ready("Running discord.py version: " + discord.__version__)
		log.ready("Connected to Discord!")
		log.info("Logged in as {0.name}.{0.discriminator} ({0.id})".format(self.user))
		log.info("Prefix: " + self.config.prefix)
		log.info("SelfBot: " + ['true', 'false'][self.config.useToken])
		await self.saveloop()
		#log.info("Server Info: ")
		#self.mainsvr = self.getMainServer()
		#log.info("-  Name: " + self.mainsvr.name)
		#log.info("-    ID: " + self.mainsvr.id)
		#log.info("- Owner: " + self.mainsvr.owner.name)
		#log.info("- Users: " + str(self.mainsvr.member_count))
		#log.warn("Displaying Roles and ID's for your enjoyment")
		#for s in self.mainsvr.roles:
		#	log.info("----" + s.name  + " - " + s.id)
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
		
		if self.config.lockLog:
			return	
		
		
		if self.members.addMember(member):	
			userEmbed = discord.Embed(title="User Joined", description="A new user joined: " + member.server.name, colour=0x00FF00)
		else:
			userEmbed = discord.Embed(title="User ReJoined", description= self.members.getMember(member.id)["aliases"][-1] + " rejoined " + member.server.name + " as " + member.name, colour=0x00FF00)
	
		userEmbed.set_author(name=self.user.name, icon_url="https://puu.sh/tAEjd/89f4b0a5a7.png")
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
		
		await self.embed(self.get_channel(self.config.logChannel), userEmbed)
		return

	async def on_member_remove(self, member):
		"""
		To be called when a member leaves
		"""
		if self.config.lockLog:
			return
		userEmbed = discord.Embed(title="User Leave" , description="A user has left: " + member.server.name, colour=0xff0000)
		userEmbed.set_author(name=self.user.name, icon_url="https://puu.sh/tB7bp/f0bcba5fc5.png")
		userEmbed.set_thumbnail(url=member.avatar_url)
		userEmbed.add_field(name="Name", value=member.name)
		userEmbed.add_field(name="ID", value=member.id)
		userEmbed.add_field(name="Discriminator", value=member.discriminator)
		userEmbed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7] )

		await self.embed(self.get_channel(self.config.logChannel), userEmbed)
		return

	
	async def on_message_delete(self, message):
		if  self.config.lockLog:	
			return
		

		userEmbed = discord.Embed(title="Message Delete" , description=message.author.name + "#" + message.author.discriminator + "'s message was deleted", colour=0xFC00a2)
		userEmbed.set_author(name=self.user.name, icon_url="https://puu.sh/tB7bp/f0bcba5fc5.png")
		userEmbed.add_field(name="Server", value= message.server.name)
		userEmbed.add_field(name="Channel", value = message.channel.name)
		userEmbed.add_field(name="Message content", value=message.content, inline=False)
		userEmbed.add_field(name="Message creation", value=str(message.timestamp)[:-7])
		userEmbed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7]) 
		
	
		await self.embed(self.get_channel(self.config.modChannel), userEmbed)
		await asyncio.sleep(2)

		return 

	async def on_message_edit(self, before, after):
		if self.config.lockLog:
			return 	
		if before.content == "":
			return 
		if before.content == after.content:
			return 

		userEmbed = discord.Embed(title="Message Edit" , description=before.author.name + "#" + before.author.discriminator + " edited their message", colour=0xae00fe)
		userEmbed.set_author(name=self.user.name, icon_url="https://puu.sh/tB7bp/f0bcba5fc5.png")
		userEmbed.add_field(name="Server", value= before.server.name)
		userEmbed.add_field(name="Channel", value = before.channel.name)
		userEmbed.add_field(name="Previous message: ", value=before.content, inline=False)	
		userEmbed.add_field(name="Edited message: ", value=after.content)
		userEmbed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7], inline=False)

		try:
			await self.embed(self.get_channel(self.config.modChannel), userEmbed)	
		except discord.errors.HTTPException:
			print("HTTP 400 error from the edit statement. Usually it's safe to ignore it")
			pass #this is awful but it silences a silly error that I can not find a solution to
#		self.config.flip()
		return 
	
	
	async def on_member_update(self, before, after):
		if self.config.lockLog:
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
			userEmbed = discord.Embed(title="({}) User Role ".format(role.server.name) + gained , description="{}#{} {} role".format(after.name, after.discriminator, gained), colour=0x0093c3)
			userEmbed.set_author(name=self.user.name, icon_url="https://puu.sh/tBpXd/ffba5169b2.png")
			userEmbed.add_field(name="Role", value=role.name) 
			userEmbed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7]) 
			await self.embed(self.get_channel(self.config.modChannel), userEmbed)

		if before.name != after.name:
			userEmbed = discord.Embed(title="User Name Change", description=before.name + " changed their name to " + after.name, colour=0x34f3ad)
			userEmbed.set_author(name=self.user.name, icon_url="https://puu.sh/tBpXd/ffba5169b2.png")
			userEmbed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7]) 
	
			await self.embed(self.get_channel(self.config.modChannel), userEmbed)
		return 
	
	async def on_voice_state_update(self, before, after):
		if self.config.tc is None:
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
				await self.send_message(after, tc["messageToUser"])
			except discord.errors.HTTPException: 
				log.warn("Unable to PM {user.name}".format(before))
			else:
				msg = self.wait_for_message(author=after, channel=after, timeout=20)
				if msg is None:
					return 
				else:
					if ["yes", "confirm", "please", "yeah", "yep", "mhm" ] in msg.content.lower(): 
						await self.send_message(postChan, tc["messageFormat"].format(user=after, channel=after.voice_channel))
					else:
						await self.send_message(after, "Alright, just to let you know. If you have a spotty connection, you may get PM'd more than once upon joining this channel") 
					return 

				
		
	async def on_message(self, message):
		await self.wait_until_ready()
		content = message.content.strip()
		self.members.addMember(message.author)
		self.members.getMember(message.author.id)["messageCount"] += 1
		
		if message.author == self.user:
			return
		if message.content == self.config.prefix:
			return
		
    
    

		
		for word in message.content.split():
			if word in self.config.wordFilter:
				embed = discord.Embed(title="Word Filter Hit", description="At least one filtered word was detected", colour=0x9f00ff)
				embed.set_author(name=self.user.name, icon_url=	"https://puu.sh/tFFD2/ff202bfc00.png")
				embed.add_field(name="Author", value=message.author.name + "#" + message.author.discriminator)
				embed.add_field(name="Channel", value=message.channel.name)
				embed.add_field(name="Server", value=message.server.name)
				embed.add_field(name="Content", value=message.content)
				embed.add_field(name="Detected word", value=word, inline=False)		
				embed.add_field(name="Timestamp", value=str(datetime.utcnow())[:-7])
				embed.set_thumbnail(url=message.author.avatar_url)
				await self.embed(self.get_channel(self.config.modChannel), embed) 
				break

				
		if message.channel.id == self.config.get("roleGrant")["chan"] and discord.utils.get(self.mainsvr.roles, id=self.config.get("roleGrant")["role"]) not in message.author.roles:
			try:
				if self.config.get("roleGrant")["ignorecase"]:
					check = re.compile(self.config.get("roleGrant")["regex"], re.IGNORECASE)
				else:
					check = re.compile(self.config.get("roleGrant")["regex"])


				if check.match(message.content):
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
				log.com("[{0}] [{1}] [{1.id}] [Cleverbot][{2}]".format(message.channel, message.author, message.content.lstrip(self.config.prefix) ))
				response = await self.commands.cleverbot(message)
				await self.send_message(message.channel, response)
			return
