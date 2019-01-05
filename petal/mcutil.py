import json
import requests
import datetime

from collections import OrderedDict
from .grasslands import Peacock

__all__ = ["Minecraft"]
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
# (Do not use this for other stuff)
PLAYERDEFAULT = OrderedDict(
    [
        ("name", "PLAYERNAME"),
        ("uuid", "00000000-0000-0000-0000-000000000000"),
        ("altname", []),
        ("discord", "000000000000000000"),
        ("approved", []),
        ("submitted", "1970-01-01_00:00"),
        ("suspended", 000),
        ("operator", 0),
        ("notes", []),
    ]
)

SUSPENSION = {
    True: "Nonspecific suspension",
    False: "Not suspended",
    000: "Not suspended",
    # Trivial suspensions
    101: "Joke suspension",
    102: "Self-sequested suspension",
    103: "Old Account",
    104: "User not in Discord",
    # Minor suspensions
    201: "Minor trolling",
    203: "Compromised Account",
    # Moderate suspensions
    301: "Major trolling",
    302: "Stealing",
    # Major suspensions
    401: "Use of slurs",
    402: "Griefing",
    403: "Discord banned",
}

# Break apart Mojang UUID with dashes
def breakUID(str0):
    str1 = str0[0:8]
    str2 = str0[8:12]
    str3 = str0[12:16]
    str4 = str0[16:20]
    str5 = str0[20:32]
    str99 = "-".join([str1, str2, str3, str4, str5])
    return str99


# User gave us a username? Text is worthless. Hey Mojang, UUID is this name?
def idFromName(uname_raw):
    uname_low = uname_raw.lower()
    response = requests.get(
        "https://api.mojang.com/users/profiles/minecraft/{}".format(uname_low)
    )
    log.f("WLME_RESP", str(response))
    if response.status_code == 200:
        return {"code": response.status_code, "udat": response.json()}
    else:
        return {"code": response.status_code}


