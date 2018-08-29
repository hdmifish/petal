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

"""
TODO:
load json database
find player in json database
edit player:
	add discord id
	add mc name
save json database
"""

def breakUID(str0): # Break apart Mojang UUID with dashes
    str1 = str0[0:8]
    str2 = str0[8:12]
    str3 = str0[12:16]
    str4 = str0[16:20]
    str5 = str0[20:32]
    str99 = str1 + "-" + str2 + "-" + str3 + "-" + str4 + "-" + str5
    return str99

def writeLocalDB(player, dbIn): # update db from ephemeral player; write db to file
    
    return -9

def createLocalDB(player0): # use the ephemeral player as the first entry in a new file
    
    return -9

def addToLocalDB(userdat, submitter): # Add UID and username to local whitelist database
    uid = userdat["id"]
    uidF = breakUID(uid)
    uname = userdat["name"]
    #print(uname + " has uuid " + uid)
    eph = { # Create dict: Ephemeral player profile, to be merged into dbRead
        "uname" : uname, # Minecraft username; append to dbase usernames
        "uid_mc" : uidF, # Minecraft UID; use to locate or create dbase entry
        "uid_dis" : submitter, # Discord UID; attach to mc uid if not present
        "approved" : []
        }
    try:
        dbRead = json.load(open(dbName)) # dbRead is now a python object
    except OSError: # TODO: file does not exist: create the file
        dbRead = createLocalDB(userdat)
        return -9 # TODO: remove this when the file creation is implemented
    #playerIndex = dbRead.index(next(filter(lambda n: n.get('uuid') == uid, dbRead)))
    plr = next((item for item in dbRead if item["uuid"] == uidF), False)
    if plr == False: # Player is not whitelisted -- Create entry
        print("plr = False")
        return dbRead, -99
    else: # Player is whitelisted -- Update entry with any new info
        playerIndex = dbRead.index(plr)
        #return -1
    return dbRead, playerIndex

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

