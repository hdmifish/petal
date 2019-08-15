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

from collections import OrderedDict
import json
from pathlib import Path
from typing import Any, Dict, List, NewType, Type, Union
from uuid import UUID

import requests

from .embeds import minecraft_card, minecraft_suspension
from ..exceptions import WhitelistError
from ..grasslands import Peacock

log = Peacock()


type_entry_db: Type = NewType("DB Entry", Dict[str, Union[bool, int, List[str], str]])
type_db: Type = NewType("Database", List[type_entry_db])


# The default profile for a new player being added to the database
# (Do not use this for other stuff)
PLAYERDEFAULT: type_entry_db = OrderedDict(
    [
        ("name", "PLAYERNAME"),
        ("uuid", "00000000-0000-0000-0000-000000000000"),
        ("altname", []),
        ("discord", 000000000000000000),
        ("approved", []),
        ("submitted", "1970-01-01_00:00"),
        ("suspended", 000),
        ("operator", 0),
        ("notes", []),
    ]
)


def break_uid(uuid: str) -> str:
    """Given an undashed UUID, break it into five fields."""
    f = [hex(c)[2:] for c in UUID(uuid).fields]
    return "-".join(f[:3] + [f[3] + f[4], f[5]])


# TODO: Implement
# if (  # Yield each Entry if looking for something specific.
#     (pending is None or pending is bool(entry.get("approved", [])))
#     and (
#         suspended is None
#         or (
#             suspended is True
#             and entry.get("suspended", 0) not in (0, False, None)
#         )
#         or suspended is entry.get("suspended", False)
#     )
# ) or


def find(data: type_db, *params: str) -> List[type_entry_db]:
    out = []
    for entry in data:
        for p in params:
            if (  # Yield each Entry if any parameter...
                # ...Matches the Discord UUID.
                p == str(entry.get("discord"))
                # ...Matches the Mojang UUID.
                or p.lower().replace("-", "") == entry["uuid"].lower().replace("-", "")
                # ...Can be found in the Username History.
                or p.lower() in map(str.lower, entry["altname"])
            ):
                out.append(entry)
                break
    return out


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
        self.ctx = None

    def __enter__(self) -> type_db:
        if self.ctx is not None:
            raise RuntimeError("Attempting to lock locked Whitelist.")
        else:
            data: type_db = self.db_read()
            self.ctx = data
            return data

    def __exit__(self, exc_type, exc_value, traceback):
        if self.ctx is None:
            raise RuntimeError("Attempting to unlock unlocked Whitelist.")
        else:
            self.db_write(self.ctx)
            self.ctx = None

    def cget(self, prop: str, default: Any = None) -> Any:
        """Retrieve a value from the Configuration. Merely a shorthand."""
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

    def db_read(self) -> type_db:
        try:
            with self.path_db.open("r") as file_db:
                data: type_db = json.load(file_db, object_pairs_hook=OrderedDict)

        except OSError as e:
            # File does not exist: Pointless to continue.
            log.err("OSError on DB read: " + str(e))
            raise WhitelistError("Cannot read PlayerDB file.") from e

        return data

    def db_write(self, data):
        try:
            with self.path_db.open("w") as file_db:
                # Save all the things.
                json.dump(data, file_db, indent=2)

        except OSError as e:
            # Cannot write file: Well this was all rather pointless.
            log.err("OSError on DB save: " + str(e))
            raise WhitelistError("Cannot write PlayerDB file.") from e

    def whitelist_rebuild(self, refreshall=False, refreshnet=False) -> int:
        """Export the local database into the whitelist file itself. If Mojang
            ever changes the format of the server whitelist file, this is the
            function that will need to be updated.
        """
        try:
            # Stage 0: Load the full database as ordered dicts, and the
            #   whitelist as dicts.
            with self.path_db.open("r") as file_db, self.path_wl.open("r") as file_wl:
                data = json.load(file_db, object_pairs_hook=OrderedDict)
                if self.cget("minecraftStrictWL", False):
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


class Minecraft(object):
    def __init__(self, client):
        self.client = client
        self.config = client.config
        self.interface = Interface(client)

    def add_entry(self, entry: type_entry_db):
        raise NotImplementedError

    def get_entry(self, ident: str) -> List[type_entry_db]:
        raise NotImplementedError

    def edit(self, ident: str):
        """Yield a search for Entries. Then pause with the Interface open, and
            wait until the Generator is resumed. Immediately after resume, the
            Interface will close, writing changes to the file.
        """
        with self.interface as file:
            target = find(file, ident)
            yield target