# The lower level tools that actually get stuff done; Called by the main Minecraft class
class WLStuff:
    def __init__(self, client):
        self.client = client
        self.config = client.config

    def cget(self, prop):
        v = self.config.get(prop)
        if v == "<poof>":
            v = None
        return v

    @property
    def dbName(self):
        return self.cget("minecraftDB")

    @property
    def WhitelistFile(self):
        return self.cget("minecraftWL")

    @property
    def OpFile(self):
        return self.cget("minecraftOP")

    def WLDump(self):
        try:
            with open(self.dbName) as fh:
                dbRead = json.load(fh, object_pairs_hook=OrderedDict)
        except OSError as e:
            # File does not exist: Pointless to continue
            log.err("OSError on DB read: " + str(e))
            return -7
        return dbRead

    def WLSave(self, dbRead):
        try:
            with open(self.dbName, "w") as fh:
                json.dump(dbRead, fh, indent=2)
                # Save all the things
            ret = 0
        except OSError as e:
            # Cannot write file: Well this was all rather pointless
            log.err("OSError on DB save: " + str(e))
            ret = -7
        return ret

    def EXPORT_WHITELIST(self, refreshall=False, refreshnet=False):
        """Export the local database into the whitelist file itself\n\nIf Mojang ever changes the format of the server whitelist file, this is the function that will need to be updated"""
        try:
            # Stage 0: Load the full database as ordered dicts, and the whitelist as dicts
            strict = self.cget("minecraftStrictWL")
            with open(self.dbName, "r") as fh, open(self.WhitelistFile, "r") as WLF:
                dbRead = json.load(fh, object_pairs_hook=OrderedDict)
                if strict:
                    wlFile = []
                else:
                    wlFile = json.load(WLF)
        except OSError:
            # File does not exist: Pointless to continue
            return 0
        opFile = []  # Op list is always strict

        if refreshall:
            # Rebuild Index
            dbNew = []
            # Stage 1: Make new DB
            for applicant in dbRead:
                # Stage 2: Find entries in old DB, import their stuff
                appNew = PLAYERDEFAULT.copy()
                appNew.update(applicant)

                if refreshnet:
                    # Stage 3, optional: Rebuild username history
                    namehist = requests.get(
                        "https://api.mojang.com/user/profiles/{}/names".format(
                            applicant["uuid"].replace("-", "")
                        )
                    )

                    if namehist.status_code == 200:
                        # Spy on their dark and shadowy past
                        appNew.update(altname=[])
                        for name in namehist.json():
                            appNew["altname"].append(name["name"])
                            # Ensure the name is up to date
                            appNew["name"] = name["name"]

                dbNew.append(appNew)
            with open(self.dbName, "w") as fh:
                json.dump(dbNew, fh, indent=2)
            dbRead = dbNew

        for applicant in dbRead:  # Check everyone who has applied
            app = next(
                (item for item in wlFile if item["uuid"] == applicant["uuid"]), False
            )
            # Is the applicant already whitelisted?
            if (
                app == False
                and len(applicant["approved"]) > 0
                and not applicant["suspended"]
            ):
                # Applicant is not whitelisted AND is approved AND is not suspended, add them
                wlFile.append({"uuid": applicant["uuid"], "name": applicant["name"]})
            elif app != False and applicant["suspended"] and app in wlFile:
                # BadPersonAlert, remove them
                wlFile.remove(app)

            # Is the applicant supposed to be an op?
            level = applicant.get("operator", 0)
            applicant["operator"] = level
            if level > 0:
                opFile.append(
                    {
                        "uuid": applicant["uuid"],
                        "name": applicant["name"],
                        "level": level,
                        "bypassesPlayerLimit": False,
                    }
                )

        log.f("wl+", "Refreshing Whitelist")
        with open(self.OpFile, "w") as OPF:
            json.dump(opFile, OPF, indent=2)
        with open(self.WhitelistFile, "w") as WLF:
            json.dump(wlFile, WLF, indent=2)
        return 1

    # update db from ephemeral player; write db to file
    def writeLocalDB(self, player):
        dbRead = self.WLDump()
        if dbRead == -7:  # File does not exist: Create the file
            dbRead = []

        pIndex = next(
            (item for item in dbRead if item["uuid"] == player["uuid"]), False
        )
        # Is the player found in the list?

        if not pIndex:
            # Player is not in the database -- Create entry

            # Fetch username history
            namehist = requests.get(
                "https://api.mojang.com/user/profiles/{}/names".format(
                    player["uuid"].replace("-", "")
                )
            )
            if namehist.status_code == 200:
                player["altname"] = []
                for name in namehist.json():
                    player["altname"].append(name["name"])

            # Set up a new profile with all the right fields
            dbRead.append(player)
            ret = 0
        else:
            pIndex = dbRead.index(pIndex)  # DBase index of player (integer 0+)
            if (
                len(dbRead[pIndex]["approved"]) > 0
            ):  # If the user is approved, say something different
                ret = -1
            else:
                ret = -2
        if self.WLSave(dbRead) != 0:
            ret = -7
        return ret

    # User wants to be whitelisted? Add to the database for approval
    def addToLocalDB(self, userdat, submitter):
        uid = userdat["id"]
        uidF = breakUID(uid)
        uname = userdat["name"]
        eph = {  # Create dict: Ephemeral player profile, to be merged into dbRead
            "name": uname,  # Minecraft username; append to dbase usernames
            "uuid": uidF,  # Minecraft UID; use to locate or create dbase entry
            "discord": submitter,  # Discord UID; attach to mc uid if not present
            "submitted": datetime.datetime.today().strftime("%Y-%m-%d_%0H:%M"),
        }
        # Apply the values to a blank slate
        pNew = PLAYERDEFAULT.copy()  # Get the slate
        pNew.update(eph)  # Imprint anything new from the player
        return self.writeLocalDB(pNew), uidF


###---
##  Top Level Commands - Invoked via commands in Discord
###---


