import json
import requests
import datetime
from collections import OrderedDict
from .grasslands import Peacock
__all__ = ["WLRequest", "WLAdd", "WLQuery", "WLSuspend", "EXPORT_WHITELIST"]
dbName = "/minecraft/playerdb.json" # file in which userdata is stored
WhitelistFile = "/minecraft/whitelist.json" # The whitelist file itself
log = Peacock()
"""
ERROR CODES:
 0: Cmnd success: user added or approved, or request sent
-1: Benign error: duplicate request which has been approved
-2: Benign error: duplicate request or approval
-3:
-4:
-5:
-6:
-7: Malign error: failed to access dbName or WhitelistFile
-8: Malign error: user supplied invalid name
-9: Malign error: incomplete function (fault of developer)
"""
    # The default profile for a new player being added to the database
    # (Do not use this)
PLAYERDEFAULT = OrderedDict([('name', 'PLAYERNAME'), ('uuid', '00000000-0000-0000-0000-000000000000'), ('altname', []), ('discord', '000000000000000000'), ('approved', []), ('submitted', '1970-01-01_00:00'), ('suspended', False)])

def EXPORT_WHITELIST(refreshall=False, refreshnet=False):
    # Export the local database into the whitelist file itself
    # If Mojang ever changes the format of the server whitelist file, this is the function that will need to be updated
    try: # Stage 0: Load the full database as ordered dicts, and the whitelist as dicts
        dbRead = json.load(open(dbName), object_pairs_hook=OrderedDict)
        wlFile = json.load(open(WhitelistFile))
        #wlFile = [] # Uncommenting this will force the whitelist to contain ONLY people in the DB file
                     # (This will also force the whitelist file to be in the same order as the DB file)
    except OSError: # File does not exist: Pointless to continue
        return 0

    if refreshall == True: # Rebuild Index
        dbNew = [] # Stage 1: Make new DB
        for applicant in dbRead: # Stage 2: Find entries in old DB, import their stuff
            appNew = PLAYERDEFAULT.copy()
            appNew.update(applicant)

            if refreshnet == True: # Stage 3, optional: Rebuild username history
                namehist = requests.get("https://api.mojang.com/user/profiles/{}/names".format(applicant["uuid"].replace("-","")))

                if namehist.status_code == 200:
                    appNew.update(altname=[]) # Spy on their dark and shadowy past
                    for name in namehist.json():
                        appNew["altname"].append(name["name"])
                        appNew["name"] = name["name"] # Ensure the name is up to date

            dbNew.append(appNew)
        json.dump(dbNew, open(dbName, 'w'), indent=2)
        dbRead = dbNew

    for applicant in dbRead: # Check everyone who has applied
        app = next((item for item in wlFile if item["uuid"] == applicant["uuid"]), False) # Is the applicant already whitelisted?
        if app == False and len(applicant["approved"]) > 0 and applicant["suspended"] == False: # Applicant is not whitelisted AND is approved, add them
            wlFile.append({'uuid': applicant["uuid"], 'name': applicant["name"]})
        elif app != False and applicant["suspended"] == True: #BadPersonAlert, remove them
            wlFile.remove(app)

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

def writeLocalDB(player): # update db from ephemeral player; write db to file

    try:
        dbRead = json.load(open(dbName), object_pairs_hook=OrderedDict) # dbRead is now a python object
    except OSError: # File does not exist: Create the file
        dbRead = [{'uuid': uidF, 'name': [uname]}]

    pIndex = next((item for item in dbRead if item["uuid"] == player["uuid"]), False) # Is the player found in the list?

    if pIndex == False: # Player is not in the database -- Create entry

        # Fetch username history
        namehist = requests.get("https://api.mojang.com/user/profiles/{}/names".format(player["uuid"].replace("-","")))
        if namehist.status_code == 200:
            player["altname"] = []
            for name in namehist.json():
                player["altname"].append(name["name"])

        dbRead.append(player) # Set up a new profile with all the right fields
        ret = 0
    else:
        pIndex = dbRead.index(pIndex) # DBase index of player (integer 0+)
        if len(dbRead[pIndex]["approved"]) > 0: # If the user is approved, say something different
            ret = -1
        else:
            ret = -2
    try:
        json.dump(dbRead, open(dbName, 'w'), indent=2) # Save all the things
    except OSError: # Cannot write file: Well this was all rather pointless
        ret = -7
    return ret

