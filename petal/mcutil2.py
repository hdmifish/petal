"""FIXME: INCOMPLETE MODULE FOR MINECRAFT UTILITY REWRITE; DO NOT USE"""

import json
import datetime
from uuid import UUID

import requests

from collections import OrderedDict
from .grasslands import Peacock

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
    103: "Old account",
    104: "User not in Discord",
    # Minor suspensions
    201: "Minor trolling",
    203: "Compromised account",
    # Moderate suspensions
    301: "Major trolling",
    302: "Stealing",
    # Major suspensions
    401: "Use of slurs",
    402: "Griefing",
    403: "Discord banned",
}


def break_uid(uuid: str):
    """Given an undashed UUID, break it into five fields."""
    f = [hex(c)[2:] for c in UUID(uuid).fields]
    return "-".join(f[:3] + [f[3] + f[4], f[5]])


# User gave us a username? Text is worthless. Hey Mojang, what UUID is this name?
def id_from_name(uname_raw):
    uname_low = uname_raw.lower()
    response = requests.get(
        "https://api.mojang.com/users/profiles/minecraft/{}".format(uname_low)
    )
    log.f("WLME_RESP", str(response))
    if response.status_code == 200:
        return {"code": response.status_code, "udat": response.json()}
    else:
        return {"code": response.status_code}


class Interface:
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

    def db_read(self):
        try:
            with open(self.dbName) as fh:
                dbRead = json.load(fh, object_pairs_hook=OrderedDict)
        except OSError as e:
            # File does not exist: Pointless to continue.
            log.err("OSError on DB read: " + str(e))
            return -7
        return dbRead

    def db_write(self, data):
        try:
            with open(self.dbName, "w") as fh:
                # Save all the things.
                json.dump(data, fh, indent=2)
            return 0
        except OSError as e:
            # Cannot write file: Well this was all rather pointless.
            log.err("OSError on DB save: " + str(e))
            return -7

    def whitelist_rebuild(self, refreshall=False, refreshnet=False):
        """Export the local database into the whitelist file itself. If Mojang
            ever changes the format of the server whitelist file, this is the
            function that will need to be updated.
        """
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
            # File does not exist: Pointless to continue.
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
        with open(self.OpFile, "w") as opt:
            json.dump(opFile, opt, indent=2)
        with open(self.WhitelistFile, "w") as wlf:
            json.dump(wlFile, wlf, indent=2)
        return 1


