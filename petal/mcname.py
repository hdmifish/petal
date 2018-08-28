import json
import requests

dbName = "playerdb.json" # file in which userdata is stored

"""
ERROR CODES:
 0: Successful cmmnd: user added to local database to be approved and synced with whitelist
-1: Benevolent error: user already whitelisted
-2: Benevolent error: user already requested whitelisting
-3:
-4:
-5:
-6:
-7:
-8: Malevolent error: user supplied erroneous name
-9: Malevolent error: incomplete function (fault of developer)
"""
class Player:
    def __init__(self, discord_id, uuid, uname):
        self.discord_uuid = discord_id # discord uuid
        self.minecraft_uuid = uuid # minecraft/mojang uuid
        self.minecraft_name = uname # minecraft username (added to list of known aliases)
        self.approved = [] # list of discord uuids who approved the whitelisting

    def approve(self, sponsor):
        self.approved.append(sponsor)

"""
TODO:
load json database
find player in json database
edit player:
	add discord id
	add mc name
save json database
"""

def writeLocalDB(player, dbIn): # read db; update db from ephemeral player; write db to file
    
    return -9

def createLocalDB(player0): # use the ephemeral player as the first entry in a new file
    
    return -9

def addToLocalDB(userdat, submitter): # Add UID and username to local whitelist database
    uid = userdat["id"]
    uname = userdat["name"]
    #print(uname + " has uuid " + uid)
    try:
        dbRead = json.load(open(dbName)) # dbRead is now a python object
    except OSError: # TODO: file does not exist: create the file
        return -9 # TODO: remove this when the file creation is implemented
    return 0

def idFromName(uname_raw):
    uname_low = uname_raw.lower()
    response = requests.get("https://api.mojang.com/users/profiles/minecraft/{}".format(uname_low))
    return {'code':response.status_code, 'udat':response.json() }
    #if code == 200:
        #return json.loads(response.text)
    #else:
        #return -1

def WLRequest(nameGiven, discord_id):
    udict = idFromName(nameGiven) # Get the id from the name, or an error
    if udict["code"] == 200: # If this is 200, the second part will contain json data; Try to add it
        verdict = addToLocalDB(udict["udat"], discord_id)
        return verdict
# Map response codes to function errors
    #elif udict["code"] == 200:
        #return 
    else:
        return "Nondescript Error ({})".format(udict["code"])

