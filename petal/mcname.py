import json
import requests
import datetime

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
def breakUID(str0): # Break apart Mojang UUID with dashes
    str1 = str0[0:8]
    str2 = str0[8:12]
    str3 = str0[12:16]
    str4 = str0[16:20]
    str5 = str0[20:32]
    str99 = str1 + "-" + str2 + "-" + str3 + "-" + str4 + "-" + str5
    return str99

def writeLocalDB(player, dbIn): # update db from ephemeral player; write db to file
    pIndex = next((item for item in dbIn if item["uuid"] == player["uid_mc"]), False) # Is the player found in the list?
    ret = -2
    if pIndex == False: # Player is not in the database -- Create entry
        pIndex = len(dbIn) # Where the new player is about to be
        dbIn.append({})
        dbIn[pIndex] = {'uuid': player["uid_mc"], 'name': player["uname"], 'altname': [], 'discord': player["uid_dis"], 'approved': player["approved"]}
        dbIn[pIndex]["submitted"] = datetime.datetime.today().strftime('%Y-%m-%d_%0H:%M')
        ret = 0
    else:
        pIndex = dbIn.index(pIndex) # DBase index of player (integer 0+)
    if 'altname' not in dbIn[pIndex]:
        dbIn[pIndex]["altname"] = []
    if player["uname"] not in dbIn[pIndex]["altname"]:
        dbIn[pIndex]["altname"].append(player["uname"])
    dbIn[pIndex]["discord"] = player["uid_dis"]
    json.dump(dbIn, open(dbName, 'w'), indent=2)
    return ret

def addToLocalDB(userdat, submitter): # Add UID and username to local whitelist database
    uid = userdat["id"]
    uidF = breakUID(uid)
    uname = userdat["name"]
    eph = { # Create dict: Ephemeral player profile, to be merged into dbRead
        "uname" : uname, # Minecraft username; append to dbase usernames
        "uid_mc" : uidF, # Minecraft UID; use to locate or create dbase entry
        "uid_dis" : submitter, # Discord UID; attach to mc uid if not present
        "approved" : []
        }
    try:
        dbRead = json.load(open(dbName)) # dbRead is now a python object
    except OSError: # File does not exist: Create the file
        dbRead = [{'uuid': uidF, 'name': [uname]}]
    return writeLocalDB(eph, dbRead), uidF

def idFromName(uname_raw):
    uname_low = uname_raw.lower()
    response = requests.get("https://api.mojang.com/users/profiles/minecraft/{}".format(uname_low))
    if response.status_code == 204:
        return {'code':response.status_code}
    else:
        return {'code':response.status_code, 'udat':response.json() }

def WLRequest(nameGiven, discord_id):
    udict = idFromName(nameGiven) # Get the id from the name, or an error
    if udict["code"] == 200: # If this is 200, the second part will contain json data; Try to add it
        verdict, uid = addToLocalDB(udict["udat"], discord_id)
        return verdict, uid
# Map response codes to function errors
    elif udict["code"] == 204:
        return -8, "x"
    #elif udict["code"] == 200:
        #return 
    else:
        return "Nondescript Error ({})".format(udict["code"])

def WLAdd(idTarget, idSponsor):
    try:
        dbRead = json.load(open(dbName)) # dbRead is now a python object
    except OSError: # File does not exist: Pointless to continue
        return -8
    # idTarget can be a Discord ID, Mojang ID, or Minecraft username; Search for all of these
    pIndex = next((item for item in dbRead if item["uuid"] == idTarget), False) # Is the target player found in the database?

    if pIndex == False: # Maybe try the Minecraft name?
        pIndex = next((item for item in dbRead if item["name"].lower() == idTarget.lower()), False)

    if pIndex == False: # ...Discord ID?
        pIndex = next((item for item in dbRead if item["discord"] == idTarget), False)

    if pIndex == False: # Fine. Player is not in the database -- Refuse to continue
        ret = -8
    else:
        pIndex = dbRead.index(pIndex) # DBase index of player (integer 0+)
        if idSponsor not in dbRead[pIndex]["approved"]: # User approves new whitelisting
            dbRead[pIndex]["approved"].append(idSponsor)
            ret = 0
        else: # User has already approved whitelisting
            ret = -2
    json.dump(dbRead, open(dbName, 'w'), indent=2)
    return ret
