import json
import requests
import datetime
from collections import OrderedDict

dbName = "playerdb.json" # file in which userdata is stored
WhitelistFile = "whitelist.json" # The whitelist file itself
"""
ERROR CODES:
 0: Successful cmmnd: user added or approved, or request sent
-1: Benevolent error: duplicate request which has been approved
-2: Benevolent error: duplicate request or approval
-3:
-4:
-5:
-6:
-7: Malevolent error: failed to access dbName or WhitelistFile
-8: Malevolent error: user supplied invalid name
-9: Malevolent error: incomplete function (fault of developer)
"""
    # The default profile for a new player being added to the database
    # (Do not use this)
PLAYERDEFAULT = OrderedDict([('name', 'PLAYERNAME'), ('uuid', '00000000-0000-0000-0000-000000000000'), ('altname', []), ('discord', '000000000000000000'), ('approved', []), ('submitted', '1970-01-01_00:00'), ('suspended', False)])

def EXPORT_WHITELIST(refreshall=False):
    # Export the local database into the whitelist file itself
    # If Mojang ever changes the format of the server whitelist file, this is the function that will need to be updated
    try:
        dbRead = json.load(open(dbName), object_pairs_hook=OrderedDict) # Load the local database
        wlFile = json.load(open(WhitelistFile)) # Load current whitelist
    except OSError: # File does not exist: Pointless to continue
        return 0

    if refreshall == True: # Rebuild Index
        dbNew = [] # Stage 1
        for applicant in dbRead:
            appNew = PLAYERDEFAULT.copy()
            appNew.update(applicant)

            namehist = requests.get("https://api.mojang.com/user/profiles/{}/names".format(applicant["uuid"].replace("-","")))

            if namehist.status_code == 200:
                appNew.update(altname=[]) # Spy on their dark and shadowy past
                for name in namehist.json():
                    appNew["altname"].append(name["name"])
            dbNew.append(appNew)
        json.dump(dbNew, open(dbName, 'w'), indent=2)

    for applicant in dbRead: # Check everyone who has applied
        app = next((item for item in wlFile if item["uuid"] == applicant["uuid"]), False) # Is the applicant already whitelisted?
        if app == False and len(applicant["approved"]) > 0: # Applicant is not whitelisted AND is approved
            wlFile.append({'uuid': applicant["uuid"], 'name': applicant["name"]})

    json.dump(wlFile, open(WhitelistFile, 'w'), indent=2)
    return 1

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
        dbIn[pIndex] = {'uuid': player["uid_mc"], 'name': player["uname"], 'altname': [], 'discord': player["uid_dis"], 'approved': player["approved"], 'suspended': player["suspended"]}
        dbIn[pIndex]["submitted"] = datetime.datetime.today().strftime('%Y-%m-%d_%0H:%M')
        ret = 0
    else:
        pIndex = dbIn.index(pIndex) # DBase index of player (integer 0+)
        if len(dbIn[pIndex]["approved"]) > 0: # If the user is approved, change feedback
            ret = -1

    # Fetch username history
    dbIn[pIndex]["altname"] = []
    namehist = requests.get("https://api.mojang.com/user/profiles/{}/names".format(player["uid_mc"].replace("-","")))

    if namehist.status_code == 200:
        for name in namehist.json():
            dbIn[pIndex]["altname"].append(name["name"])


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
        "approved" : [],
        "suspended" : False
        }
    try:
        dbRead = json.load(open(dbName), object_pairs_hook=OrderedDict) # dbRead is now a python object
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
        dbRead = json.load(open(dbName), object_pairs_hook=OrderedDict) # dbRead is now a python object
    except OSError: # File does not exist: Pointless to continue
        return -7
    # idTarget can be a Discord ID, Mojang ID, or Minecraft username; Search for all of these
    pIndex = next((item for item in dbRead if item["uuid"] == idTarget), False) # Is the target player found in the database?

    targetid = -1
    targetname = "<Error>"
    doSend = False

    if pIndex == False: # Maybe try the Minecraft name?
        pIndex = next((item for item in dbRead if item["name"].lower() == idTarget.lower()), False)

    if pIndex == False: # ...Discord ID?
        pIndex = next((item for item in dbRead if item["discord"] == idTarget), False)

    if pIndex == False: # Fine. Player is not in the database -- Refuse to continue
        ret = -8
    else:
        targetid = pIndex["discord"]
        targetname = pIndex["name"]
        #pIndex = dbRead.index(pIndex) # DBase index of player (integer 0+) # why?
        if idSponsor not in pIndex["approved"]: # User approves new whitelisting
            pIndex["approved"].append(idSponsor)
            ret = 0
            if len(pIndex["approved"]) == 1: # User is the first approver
                doSend = True # Send the person a PM
        else: # User has already approved whitelisting
            ret = -2

    json.dump(dbRead, open(dbName, 'w'), indent=2)
    return ret, doSend, targetid, targetname, EXPORT_WHITELIST()

def WLQuery(instr):
    try:
        dbRead = json.load(open(dbName)) # dbRead is now a python object
    except OSError: # File does not exist: Pointless to continue
        return -7
    res = []
    for entry in dbRead:
        for attr in entry:
            if entry[attr] == instr and entry not in res:
                res.append(entry)
        if instr.lower() in (val.lower() for val in entry["altname"]) and entry not in res:
            res.append(entry)
    return res