class Minecraft:
    def __init__(self, client):
        self.client = client
        self.config = client.config

        self.etc = WLStuff(client)
        self.suspend_table = SUSPENSION

    # !wlme <username>
    def WLRequest(self, nameGiven, discord_id):
        udict = idFromName(nameGiven)  # Get the id from the name, or an error
        if udict["code"] == 200:
            # If this is 200, the second part will contain json data; Try to add it
            verdict, uid = self.etc.addToLocalDB(udict["udat"], discord_id)
            return verdict, uid
        # Map response codes to function errors
        elif udict["code"] == 204:
            log.err("wlrequest failed with 204")
            return -8, "x"
        else:
            return "Nondescript API Error ({})".format(udict["code"])

    # !wl <ticket>
    def WLAdd(self, idTarget, idSponsor):
        dbRead = self.etc.WLDump()
        if dbRead == -7:
            return -7

        targetid = -1
        targetname = "<Error>"
        doSend = False

        # idTarget can be a Discord ID, Mojang ID, or Minecraft username; Search for all of these
        pIndex = next((item for item in dbRead if item["uuid"] == idTarget), False)
        # Is the target player found in the database?

        if not pIndex:
            # Maybe try the Minecraft name?
            pIndex = next(
                (item for item in dbRead if item["name"].lower() == idTarget.lower()),
                False,
            )

        if not pIndex:
            # ...Discord ID?
            pIndex = next(
                (item for item in dbRead if item["discord"] == idTarget), False
            )

        if not pIndex:
            # Fine. Player is not in the database -- Refuse to continue
            log.f("wlme", "IndexError player not in DB")
            ret = -8
        else:
            targetid = pIndex["discord"]
            targetname = pIndex["name"]
            if idSponsor not in pIndex["approved"]:
                # User approves new whitelisting
                pIndex["approved"].append(idSponsor)
                ret = 0
                if len(pIndex["approved"]) == 1:
                    # User is the first approver
                    doSend = True
                    # Send the person a PM
            else:
                # User has already approved whitelisting
                ret = -2

        if self.etc.WLSave(dbRead) != 0:
            ret = -7
        return ret, doSend, targetid, targetname, self.etc.EXPORT_WHITELIST()

    # !wlquery <ticket>
    def WLQuery(self, instr):
        dbRead = self.etc.WLDump()
        if dbRead == -7:
            return -7
        res = []
        in2 = instr.split(" ")
        while "" in in2:
            in2.remove("")
        for in3 in in2:
            for entry in dbRead:
                for attr in entry:
                    if entry[attr] == in3 and entry not in res:
                        res.append(entry)
                if (
                    in3.lower() in (val.lower() for val in entry["altname"])
                    and entry not in res
                ):
                    res.append(entry)
        return res

    # !wlsuspend bad_person
    def WLSuspend(self, baddies, sus=True):
        dbRead = self.etc.WLDump()
        if dbRead == -7:
            # File does not exist: Pointless to continue
            return -7
        actions = []
        for target in baddies:
            try:
                found = dbRead[dbRead.index(target)]
            except OSError:
                act = -8
            else:
                if found["suspended"] == sus:
                    if sus:
                        # Already suspended
                        act = -2
                    else:
                        # Already forgiven
                        act = -3
                else:
                    if sus:
                        # Suspended
                        act = 0
                    else:
                        # Forgiven
                        act = -1
                found["suspended"] = sus
            actions.append({"name": target["name"], "change": act})
        try:
            with open(self.etc.dbName, "w") as fh:
                json.dump(dbRead, fh, indent=2)  # Save all the things
            wlwin = self.etc.EXPORT_WHITELIST()
        except OSError:  # oh no
            for revise in actions:
                revise["change"] = -7
                # Could not update the database, so NOTHING that we just did actually saved
            wlwin = 0
        return actions, wlwin

    def WLMod(self, newmod, newlevel):
        dbRead = self.etc.WLDump()
        if dbRead == -7:
            return -7

        targetid = -1
        targetname = "<Error>"
        doSend = False

        # newmod can be a Discord ID, Mojang ID, or Minecraft username; Search for all of these
        pIndex = next((item for item in dbRead if item["uuid"] == newmod), False)
        # Is the target player found in the database?

        if not pIndex:
            # Maybe try the Minecraft name?
            pIndex = next(
                (item for item in dbRead if item["name"].lower() == newmod.lower()),
                False,
            )

        if not pIndex:
            # ...Discord ID?
            pIndex = next((item for item in dbRead if item["discord"] == newmod), False)

        if not pIndex:
            # Fine. Player is not in the database -- Refuse to continue
            log.f("wl+", "IndexError player not in DB")
            ret = -8
        else:
            targetid = pIndex["discord"]
            targetname = pIndex["name"]
            pIndex["operator"] = newlevel
            log.f(
                "wl+",
                "{} was given Level {} Operator status".format(
                    *[str(term) for term in [targetid, newlevel]]
                ),
            )
            ret = 0

        if self.etc.WLSave(dbRead) != 0:
            ret = -6
        return ret, doSend, targetid, targetname, self.etc.EXPORT_WHITELIST()

    def WLNote(self, user, note):
        dbRead = self.etc.WLDump()
        if dbRead == -7:
            return -7

        # user can be a Discord ID, Mojang ID, or Minecraft username; Search for all of these
        pIndex = next((item for item in dbRead if item["uuid"] == user), False)
        # Is the target player found in the database?

        if not pIndex:
            # Maybe try the Minecraft name?
            pIndex = next(
                (item for item in dbRead if item["name"].lower() == user.lower()), False
            )

        if not pIndex:
            # ...Discord ID?
            pIndex = next((item for item in dbRead if item["discord"] == user), False)

        if not pIndex:
            # Fine. Player is not in the database -- Refuse to continue
            log.f("wl+", "IndexError player not in DB")
            ret = -8
        else:
            targetid = pIndex["discord"]
            pIndex["notes"].append(note)
            log.f(
                "wl+",
                "{} has been noted: `{}`".format(
                    *[str(term) for term in [targetid, note]]
                ),
            )
            ret = 0

        if self.etc.WLSave(dbRead) != 0:
            ret = -6
        self.etc.EXPORT_WHITELIST()
        return ret

    def WLAuthenticate(self, msg, clearance=3):
        entries = self.WLQuery(str(msg.author.id))
        for e in entries:
            try:
                if e["discord"] == str(msg.author.id) and e["operator"] >= clearance:
                    return True
            except:
                continue
        return False
