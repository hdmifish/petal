from ruamel import yaml
from .grasslands import Peacock
import urllib.request as urllib2
from datetime import datetime
import discord

log = Peacock() 

class Members(object):
	def __init__(self, client):
		log.info("Starting member module...")
		try:
			with open('members.yaml', 'r') as fp:
				self.doc = yaml.load(fp, Loader=yaml.RoundTripLoader)
					
		except IOError as e:
			log.err("Could not open members.yaml: " + str(e))
			exit()
		except Exception as e:
			log.err("An unexcpected exception of type: "
				+ type(e).__name__
				+ "has occurred: " + str(e))
			exit()
		else:
			if self.doc is None:
				log.warn("member database is empty. Attempting to fix...")
				response = urllib2.urlopen( "https://raw.githubusercontent.com/hdmifish/petal/master/example_members.yaml" )
				self.doc = yaml.load(response.read())
				log.warn("members.yaml was missing, so I created one using the default on my github")
			else:
				log.ready("members module is ready!")
		return 
	
	def addMember(self, mem):
		if mem.id in self.doc:
			return False
			if self.doc[mem.id]["name"] not in self.doc[mem.id]["aliases"]:
				self.doc[mem.id]["aliases"].append(self.doc[mem.id]["name"])
			else:
				self.doc[mem.id]["name"] = mem.name
		
			self.doc[mem.id]["joinedAt"].append(str(mem.joinedAt))

		else:
			self.doc[mem.id] = {"name": mem.name, "aliases":[], "joinedAt": [str(mem.joined_at)], "memberAt": "null", "leftAt": "null", "messageCount": 0, "lastOnline": datetime.utcnow(), "osu":"null", "weather": "null", "imgur": "aww", "warnings": {}, "isBanned": False, "tempBan": {}, "blockedChannels":[], "trackedEvents": {}, "notes": {}  }
			log.info( mem.name + " ID: " + mem.id + " was added to the member list")
			return True


	def getMember(self, id):
		if id in self.doc:
			self.doc[id]
			return self.doc[id]
		else:
			return None

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
			with open('members.yaml', 'w') as fp:
				yaml.dump(self.doc, fp, Dumper=yaml.RoundTripDumper)
		except PermissionError:
			log.err("No write access to members.yaml")
		except IOError as e:
			log.err("Could not open members.yaml: " + str(e))
		except Exception as e:
			log.err("An unexcpected exception of type: "
				+ type(e).__name__
				+ "has occurred: " + str(e) + " in members.yaml")
		else:
			if vb:
				log.info("Save complete")
		return

	

				
				 
				
				
					



