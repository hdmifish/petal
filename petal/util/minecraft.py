"""FIXME: INCOMPLETE MODULE FOR MINECRAFT UTILITY REWRITE; DO NOT USE YET

ERROR CODES:
 0: Cmnd success: User added or approved, or request sent
-1: Benign error: Duplicate request which has been approved
-2: Benign error: Duplicate request or approval
-3:
-4:
-5:
-6:
-7: Malign error: Failed to access dbName or WhitelistFile
-8: Malign error: User supplied invalid name
-9: Malign error: Incomplete function (fault of developer)
"""

import json
from pathlib import Path
from uuid import UUID

import requests

from ..grasslands import Peacock
from collections import OrderedDict

log = Peacock()


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


def break_uid(uuid: str) -> str:
    """Given an undashed UUID, break it into five fields."""
    f = [hex(c)[2:] for c in UUID(uuid).fields]
    return "-".join(f[:3] + [f[3] + f[4], f[5]])


def id_from_name(uname_raw: str):
    """Given a Minecraft Username, get its UUID."""
    uname_low: str = uname_raw.lower()
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

    def cget(self, prop: str, default=None):
        v = self.config.get(prop, default)
        return v

    @property
    def path_db(self) -> Path:
        return Path(self.cget("minecraftDB", "playerdb.json"))

    @property
    def path_wl(self) -> Path:
        return Path(self.cget("minecraftWL", "whitelist.json"))

    @property
    def path_op(self) -> Path:
        return Path(self.cget("minecraftOP", "ops.json"))

    def db_read(self):
        try:
            with self.path_db.open("r") as file_db:
                data = json.load(file_db, object_pairs_hook=OrderedDict)
        except OSError as e:
            # File does not exist: Pointless to continue.
            log.err("OSError on DB read: " + str(e))
            return -7
        return data

    def db_write(self, data):
        try:
            with self.path_db.open("w") as file_db:
                # Save all the things.
                json.dump(data, file_db, indent=2)
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
            # Stage 0: Load the full database as ordered dicts, and the
            #   whitelist as dicts.
            strict = self.cget("minecraftStrictWL")
            with self.path_db.open("r") as file_db, self.path_wl.open("r") as file_wl:
                data = json.load(file_db, object_pairs_hook=OrderedDict)
                if strict:
                    data_wl = []
                else:
                    data_wl = json.load(file_wl)
        except OSError:
            # File does not exist: Pointless to continue.
            return 0
        data_op = []  # Op list is always strict.

        if refreshall:
            # Rebuild Index
            data_db = []
            # Stage 1: Make new DB.
            for applicant in data:
                # Stage 2: Find entries in old DB, import their stuff.
                entry_new = PLAYERDEFAULT.copy()
                entry_new.update(applicant)

                if refreshnet:
                    # Stage 3, optional: Rebuild username history.
                    name_history = requests.get(
                        "https://api.mojang.com/user/profiles/{}/names".format(
                            applicant["uuid"].replace("-", "")
                        )
                    )

                    if name_history.status_code == 200:
                        # Spy on their dark and shadowy past.
                        entry_new.update(altname=[])
                        for name in name_history.json():
                            entry_new["altname"].append(name["name"])
                            # Ensure the name is up to date.
                            entry_new["name"] = name["name"]

                data_db.append(entry_new)
            with self.path_db.open("w") as file_db:
                json.dump(data_db, file_db, indent=2)
            data = data_db

        for applicant in data:
            # Check everyone who has applied.
            app = next(
                (item for item in data_wl if item["uuid"] == applicant["uuid"]), False
            )
            # Is the applicant already whitelisted?
            if (
                app == False
                and len(applicant["approved"]) > 0
                and not applicant["suspended"]
            ):
                # Applicant is not whitelisted AND is approved AND is not
                #   suspended, add them.
                data_wl.append({"uuid": applicant["uuid"], "name": applicant["name"]})
            elif app != False and applicant["suspended"] and app in data_wl:
                # BadPersonAlert, remove them.
                data_wl.remove(app)

            # Is the applicant supposed to be an op?
            level = applicant.get("operator", 0)
            applicant["operator"] = level
            if level > 0:
                data_op.append(
                    {
                        "uuid": applicant["uuid"],
                        "name": applicant["name"],
                        "level": level,
                        "bypassesPlayerLimit": False,
                    }
                )

        log.f("wl+", "Refreshing Whitelist")
        with self.path_op.open("w") as file_op:
            json.dump(data_op, file_op, indent=2)
        with self.path_wl.open("w") as file_wl:
            json.dump(data_wl, file_wl, indent=2)
        return 1


