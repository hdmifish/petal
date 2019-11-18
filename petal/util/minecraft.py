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

from contextlib import contextmanager
from datetime import datetime as dt
import json
from pathlib import Path
from typing import Dict, Iterator, List, Type, Union, Tuple
from uuid import UUID

from discord import Embed
import requests

from ..exceptions import WhitelistError
from ..grasslands import Peacock
from .fmt import bold, escape, italic, mono, underline, userline
from petal.config import cfg
from petal.types import PetalClientABC

log = Peacock()


type_entry_db: Type = Dict[str, Union[bool, int, List[int], List[str], str]]
type_db: Type = List[type_entry_db]


# The default profile for a new player being added to the database.
# (Do not use this for other stuff)
PLAYERDEFAULT: type_entry_db = {
    "name": "PLAYERNAME",
    "uuid": "00000000-0000-0000-0000-000000000000",
    "altname": [],
    "discord": 000000000000000000,
    "approved": [],
    "submitted": "1970-01-01_00:00",
    "suspended": 000,
    "operator": 0,
    "notes": [],
}


minecraft_suspension = {
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
APPROVE: str = underline(mono("--- APPROVED ---"))
PENDING: str = italic(mono("-#- PENDING -#-"))
SUSPEND: str = bold(mono("#!# SUSPENDED #!#"))


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


def find(data: type_db, *params: str) -> Iterator[type_entry_db]:
    return (
        entry
        for entry in data
        if any(  # Yield each Entry if any parameter...
            (
                # ...Matches the Discord UUID.
                p == str(entry.get("discord"))
                # ...Matches the Mojang UUID.
                or p.lower().replace("-", "") == entry["uuid"].lower().replace("-", "")
                # ...Can be found in the Username History.
                or p.lower() in map(str.lower, entry["altname"])
            )
            for p in params
        )
    )


def id_from_name(name: str):
    """Given a Minecraft Username, get its UUID."""
    response = requests.get(
        f"https://api.mojang.com/users/profiles/minecraft/{name.lower()}"
    )
    log.f("WLME_RESP", str(response))

    if response.ok:
        return response.json()
    else:
        response.raise_for_status()


def make_lists(data: type_db, refresh: bool = False) -> Tuple[type_db, type_db]:
    wl: type_db = []
    op: type_db = []

    if refresh:
        data[:] = [refresh_entry(entry) for entry in data]

    for entry in data:
        if entry["approved"] and not entry["suspended"]:
            wl.append({"uuid": entry["uuid"], "name": entry["name"]})

        if entry["operator"] > 0:
            op.append(
                {
                    "uuid": entry["uuid"],
                    "name": entry["name"],
                    "level": entry["operator"],
                    "bypassesPlayerLimit": False,
                }
            )

    return wl, op


def new_entry(
    uuid_discord: str, *, uuid_mc: str = None, name_mc: str = None
) -> type_entry_db:
    if uuid_mc is None and name_mc is None:
        raise TypeError("Entry requires either Username or UUID.")
    elif uuid_mc is None:
        # print(id_from_name(name_mc))
        _d = id_from_name(name_mc)
        uuid_mc = _d["id"]

    new = PLAYERDEFAULT.copy()
    hist = requests.get(f"https://api.mojang.com/user/profiles/{uuid_mc}/names")

    if hist.ok:
        new["altname"] = [e["name"] for e in hist.json()]
        new["name"] = new["altname"][-1]
    else:
        hist.raise_for_status()

    new["uuid"] = uuid_mc
    new["discord"] = str(uuid_discord)
    new["submitted"] = dt.utcnow().strftime("%Y-%m-%d_%0H:%M")

    return new


def refresh_entry(old: type_entry_db) -> type_entry_db:
    try:
        new = new_entry(old["discord"], uuid_mc=old["uuid"])
        new["approved"] = old["approved"]
        new["submitted"] = old["submitted"]
        new["suspended"] = old["suspended"]
        new["operator"] = old["operator"]
        new["notes"] = old["notes"]
        return new
    except:
        return old


class Interface:
    def __init__(self, client: PetalClientABC):
        self.client: PetalClientABC = client

    @property
    def path_db(self) -> Path:
        return Path(cfg.get("minecraftDB", "playerdb.json"))

    @property
    def path_wl(self) -> Path:
        return Path(cfg.get("minecraftWL", "whitelist.json"))

    @property
    def path_op(self) -> Path:
        return Path(cfg.get("minecraftOP", "ops.json"))

    def db_read(self) -> type_db:
        try:
            with self.path_db.open("r") as file_db:
                data: type_db = json.load(file_db)

        except OSError as e:
            # File does not exist: Pointless to continue.
            log.err(f"OSError on DB read: {e}")
            raise WhitelistError("Cannot read PlayerDB file.") from e

        return data

    def db_write(self, data: type_db):
        try:
            with self.path_db.open("w") as fd:
                # Save all the things.
                json.dump(data, fd, indent=2)

        except OSError as e:
            # Cannot write file: Well this was all rather pointless.
            log.err(f"OSError on DB save: {e}")
            raise WhitelistError("Cannot write PlayerDB file.") from e

    def export(self, data: type_db):
        wl, op = make_lists(data)

        try:
            with self.path_wl.open("w") as fd:
                json.dump(wl, fd, indent=2)

        except OSError as e:
            log.err(f"OSError on WL save: {e}")
            raise WhitelistError("Cannot write Whitelist file.") from e

        try:
            with self.path_op.open("w") as fd:
                json.dump(op, fd, indent=2)

        except OSError as e:
            log.err(f"OSError on OP save: {e}")
            raise WhitelistError("Cannot write Operators file.") from e

    def whitelist_rebuild(self, refreshall=False, refreshnet=False) -> int:
        """Export the local database into the whitelist file itself. If Mojang
            ever changes the format of the server whitelist file, this is the
            function that will need to be updated.
        """
        try:
            # Stage 0: Load the full database as ordered dicts, and the
            #   whitelist as dicts.
            with self.path_db.open("r") as file_db, self.path_wl.open("r") as file_wl:
                data = json.load(file_db)
                if cfg.get("minecraftStrictWL", False):
                    data_wl = []
                else:
                    data_wl = json.load(file_wl)
        except OSError:
            # File does not exist: Pointless to continue.
            return 0
        data_op: type_db = []  # Op list is always strict.

        if refreshall:
            # Rebuild Index
            data_db: type_db = []
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
    def __init__(self, client: PetalClientABC):
        self.client: PetalClientABC = client
        self.interface = Interface(self.client)

        self._ctxs: int = 0
        self._db = None

    def card(
        self,
        profile: Dict[str, Union[int, str, List[int], List[str]]],
        verbose: bool = False,
        title: str = "Minecraft User",
    ) -> Embed:
        suspended: int = profile.get("suspended", 0)
        approved: List[int] = profile.get("approved", [])

        if suspended:
            col = 0x_AA_22_00
            status = f"{SUSPEND}\n{minecraft_suspension.get(suspended, 'Unknown Code')}"
        elif approved:
            col = 0x_00_CC_00
            status = "\n".join((APPROVE, *(f"<@{i}>" for i in approved)))
        else:
            col = 0x_CC_AA_00
            status = PENDING

        uuid_discord = profile.get("discord")
        user = self.client.get_user(int(uuid_discord)) if uuid_discord else None

        em = (
            Embed(
                title=title,
                description=f"Minecraft Username: {escape(repr(profile.get('name')))}"
                f"\nMinecraft UUID: `{profile.get('uuid')}`"
                f"\nDiscord Identity: `{escape(userline(user) if user else uuid_discord)}`"
                f"\nDiscord Tag: <@{uuid_discord}>",
                colour=col,
            )
            .add_field(name="Application Status", value=status, inline=False)
            .add_field(name="Timestamp", value=profile.get("submitted"))
            .add_field(name="Op Level", value=profile.get("operator", 0))
        )
        if verbose:
            em.add_field(
                name="Username History",
                value="\n".join(
                    f"- {escape(name)}" for name in profile.get("altname", [])
                ),
                inline=False,
            )
            if profile.get("notes", []):
                em.add_field(
                    name="User Notes", value="\n".join(profile["notes"]), inline=False
                )

        return em

    def add_entries(self, *entries: type_entry_db):
        with self.db() as db:
            db.extend(entries)

    def export(self):
        with self.db() as db:
            self.interface.export(db)

    def rebuild(self):
        with self.db() as db:
            db[:] = [refresh_entry(e) for e in db]
            # self.interface.db_write(self._db)

    def user_has_op(self, user, op: int) -> bool:
        with self.db(str(user.id)) as db:
            allow = any(e["operator"] >= op for e in db)
        return allow

    @contextmanager
    def db(self, *params: str) -> type_db:
        """Context Manager: Yield the Users Database, potentially filtered. Data
            within the yielded List is mutable, and changes made to Entries will
            be saved to the File after the Context Manager closes.

        If no Parameters were provided, the initially-yielded List will be what
            is written to the File, and can thus be used to add new Entries.
        """
        self._ctxs += 1
        try:
            if self._db is None:
                self._db = self.interface.db_read()

            if params:
                yield find(self._db, *params)
            else:
                yield self._db

        finally:
            self._ctxs -= 1
            self.interface.db_write(self._db)

            if self._ctxs < 1:
                self._db = None
