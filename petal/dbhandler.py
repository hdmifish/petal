# 2017 John Shell
import discord
from datetime import datetime, timezone
from .grasslands import Peacock
log = Peacock()


def m2id(mem):
    """
    Convert member object to id str
    :param mem: discord.Member or id str
    :return: str id
    """
    if isinstance(mem, discord.Member):
        mid = mem.id
    else:
        mid = mem
    return mid


def ts(dt):
    """
    Generate timestamp from datetime object, it's just cleaner
    :param dt: datetime object
    :return: seconds since epoch
    """
    return (dt - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds()


class DBHandler(object):
    """
    Handle connections between leaf and the database. If config.yaml has Databasing turned off, functionality will be solely
    to let the user know it is off.

    """
    def __init__(self, config):
        if config.get("dbconf") is None:
            self.useDB = False
            return

        self.useDB = True
        self.config = config
        db_conf = self.config.get("dbconf")
        from pymongo import MongoClient

        if "remote_uri" in db_conf:
            client = MongoClient(db_conf["remote_uri"])

        else:
            client = MongoClient("localhost", db_conf["port"])
        if "name" not in db_conf:
            self.db = client["petal"]
        else:
            self.db = client[db_conf["name"]]
            self.members = self.db['members']
            self.reminders = self.db['reminders']
            self.motd = self.db['motd']

        log.f("DBHandler", "Database system ready")

    def member_exists(self, member):
        """
        :param member: id of member to look up
        :return: bool member id is in the member collection
        """
        if self.members.find_one({"uid": m2id(member)}) is not None:
            return True
        return False

    def add_member(self, member):
        if self.member_exists(member):
            log.f("DBhandler", "Member already exists in database, use update_member to update them")
            return False
        else:

            data = {"name": member.name,
                    "uid": member.id,
                    "server_date": ts(member.joined_at),
                    "discord_date": ts(member.created_at),
                    "local_date": ts(datetime.utcnow()),
                    "joins": [ts(member.joined_at)],
                    "aliases": [],
                    "servers": [member.server.id],
                    "discriminator": member.discriminator,
                    "isBot": member.bot,
                    "avatar_url": member.avatar_url,
                    "location": "Brisbane, Australia",
                    "osu": "",
                    "subreddit": "aww",
                    "message_count": 0,
                    "last_active": ts(datetime.utcnow()),
                    "last_message": 0,
                    "last_message_channel": '0',
                    "strikes": [],
                    "commands_count": 0}

            if member.display_name != member.name:
                data["aliases"].append(member.display_name)

            pid = self.members.insert_one(data).inserted_id

            log.f("DBhandler", "New member added to DB! (_id: " + str(pid) + ")")
            return True

    def get_member(self, member):
        """
        Retrieves a Dictionary representation of a member
        :param member: discord.Member or str id of member
        :return: dict member
        """
        r = self.members.find_one({"uid": m2id(member)})
        if r is not None:
            return r
        return None

    def update_member(self, member, data=None):
        """
        Updates a the database with keys and values provided in the data field
        :param member: member to update
        :param data: dictionary containing data to update
        :return: str response
        """
        if data is None:
            return "Please provide data first!"

        if not self.member_exists(member):
            self.add_member(member)
        # TODO: get member dict first then query over. Update finally
        for key in data:
            if key in
