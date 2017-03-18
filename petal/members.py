import json
from .grasslands import Peacock
import urllib.request as urllib2
from datetime import datetime
from datetime import timedelta
import discord
import asyncio

log = Peacock()

class Members(object):
	def __init__(self, client):
		log.info("Starting member module...")
		try:
			with open('members.json', 'r') as fp:
				self.doc = json.load(fp)
				self.client = client
				log.info("Using local member database file")

		except IOError as e:

			log.err("Could not open members.json: " + str(e))
			response = urllib2.urlopen( "https://raw.githubusercontent.com/hdmifish/petal/master/example_members.json" ).read()
			self.doc = json.loads(response.decode('utf-8'))
			log.warn("members.json was missing, so I created one using the default on github")
			fp = open('members.json', 'w+')
			json.dump(self.doc, fp, indent=4)
			fp.close()
		except Exception as e:

			log.err("An unexcpected exception of type: "
				+ type(e).__name__
				+ "has occurred: " + str(e))
			exit()
		else:
			if self.doc is None:
				log.warn("member database is empty. Attempting to fix...")
				response = urllib2.urlopen( "https://raw.githubusercontent.com/hdmifish/petal/master/example_members.json" ).read()
				self.doc = json.loads(response.decode('utf-8'))
				log.warn("members.json was missing, so I created one using the default on my github")
			log.ready("members module is ready!")
			return

	def addMember(self, mem):
		if mem.id in self.doc:

			if self.doc[mem.id]["name"] not in self.doc[mem.id]["aliases"]:
				self.doc[mem.id]["aliases"].append(self.doc[mem.id]["name"])
			else:
				self.doc[mem.id]["name"] = mem.name
			try:
				self.doc[mem.id]["joinedAt"].append(str(mem.joined_at))
			except KeyError:
				self.doc[mem.id]["joinedAt"] = [str(datetime.utcnow())]
			except AttributeError:
				self.doc[mem.id]["joinedAt"] = [self.doc[mem.id]["joinedAt"]].append(str(mem.joined_at))
			return False
		else:
			self.doc[mem.id] = {"name": mem.name, "aliases":[],  "memberAt": "null", "leftAt": "null", "messageCount": 0, "lastOnline": str(datetime.utcnow()), "osu":"null", "weather": "null", "imgur": "aww", "warnings": {}, "isBanned": False, "tempBan": {}, "blockedChannels":[], "trackedEvents": {}, "notes": {}  }
			log.info( mem.name + " ID: " + mem.id + " was added to the member list")
			return True


	def getMember(self, id):
		if id in self.doc:
			self.doc[id]
			return self.doc[id]
		else:
			return None

	async def tempBan(self, member, author, reason, Days):
		if member.id not in self.doc:
			log.err("Invalid member to ban")
			return False
		elif self.doc[member.id]["isBanned"]:
			return False
		else:
			self.doc[member.id]["isBanned"] = True
			self.doc[member.id]["tempBan"][str(len(self.doc[member.id]["tempBan"]))] = {"server": member.server.id, "active": True, "date": str(datetime.utcnow()), "expires": str(datetime.utcnow() + timedelta(days=Days)), "issuer": author.name + " ({})".format(author.id), "reason": reason }
			await self.client.ban(member)
			return True

	def searchMembers(self, name):
		results = []
		for mem in self.doc:
			if name in mem["name"]:
				results.append(mem)
		if len(results) == 0:
			return None
		else:
			return results

	def save(self, vb=False):
		try:
			with open('members.json', 'w') as fp:
				json.dump(self.doc, fp, indent=4)
		except PermissionError:
			log.err("No write access to members.json")
		except IOError as e:
			log.err("Could not open members.json: " + str(e))
		except Exception as e:
			log.err("An unexcpected exception of type: "
				+ type(e).__name__
				+ "has occurred: " + str(e) + " in members.json")
		else:
			if vb:
				log.info("Save complete")
		return