# User wants to be whitelisted? Add to the database for approval
def addToLocalDB(userdat, submitter):
    uid = userdat["id"]
    uidF = breakUID(uid)
    uname = userdat["name"]
    eph = { # Create dict: Ephemeral player profile, to be merged into dbRead
        "name" : uname, # Minecraft username; append to dbase usernames
        "uuid" : uidF, # Minecraft UID; use to locate or create dbase entry
        "discord" : submitter, # Discord UID; attach to mc uid if not present
        "submitted" : datetime.datetime.today().strftime('%Y-%m-%d_%0H:%M')
        }
    # Apply the values to a blank slate
    pNew = PLAYERDEFAULT.copy() # Get the slate
    pNew.update(eph) # Imprint anything new from the player
    return writeLocalDB(pNew), uidF

# User gave us a username? Text is worthless. Hey Mojang, UUID is this name?
def idFromName(uname_raw):
    uname_low = uname_raw.lower()
    response = requests.get("https://api.mojang.com/users/profiles/minecraft/{}".format(uname_low))
    log.f("WLME_RESP", str(response))
    if response.status_code == 200:
        return {'code':response.status_code, 'udat':response.json() }
    else:
        return {'code':response.status_code}

###---
##  Top Level Commands - Invoked by Discord users
###---

# !wlme <username>
def WLRequest(nameGiven, discord_id):
    udict = idFromName(nameGiven) # Get the id from the name, or an error
    if udict["code"] == 200: # If this is 200, the second part will contain json data; Try to add it
        verdict, uid = addToLocalDB(udict["udat"], discord_id)
        return verdict, uid
    # Map response codes to function errors
    elif udict["code"] == 204:
        log.err("wlrequest failed with 204")
        return -8, "x"
    #elif udict["code"] == 200:
        #return
    else:
        return "Nondescript API Error ({})".format(udict["code"])



# !wl <ticket>
def WLAdd(idTarget, idSponsor):
    try:
        dbRead = json.load(open(dbName), object_pairs_hook=OrderedDict) # dbRead is now a python object
    except OSError as e: # File does not exist: Pointless to continue
        log.err("OSError: " + str(e))
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
        log.f("wlme", "IndexError player not in DB")
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



# !wlquery <ticket>
def WLQuery(instr):
    try:
        dbRead = json.load(open(dbName)) # dbRead is now a python object
    except OSError as e: # File does not exist: Pointless to continue
        log.err("OSError on query " + str(e))
        return -7
    res = []
    for entry in dbRead:
        for attr in entry:
            if entry[attr] == instr and entry not in res:
                res.append(entry)
        if instr.lower() in (val.lower() for val in entry["altname"]) and entry not in res:
            res.append(entry)
    return res



# !wlsuspend bad_person
def WLSuspend(baddies, sus=True):
    try:
        dbRead = json.load(open(dbName), object_pairs_hook=OrderedDict) # dbRead is now a python object
    except OSError: # File does not exist: Pointless to continue
        return -7
    actions = []
    for target in baddies:
        act = 0
        try:
            found = dbRead[dbRead.index(target)]
        except OSError:
            act = -8
        else:
            if found["suspended"] == sus:
                if sus == True:
                    act = -2 # -2: Already suspended
                else:
                    act = -3 # -1: Already forgiven
            else:
                if sus == True:
                    act = 0 # 0: Suspended
                else:
                    act = -1 # -1: Forgiven
            found["suspended"] = sus
        actions.append({"name" : target["name"], "change" : act})
    try:
        json.dump(dbRead, open(dbName, 'w'), indent=2) # Save all the things
    except OSError: # oh no
        for revise in actions:
            revise["change"] = -7 # Could not update the database, so NOTHING that we just did actually saved
    wlwin = EXPORT_WHITELIST()
    return actions, wlwin
