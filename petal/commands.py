import asyncio
import discord
import random

import imghdr
import urllib.request as urllib2
import magic
import re
import os
import praw

from cleverbot import Cleverbot
from datetime import datetime
from .grasslands import Octopus
from .grasslands import Giraffe
from .grasslands import Peacock
class Commands:

	"""
	Pretty cool thing with which to store commands
	"""
	def __init__(self, client):
		self.client = client
		self.config = client.config
		self.cb = Cleverbot()
		self.log = Peacock()
		self.osuKey = self.config.get("osu")
		if self.osuKey is not None:
			self.o = Octopus(self.osuKey)
		self.imgurKey = self.config.get("imgur")
		if self.imgurKey is not None:
			self.i = Giraffe(self.imgurKey)
		if self.config.get("reddit") is not None:
			reddit = self.config.get("reddit")
			self.r = praw.Reddit(client_id=reddit["clientID"],
								client_secret=reddit["clientSecret"],
								user_agent=reddit["userAgent"],
								username=reddit["username"],
								password=reddit["password"]
								)
			if self.r.read_only:
				self.log.warn("This account is in read only mode. You may have done something wrong. This will disable reddit functionality.")
				return


	def level0(self, author):
		#this supercedes all other levels so, use it carefully

		return author.id == str(self.config.owner)

	def level1(self, author):

		return author.id in self.config.l1 or self.level0(author)

	def level2(self, author):

		return author.id in self.config.l2 or self.level1(author)

	def level3(self, author):

		return author.id in self.config.l3 or self.level2(author)

	def level4(self, author):

		return author.id in self.config.l4 or self.level3(author)

	def getlevel(self, author):
		count = 0
		if self.level0(author):
			return 0
		for l in self.config.get("level"):
			count += 1
			if author.id in self.config.get("level")[l]:
				return count
		return 5


	def check(self, message):

		return message.content.lower() == 'yes'

	def cleanInput(self, input):

		args = input[len(input.split()[0]):].split('|')
		newargs = []
		for i in args:
			newargs.append(i.strip())

		return newargs

	def removePrefix(self, input):

		return input[len(input.split()[0]):]

	def getMember(self, message, member):
		return discord.utils.get(message.server.members, id=member.lstrip("<@!").rstrip('>'))

	def saveImage(self, command):
		if not re.match('^[a-zA-Z0-9_]+$', command[0]):
			 return "File name must be letters and numbers only"
		try:
			response = urllib2.urlopen(command[1].strip())
			with open('{}/img/temp'.format(os.getcwd()), 'wb') as outfile:
				outfile.write(response.read())
			mimetype = magic.from_file("./img/temp", mime=True)

			if mimetype.lower() not in ['image/png', 'image/jpg', 'image/jpeg', 'image/gif', 'video/mp4', 'video/webm']:
				return "Invalid File Type: " + mimetype ("note: gifv is not supported by petal right now")
			extension = mimetype.lower()[6:]
			filename = "{}/img/{}.{}".format(os.getcwd(), command[0].strip(), extension.strip())
			tempfile = os.getcwd() + "/img/temp"
			print(filename )
			print(tempfile)
			os.rename(tempfile, filename)
			self.config.imageIndex[command[0]] = filename
		except Exception as e:
			return "Something went wrong :( " + str(type(e).__name__) + str(e.args)
		else:
			self.config.save()
			return "Image: " + command[0] + "saved successfully!"

	async def parseCustom(self, command, message):
		invoker = command.split()[0]
		if len(command.split()) > 1:
			tags = self.getMember(message, command.split()[1].strip()).mention
		else:
			tags = "<poof>"
		com = self.config.commands[invoker]
		response = com["com"]
		perms = com["perm"]

		try:
			output = response.format(self=message.author.name, myID=message.author.id, tag=tags)
		except KeyError:
			return "Error translating custom command"
		else:
			return output


	# ------------------------------------------
	# START COMMAND LIST (ILL ORGANIZE IT later)
	# ------------------------------------------

	async def hello(self, message):
		"""
		This is a test, its a test
		"""
		if self.level0(message.author):
			return "Hello boss! How's it going?"
		else:
			return "Hey there!"

	async def choose(self, message):
		"""
		Chooses a random option from a list, separated by |
		Syntax: `>choose foo | bar`
		"""
		args = self.cleanInput(message.content)
		response = "From what you gave me, I believe `{}` is the best choice".format(args[random.randint(0, len(args) - 1)])
		return response


	async def cleverbot(self, message):
		"""
		Sends your message to cleverbot
		Syntax: `>(your message)`
		"""
		return self.cb.ask(self.removePrefix(message.content))




	# osu (grasslands.octopus)
	async def osu(self, message):
		"""
		Gets information for an osu player
		Syntax: `>osu (optional: username)`
		"""
		try:
			self.o
		except AttributeError:
			return "Osu Support is disabled by administrator"
		uid = self.removePrefix(message.content)
		if uid.strip() == "":
			user = self.o.get_user(message.author.name)
			if user is None:
				return "Looks like there is no osu data associated with your discord name"
		else:
			user = self.o.get_user(uid.split('|')[0])
			if user is None:
				return "No user found with Osu! name: " + uid.split('|')[0]

		em = discord.Embed(title=user.name, description= "https://osu.ppy.sh/u/{}".format(user.id) ,colour=0x0acdff )
		em.set_author(name="Osu Data", icon_url=self.client.user.avatar_url)
		em.set_thumbnail(url="http://a.ppy.sh/" + user.id)
		em.add_field(name="Maps Played", value="{:,}".format(int(user.playcount)))
		em.add_field(name="Total Score", value="{:,}".format(int(user.total_score)))
		em.add_field(name="Level", value=round(float(user.level),2), inline=False)
		em.add_field(name="Accuracy", value=round(float(user.accuracy), 2))
		em.add_field(name="PP Rank", value="{:,}".format(int(user.rank)), inline=False)
		em.add_field(name="Local Rank ({})".format(user.country), value="{:,}".format(int(user.country_rank)))
		await self.client.embed(message.channel, embedded=em)
		return None

	async def new(self, message):
		if not self.level4(message.author):
			return
		if len(self.removePrefix(message.content).split('|')) < 2:
			return "This command needs at least 2 arguments"

		invoker = self.removePrefix(message.content).split('|')[0].strip()
		command = self.removePrefix(message.content).split('|')[1].strip()

		if len(self.removePrefix(message.content).split('|')) > 3:
			perms = self.removePrefix(message.content).split('|')[2].strip()
		else:
			perms = '0'

		if invoker in self.config.commands:
			await self.client.send_message(message.channel, "This command already exists, type 'yes' to rewrite it")
			response = await self.client.wait_for_message(timeout=15, author=message.author, channel=message.channel)
			if response is None or not self.check(response):
				return "Command: `" + invoker + "` was not changed."
			else:
				self.config.commands[invoker] = {"com":command, "perm":perms}
				self.config.save()
				return "Command: `" + invoker + "` was redefined"
		else:
			self.config.commands[invoker] = {"com":command, "perm": perms}
			self.config.save()
			return "New Command `{}` Created!".format(invoker)

	async def save(self, message):
		"""
		Saves an image to database.
		Syntax: `>save (foo)`
		Filetypes: gif, png, jpg, tiff, mp4 (< 8MB)
		"""
		command = self.cleanInput(message.content)
		if command[0] in self.config.imageIndex:
			await self.client.send_message(message.channel, "This image already exists, type 'yes' to overwrite")
			response = await self.client.wait_for_message(timeout=15, author= message.author, channel= message.channel)
			if response is None or not self.check(response):
				return "Image `{}` was not changed".format(self.config.imageIndex[command[0]].split('/')[-1])

		return self.saveImage(command)

	async def load(self, message):
		"""
		Loads an image from database.
		Syntax: `>load (foo)`
		Can also load via `foo` if foo is not a function or custom command
		"""
		imageToLoad = self.cleanInput(message.content)[0].strip()
		if imageToLoad not in self.config.imageIndex:
			return "Image does not exist"
		else:
			try:
				await self.client.send_file(message.channel, self.config.imageIndex[imageToLoad])
			except Exception as e:
				return "Exception occured: " + type(e).__name__ + str(e.args)
			else:
				return None

	async def help(self, message):
		"""
		Congrats, You did it!
		"""
		func = self.cleanInput(message.content)[0]
		if func == "":
			em = discord.Embed(title="Help tester!", description="A rich embed test!", colour=0x0acdff)
			em.set_author(name="Petal Help Provider", icon_url=self.client.user.avatar_url)
			em.set_thumbnail(url=message.author.avatar_url)
			em.add_field(name="Title", value="Magic Help Text Line 1")
			em.add_field(name="Syntax", value="`>help`")


			await self.client.embed(message.channel, em)
			return
		if func in dir(self):
			if getattr(self, func).__doc__ is None:
				return "No help info for function: " + func
			else:
				helptext = getattr(self, func).__doc__.split("\n")
				em = discord.Embed(title=func, description=helptext[1], colour=0x0acdff)
				em.set_author(name="Petal Help", icon_url=self.client.user.avatar_url)
				em.set_thumbnail(url=self.client.user.avatar_url)
				em.add_field(name="Syntax", value=helptext[2])
				await self.client.embed(message.channel, em)
		else:
			if self.config.aliases[func] in dir(self):
				if getattr(self, self.config.aliases[func]).__doc__ is None:
					return "No help for function: " + func
				else:
					helptext = getattr(self, self.config.aliases[func]).__doc__.split("\n")
					em = discord.Embed(title=func, description=helptext[1], colour=0x0acdff)
					em.set_author(name="Petal Help", icon_url=self.client.user.avatar_url)
					em.set_thumbnail(url=self.client.user.avatar_url)
					em.add_field(name="Syntax", value=helptext[2])
					await self.client.embed(message.channel, em)
					return "__**Help Information For {}**__:\n{}".format(func, getattr(self, self.config.aliases[func]).__doc__)
			else:
				return "Function does not exists"

	async def freehug(self, message):
		"""
		Requests a freehug from a hug donor
		`freehug add | foo` - adds user to donor list
		'freehug del | foo' - removes user from donor list
		'freehug donate' - toggles your donor status, your request counter will reset if you un-donate
		'freehug status' - If you're a donor, see how many requests you have recieved
		'freehug' - requests a hug
		"""
		args = self.cleanInput(message.content)

		if args[0] == '':
			valid = []
			for m in self.config.hugDonors:
				user = self.getMember(message, m)
				if user is not None:
					if user.status == discord.Status.online and user != message.author:
						valid.append(user)

			if len(valid) == 0:
				return "Sorry, no valid hug donors are online right now"

			pick = valid[random.randint(0, len(valid) - 1)]

			try:
				await self.client.send_message(pick, "Hello there. This message is to inform you that " + message.author.name + " has requested a hug from you")
			except discord.ClientException:
				return "Your hug donor was going to be: " + pick.mention + " but unfortunately they were unable to be contacted"
			else:
				self.config.hugDonors[pick.id]["donations"] += 1
				self.config.save()
				return "A hug has been requested of: " + pick.name




		if args[0].lower() == 'add':
			if len(args) < 2:
				return "To add a user, please tag them after add | "
			user = self.getMember(message, args[1].lower())
			if user is None:
				return "No valid user found for " + args[1]
			if user.id in self.config.hugDonors:
				return "That user is already a hug donor"

			self.config.hugDonors[user.id]  = {"name":user.name, "donations":0}
			self.config.save()
			return "{} added to the donor list".format(user.name)

		elif args[0].lower() == 'del':
			if len(args) < 2:
				return "To remove a user, please tag them after del | "
			user = self.getMember(message, args[1].lower())
			if user is None:
				return "No valid user for " + args[1]
			if user.id not in self.config.hugDonors:
				return "That user is not a hug se donor"

			del self.config.hugDonors[user.id]
			return "{} was removed from the donor list".format(user.name)

		elif args[0].lower() == 'status':
			if message.author.id not in self.config.hugDonors:
				return "You are not a hug donor, user `freehug donate` to add yourself"
			return "You have received {} requests since you became a donor".format(self.config.hugDonors[message.author.id]["donations"])

		elif args[0].lower() == 'donate':
			if message.author.id not in self.config.hugDonors:
				self.config.hugDonors[message.author.id] = {"name":message.author.name, "donations":0}
				self.config.save()
				return "Thanks! You have been added to the donor list <3"
			else:
				del self.config.hugDonors[message.author.id]
				self.config.save()
				return "You have been removed from the donor list."

	async def promote(self, message):
		"""
		Promotes a member up one level. You must be at least one level higher to give them a promotion
		Syntax: `>promote (user tag)`
		"""
		if not self.level4(message.author):
			return "Dude, you don't have any perms at all. You can't promote people."
		args = self.cleanInput(message.content)
		if args[0] == '':
			return "Tag someone first ya goof"
		mem = self.getMember(message, args[0])
		if mem is None:
			return "Couldn't find a member with that tag/id"

		if self.getlevel(message.author) < self.getlevel(mem):
			mlv = self.getlevel(mem)
			if mlv < 2:
				return "You cannot promote this person any further. There can only be one level 0 (owner)"
			for l in self.config.get("level"):
				if mem.id in self.config.get("level")[l]:
					self.config.get("level")[l].remove(mem.id)

			self.config.get("level")["l"+ str(mlv - 1)].append(mem.id)

			self.config.save()
			return mem.name + " was promoted to level: " + str(mlv -1)
		else:
			return "You cannot promote this person"

	async def demote(self, message):
		"""
		Demotes a member down one level. You must be at least one level higher to demote someone
		Syntax: `>demote (user tag)`
		"""
		if not self.level4(message.author):
			return "Dude, you don't have any perms at all. You can't demote people"
		args = self.cleanInput(message.content)
		if args[0] == '':
			return "Tag someone first ya goof"
		mem = self.getMember(message, args[0])
		if mem is None:
			return "Couldn't find a member with that tag/id"

		if self.getlevel(message.author) < self.getlevel(mem):
			mlv = self.getlevel(mem)
			if mlv == 4:
				for l in self.config.get("level"):
					if mem.id in self.config.get("level")[l]:
						self.config.get("level")[l].remove(mem.id)
				return "All perms removed"
			if mlv == 5:
				return "Person has no perms, and therefor cannot be demoted"
			for l in self.config.get("level"):
				if mem.id in self.config.get("level")[l]:
					self.config.get("level")[l].remove(mem.id)

			self.config.get("level")["l"+ str(mlv + 1)].append(mem.id)
			self.config.save()
			return mem.name + " was promoted to level: " + str(mlv + 1)
		else:
			return "You cannot promote this person"

	async def sub(self, message, force=None):
		"""
		Returns a random image from a given subreddit.
		Syntax: '>sub (subreddit)'
		"""
		args = self.cleanInput(message.content)
		if args[0] == '':
			sr = "cat"
		else:
			sr = args[0]
		if force is not None:
			sr = force
		try:
			self.i
		except AttributeError:
			return "Imgur Support is disabled by administrator"

		try:
			ob =  self.i.get_subreddit(sr)
			if ob is None:
				return "Sorry, I couldn't find any images in subreddit: `" + sr + "`"
			if ob.nsfw and not self.config.permitNSFW:
				return "Found a NSFW image, currently NSFW images are disallowed by administrator"

		except ConnectionError as e:
			return "A Connection Error Occurred, this usually means imgur is over capacity. I cant fix this part :("
		except Exception as e:
			self.log.err("An unknown error occurred " + type(e).__name__ + " " + str(e))
			return "Unknown Error " + type(e).__name__
		else:
			return ob.link
	#=========REDEFINITIONS============#
	async def cat(self, message):
		"""
		what...
		"""
		return await self.sub(message, "cat")
	async def dog(self, message):
		"""
		what...
		"""
		return await self.sub(message, "dog")
	async def doggo(self, message):
		"""
		what...
		"""
		return await self.sub(message, "dog")
	async def pupper(self, message):
		"""
		what...
		"""
		return await self.sub(message, "dog")
	async def penguin(self, message):
		"""
		what...
		"""
		return await self.sub(message, "penguin")
	async def ferret(self, message):
		"""
		what...
		"""
		return await self.sub(message, "ferret")
	async def panda(self, message):
		"""
		what...
		"""
		return await self.sub(message, "panda")

	async def ping(self, message):
		"""
		Shows the round trip time from this bot to you and back
		Syntax: `>ping`
		"""
		msg = await self.client.send_message(message.channel, "*hugs*")
		delta = int((datetime.now() - msg.timestamp).microseconds / 1000)
		self.config.stats['pingScore'] += delta
		self.config.stats['pingCount'] += 1

		self.config.save(vb=0)
		truedelta = int(self.config.stats['pingScore'] / self.config.stats['pingCount'])


		return "Current Ping: {}ms\nPing till now: {}ms of {} pings".format(str(delta), str(truedelta), str(self.config.stats['pingCount']))

	async def weather(self, message):
		"""
		Displays the weather for a location.
		Syntax: `>weather (location)`
		"""
		args = self.cleanInput(message.content)
		if args[0] == '':
			self.log.warn("The member module is not ready yet.\n It will be implemented in a future update")
			return "This function requires membership storage.\nIf you're the owner of the bot. Check the logs."
		elif len(args) == 2:

			key = self.config.get("weather")

			if not key:
				return "Weather support has not been set up by adminstrator"
			url = "http://api.openweathermap.org/data/2.5/weather/?APPID={}&q={}&units={}".format(key, )

	async def reddit(self, message):
		"""
		Allows posting to a subreddit. Requires level 2 authorization as well as a reddit api key and an account.
		Syntax: `>reddit (post title) | (Your message) | (subreddit)`
		"""
		if not self.level4(message.author):
			return "You must have level4 access to perform this command"

		args = self.cleanInput(message.content)
		if len(args) < 3:
			return "You must have a title, a post and a subreddit. Check the help text"
		title = args[0]
		postdata = args[1]
		subredditstr = args[2]
		sub1=self.r.subreddit(subredditstr)


		response= sub1.submit(title, selftext=postdata, send_replies=False)
		return "Submitted post to " + subreddit

	# twitter (grasslands.bird)
	# tumblr(grasslands.ferret)
	# wolframAlpha(wa module)
	# configurator

	# Overwatch (grasslands.gorilla)
	# Weather (pyOWM)
