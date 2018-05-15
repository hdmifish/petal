# 2017 John Shell
import discord
from datetime import datetime, timezone
from random import randint as rand
import pytz

from .grasslands import Peacock
log = Peacock()


def m2id(mem):
    """
    Convert member object to id str
    :param mem: discord.Member or id str
    :return: str id
    """
    if isinstance(mem, discord.Member) or isinstance(mem, discord.User):
        mid = mem.id
    elif isinstance(mem, discord.Channel) or isinstance(mem, discord.Server):
        print(mem.name)
        mid = None
    else:
        mid = mem
    return mid


def ts(dt):
    """
    Generate timestamp from datetime object, it's just cleaner
    :param dt: datetime object
    :return: seconds since epoch
    """
    if not isinstance(dt, datetime):
        return dt
    try:
        dt = dt.replace(tzinfo=pytz.utc)
        return (dt - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds()
    except TypeError:
        return dt


class DBHandler(object):
    """
    Handle connections between leaf and the database. If config.yml has
    Databasing turned off, functionality will be solely
    to let the user know it is off.

    """
    def __init__(self, config):
        if config.get("dbconf") is None:
            log.f("DBHandler", "Could not find database config entry "
                               "in config.yml. "
                               "Certain features will be disabled")
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
        self.void = self.db["void"]
        self.ac = self.db["ac"]
        self.subs = self.db["subs"]

        log.f("DBHandler", "Database system ready")

    def member_exists(self, member):
        """
        :param member: id of member to look up
        :return: bool member id is in the member collection
        """
        if not self.useDB:
            return False
        if self.members.find_one({"uid": m2id(member)}) is not None:
            return True
        return False

    def add_member(self, member, verbose=False):
        if not self.useDB:
            return False
        if self.member_exists(member):
            if verbose:
                log.f("DBhandler", "Member already exists in database, "
                                   "use update_member to update them")
            return False

        else:

            data = {"name": member.name,
                    "uid": member.id,
                    "discord_date": ts(member.created_at),
                    "local_date": ts(datetime.utcnow()),
                    "aliases": [],
                    "servers": [member.server.id],
                    "discriminator": member.discriminator,
                    "isBot": member.bot,
                    "avatar_url": member.avatar_url,
                    "location": "Brisbane, Australia",
                    "osu": "",
                    "banned": False,
                    "subreddit": "aww",
                    "message_count": 0,
                    "last_active": ts(datetime.utcnow()),
                    "last_message": 0,
                    "last_message_channel": '0',
                    "strikes": [],
                    "subscriptions": [],
                    "commands_count": 0}
            if isinstance(member, discord.Member):
                data["server_date"] = ts(member.joined_at)
                data["joins"] =  [ ts(member.joined_at) ]
            if member.display_name != member.name:
                data["aliases"].append(member.display_name)

            pid = self.members.insert_one(data).inserted_id
            if verbose:
                log.f("DBhandler", "New member added to DB! (_id: " + str(pid) + ")")
            return True

    def get_member(self, member):
        """
        Retrieves a Dictionary representation of a member
        :param member: discord.Member or str id of member
        :return: dict member
        """
        if not self.useDB:
            return False
        r = self.members.find_one({"uid": m2id(member)})
        if r is not None:
            return r
        return None

    def get_attribute(self, member, key, verbose=True):
        """
        Retrieves a specific field from a stored member object
        :param member: discord.Member or str id of member
        :param key: field to return
        :param verbose:
        :return: member[key] or None if none
        """
        if not self.useDB:
            return False
        mem = self.get_member(member)
        if mem is None:
            if verbose:
                log.f("DBHandler",   member.name + m2id(member) + " not found in db")
            return None

        if key in mem:
            return mem[key]
        else:
            if verbose:
                log.f("DBHandler", m2id(member) + " has no field: " + key)
            return None

    def update_member(self, member, data=None, type=0):
        """
        Updates a the database with keys and values provided in the data field

        :param member: member to update
        :param data: dictionary containing data to update
        :param type: 0 = None, 1 = Message, 2 = Command
        :return: str response
        """
        if not self.useDB:
            return False

        if data is None:
            log.f("DBhandler", "Please provide data first!")
            return False
        if not self.member_exists(member):
            self.add_member(member)

        mem = self.get_member(member)
        if mem is None:
            log.f("DBhandler", "Member doesn't exist")
            return False

        # TODO: get member dict first then query over. Update finally
        count = 0

        for key in data:
            if isinstance(data[key], dict):
                print(str(key) + "\n" + str(data) + "\n")
                mem[key] = data[key]
                print(str(mem[key]))
                for vk in mem[key]:
                    mem[key][vk] = ts(mem[key][vk])

            elif key in mem:
                if isinstance(mem[key], list):
                    if isinstance(data[key], list):
                        for item in data[key]:
                            # log.f("DBHandler", "Item: " + item)
                            if item not in mem[key]:
                               #  log.f("DBHandler", "ON key: " + key + " added " + item + " to " + str(mem[key]))
                                mem[key].append(item)
                                count += 1
                    else:
                        if data[key] not in mem[key]:
                            mem[key].append(data[key])
                            log.f("DBHandler", "added " + data[key] + " to " + key )
                            count += 1

                else:
                    # log.f("DBHandler", "replace key: " + key + " -> "
                    #  + str(mem[key]) + " with "
                    #      + str(data[key]))
                    # log.f("Replaced " + key + ": " + str(mem[key]) + " -> " + str(ts(data[key])))
                    mem[key] = ts(data[key])



            else:
                # log.f("Added " + key)
                mem[key] = ts(data[key])
                count += 1

        if type == 1:
            mem["message_count"] += 1
        elif type == 2:
            mem["commands_count"] += 1

        if count > 0:
            log.f("DBHandler", "Added "  + str(count) + " fields to "
                  + mem["name"])

        self.members.replace_one({"uid": m2id(member)}, mem, upsert=False)

        return True

    def get_void(self):
        void_size = self.void.count()
        if void_size == 0:
            return "Nothing in void storage"

        response = None
        while response is None:
            index = rand(0, void_size - 1)
            response = self.void.find_one({"number": index})

        return response

    def save_void(self, content, name, id):
        if self.void.count({"content" : content}) > 0:
            return None

        self.void.insert({"content": content, "number": self.void.count(), "author": name + " " + id})
        return self.void.count()

    def delete_void(self, number):
        return self.void.delete_one({"number": number})

    def get_reminders(self, timestamp):
        timestamp = ts(timestamp)
        return self.reminders.find({"ts": {"$lr": timestamp}})

    def add_reminder(self, author, content, timestamp):
        timestamp = ts(timestamp)
        return self.reminders.insert_one({"ts": timestamp, "author": author.id, "content": content})

    def get_motd_entry(self, update=False):
        response = self.motd.find_one({"used": False, "approved": True})
        if response is None:
            return None
        if not update:
            return response
        self.motd.update({'_id': response['_id']}, {'$set': {"used": True}},  upsert=False, multi=False)
        return response

    def get_motd_max(self):
        return self.motd.find_one(sort=[("num", -1)])

    def submit_motd(self, author, content):
        num = self.get_motd_max()

        if num is None:
            num = 2000
        else:
            num = num["num"] + 1
        object = {"author": author,
                  "num": num,
                  "content": content,
                  "approved": False,
                  "used": False}
        # print(str(object))
        return self.motd.find_one({"_id": self.motd.insert_one(object).inserted_id})


    def update_motd(self, num, approve=True):
        if approve:
            self.motd.update_one({"num": num},{"$set" : {"approved": True, "used": False}}, upsert=False)
        else:
            self.motd.update_one({"num": num},
                                 {"$set": {"approved": False, "used": False}},
                                 upsert=False)

        return self.motd.find_one({"num": num})
