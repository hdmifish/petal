import asyncio
import json

import discord
import random
# import urllib.request as urllib2
# import re


import os
import praw
import requests
import twitter
import facebook
import pytumblr
# import _mysql (deprecated in favor of the python package)

# FIXME: replace pymysql with mongo functionality
import pymysql
import time
# from cleverbot import Cleverbot
import petal
from datetime import datetime, timedelta
from .grasslands import Octopus
from .grasslands import Giraffe
from .grasslands import Peacock
from .grasslands import Pidgeon
from .dbhandler import DBHandler
from random import randint
version = "0.3.5(Experimental)"



class Commands:

    """
    Pretty cool thing with which to store commands
    """

    def __init__(self, client):

        self.client = client
        self.config = client.config
        self.db = client.db
        # self.cb = Cleverbot('discordBot-petal')
        self.log = Peacock()
        self.startup = datetime.utcnow()
        self.activeHelpers = []
        self.activeSads = []
        self.log.info("Command module init start")
        self.supportdict = {}
        self.osuKey = self.config.get("osu")
        if self.osuKey is not None:
            self.o = Octopus(self.osuKey)
        else:
            self.log.warn("No OSU! key found.")

        self.imgurKey = self.config.get("imgur")
        if self.imgurKey is not None:
            self.i = Giraffe(self.imgurKey)
        else:
            self.log.warn("No imgur key found.")
        if self.config.get("reddit") is not None:
            reddit = self.config.get("reddit")
            self.r = praw.Reddit(client_id=reddit["clientID"],
                                 client_secret=reddit["clientSecret"],
                                 user_agent=reddit["userAgent"],
                                 username=reddit["username"],
                                 password=reddit["password"])
            if self.r.read_only:
                self.log.warn("This account is in read only mode. " +
                              "You may have done something wrong. " +
                              "This will disable reddit functionality.")
                self.r = None
                return
        else:
            self.log.warn("No reddit keys found")

        if self.config.get("twitter") is not None:
            tweet = self.config.get("twitter")
            self.t = twitter.Api(consumer_key=tweet["consumerKey"],
                                 consumer_secret=tweet["consumerSecret"],
                                 access_token_key=tweet["accessToken"],
                                 access_token_secret=tweet["accessTokenSecret"]
                                 )
            # tweet test
            if "id" not in str(self.t.VerifyCredentials()):
                self.log.warn("Your twitter authentication is invalid, " +
                              " twitter posting will not work")
                self.t = None
                return
        else:
            self.log.warn("No twitter keys found.")

        if self.config.get("facebook") is not None:
            fb = self.config.get("facebook")
            self.fb = facebook.GraphAPI(access_token=fb["graphAPIAccessToken"],
                                        version=fb["version"])

        if self.config.get("tumblr") is not None:
            tumble = self.config.get("tumblr")
            self.tb = pytumblr.TumblrRestClient(tumble["consumerKey"],
                                                tumble["consumerSecret"],
                                                tumble["oauthToken"],
                                                tumble["oauthTokenSecret"])
        else:
            self.log.warn("No tumblr keys found.")

    def level0(self, author):
        # this supercedes all other levels so, use it carefully
        return author.id == str(self.config.owner)

    def level1(self, author):
        return author.id in self.config.l1 or self.level0(author)

    def level2(self, author):
        return author.id in self.config.l2 or self.level1(author)

    def level3(self, author):
        return author.id in self.config.l3 or self.level2(author)

    def level4(self, author):
        return author.id in self.config.l4 or self.level3(author)

    def getlevel(self, author):
        count = 0
        if self.level0(author):
            return 0
        for l in self.config.get("level"):
            count += 1
            if author.id in self.config.get("level")[l]:
                return count
        return 5

    def check(self, message):
        return message.content.lower() == 'yes'

    def cleanInput(self, input):
        args = input[len(input.split()[0]):].split('|')
        newargs = []
        for i in args:
            newargs.append(i.strip())
        return newargs

    def yesNoCheck(self, message):
        if message.content.lower().strip() in ["yes", "no"]:
            return True
        return False

    def isNumeric(self, message):
        try:
            int(message.content)
        except ValueError:
            return False
        else:
            return True

    def getUptime(self):
        delta = datetime.utcnow() - self.startup
        delta = delta.total_seconds()

        d = divmod(delta,86400)  # days
        h = divmod(d[1],3600)  # hours
        m = divmod(h[1],60)  # minutes
        s = m[1]  # seconds

        return '%d days, %d hours, %d minutes, %d seconds' % (d[0],h[0],m[0],s)

    def validateChan(self, chanlist, msg):
        for i in range(len(msg.content)):
            try:
                print(msg.content[i])
                chanlist[int(msg.content[int(i)])]
            except:
                return False
        return True

    def hasRole(self, user, role):
        target = discord.utils.get(user.server.roles, name=role)
        if target is None:
            self.log.err(role + " does not exist")
            return False
        else:
            if target in user.roles:
                return True
            else:
                return False

    def removePrefix(self, input):
        return input[len(input.split()[0]):]

    def getMember(self, message, member):
        return discord.utils.get(message.server.members,
                                 id=member.lstrip("<@!").rstrip('>'))

    def anonCheck(self, msg):
        if msg.author == self.client.user:
            return False
        elif msg.channel.id == self.hc.id or msg.channel.id == self.sc.id:
            return True
        else:
            return False

    def getSubscriptionKey(self, post):
        # EVENTS SCHEMA
        # 2 Tables:
        # CREATE TABLE subKeys(code VARCHAR(20), friendly VARCHAR(20));
        # CREATE TABLE users(name VARCHAR(20), id VARCHAR(20),
        #                    code VARCHAR(20));
        try:
            conn = pymysql.connect(self.config.get("mysql")["hostname"],
                                   self.config.get("mysql")["username"],
                                   self.config.get("mysql")["password"],
                                   self.config.get("mysql")["eventdatabase"])
        except Exception as e :
            self.log.err("SQL Error, " + str(e))
            return None, None
        else:
            cursor = conn.cursor()
        find_entry = ("SELECT * FROM subKeys")
        cursor.execute(find_entry)
        data = cursor.fetchall()

        if len(data) == 0:
            self.log.f("event", "Database is empty for keys!" +
                                " Skipping further validation")
            return None, None
        postdata = post.lower().split()

        for row in data:
            for i in row[1].split():
                if i.lower() in postdata:
                    return row[0] , row[1]
        conn.close()
        self.log.f("event", "could not find sub key in post")
        return None, None


    async def checkservers(self, message):
        """
        hello
        """
        if not self.level0(message.author):
            return
        for s in self.client.servers:
            await self.client.send_message(message.channel, s.name + " " + s.id, )



#    async def killthenonconformist(self, message):
 #       """
  #      hello
   #     """
    #    for s in self.client.servers:
     #        if s.id == "215170877002612737":
      #           await self.client.leave_server(s)
       #          return "left " + s.name

    # AskPatch is designed for discord.gg/patchgaming but you may edit it
    # for your own personal uses if you like
    # the database fields are:
    # Single table:
    # varchar(20) author, vc(20) id, TIMESTAMP time, TEXT content, BOOL used,
    # INT(11)PK entryid, BOOL approved
    async def notifySubs(self, message, key):
            return

    async def checkUpdate(self, force=False):
            if force:
                self.config.doc["lastRun"] = datetime.utcnow()
                self.config.save()

            else:
                lastRun = self.config.get("lastRun")
                self.log.f("pa", "Last run at: " + str(lastRun))
                if lastRun is None:
                    lastRun = datetime.utcnow()
                    self.config.doc["lastRun"] = lastRun
                    self.config.save()
                else:
                    difference = (datetime.utcnow() - datetime.strptime(str(lastRun), '%Y-%m-%d %H:%M:%S.%f')).total_seconds()
                    self.log.f("pa", "Difference: " + str(difference))
                    if difference < 86400:
                        return
                    else:
                        self.config.doc["lastRun"] = datetime.utcnow()
                        self.config.save()


            self.log.f("pa", "Searching for entries...")

            conn = pymysql.connect(self.config.get("mysql")["hostname"],
                                   self.config.get("mysql")["username"],
                                   self.config.get("mysql")["password"],
                                   self.config.get("mysql")["padatabase"])
            cursor = conn.cursor()
            find_entry = ("SELECT entryid, author, content, used, approved " +
                          "FROM questions WHERE approved = 1 AND used = 0")

            cursor.execute(find_entry)
            data = cursor.fetchall()

            if len(data) == 0:
                self.log.f("pa", "Could not find suitable entry")
            else:
                askrow = data[random.randint(0, len(data) - 1)]
                em = discord.Embed(title="Patch Asks",
                                   description="Today Patch asks: \n "
                                   + askrow[2],
                                   colour=0x0acdff)

                msg = await self.client.embed(self.client.get_channel(
                                              self.config.get
                                              ("mysql")["channelid"]), em)
                await self.client.send_message(msg.channel, "*today's patch asks was " +
                                               "written by " + askrow[1]
                                               .strip() + "*", )
                self.log.f("pa", "Going with entry: " + str(askrow[0]) + " by "
                                 + askrow[1].strip())
                try:
                    mark_entry = ("UPDATE questions SET used = 1 WHERE " +
                                  "entryid={}".format(askrow[0]))
                    cursor.execute(mark_entry)
                    conn.commit()
                except:
                    self.log.err("An SQL error occurred")
                    conn.rollback()
                finally:
                    conn.close()

    async def parseCustom(self, command, message):
        invoker = command.split()[0]
        if len(command.split()) > 1:
            tags = self.getMember(message, command.split()[1].strip()).mention
        else:
            tags = "<poof>"
        com = self.config.commands[invoker]
        response = com["com"]
        # perms = com["perm"]

        try:
            output = response.format(self=message.author.name,
                                     myID=message.author.id,
                                     tag=tags)
        except KeyError:
            return "Error translating custom command"
        else:
            return output

    # ------------------------------------------
    # START COMMAND LIST (ILL ORGANIZE IT later)
    # ------------------------------------------
    # You may write your own commands here by using the command as the
    # function name. Return is an optional final output (must be string)

    async def hello(self, message):
        """
        This is a test, its a test
        """
        if self.level0(message.author):
            return "Hello boss! How's it going?"
        else:
            return "Hey there!"

    async def choose(self, message):
        """
        Chooses a random option from a list, separated by |
        Syntax: `>choose foo | bar`
        """
        args = self.cleanInput(message.content)
        response = ("From what you gave me, I believe `{}` " +
                    "is the best choice".format(args[random.randint(0,
                                                len(args) - 1)]))
        return response

    async def cleverbot(self, message):
        """
        Sends your message to cleverbot
        Syntax: `>(your message)`
        """
        return self.cb.ask(self.removePrefix(message.content))

    async def osu(self, message):
        """
        Gets information for an osu player
        Syntax: `>osu (optional: username)`
        """
        try:
            self.o
        except AttributeError:
            return "Osu Support is disabled by administrator"
        uid = self.removePrefix(message.content)
        user = message.author.name
        if uid.strip() == "":
            if self.db.useDB:
                m = self.db.get_attribute(message.author, "osu")
                if m is None:
                    m = ""
                if m != "":
                    user = m

            user = self.o.get_user(user)

            if user is None:
                return ("Looks like there is no osu data associated with" +
                        " your discord name")
        else:
            user = self.o.get_user(uid.split('|')[0])
            if user is None:
                return "No user found with Osu! name: " + uid.split('|')[0]

        em = discord.Embed(title=user.name,
                           description="https://osu.ppy.sh/u/{}"
                           .format(user.id),
                           colour=0x0acdff)

        em.set_author(name="Osu Data", icon_url=self.client.user.avatar_url)
        em.set_thumbnail(url="http://a.ppy.sh/" + user.id)
        em.add_field(name="Maps Played",
                     value="{:,}".format(int(user.playcount)))
        em.add_field(name="Total Score",
                     value="{:,}".format(int(user.total_score)))
        em.add_field(name="Level",
                     value=round(float(user.level), 2), inline=False)
        em.add_field(name="Accuracy",
                     value=round(float(user.accuracy), 2))
        em.add_field(name="PP Rank",
                     value="{:,}".format(int(user.rank)), inline=False)
        em.add_field(name="Local Rank ({})".format(user.country),
                     value="{:,}".format(int(user.country_rank)))
        await self.client.embed(message.channel, embedded=em)
        return None

    async def new(self, message):
        """
        That awesome custom command command.
        >new <name of command> | <output of command>
        """
        if not self.level4(message.author):
            return
        if len(self.removePrefix(message.content).split('|')) < 2:
            return "This command needs at least 2 arguments"

        invoker = self.removePrefix(message.content).split('|')[0].strip()
        command = self.removePrefix(message.content).split('|')[1].strip()

        if len(self.removePrefix(message.content).split('|')) > 3:
            perms = self.removePrefix(message.content).split('|')[2].strip()
        else:
            perms = '0'

        if invoker in self.config.commands:
            await self.client.send_message(message.channel, "This command already exists, " +
                                           "type 'yes' to rewrite it", )
            response = (await self.client.
                        wait_for_message(timeout=15,
                                         author=message.author,
                                         channel=message.channel))

            if response is None or not self.check(response):
                return "Command: `" + invoker + "` was not changed."
            else:
                self.config.commands[invoker] = {"com": command, "perm": perms}
                self.config.save()
                return "Command: `" + invoker + "` was redefined"
        else:
            self.config.commands[invoker] = {"com": command, "perm": perms}
            self.config.save()
            return "New Command `{}` Created!".format(invoker)


    async def help(self, message):
        """
        Congrats, You did it!
        """
        func = self.cleanInput(message.content)[0]
        if func == "":
            em = discord.Embed(title="Help",
                               description="Petal Info and Help",
                               colour=0x0acdff)
            em.set_author(name="Petal Help Provider",
                          icon_url=self.client.user.avatar_url)

            em.set_thumbnail(url=message.author.avatar_url)
            em.add_field(name="Version", value=version)
            em.add_field(name="Command List", value=self.config.prefix +
                         "commands")
            em.add_field(name="Author", value="isometricramen")
            em.add_field(name="Help Syntax", value=self.config.prefix +
                         "help <command name>")
            url = "http://leaf.drunkencode.net/"
            await self.client.embed(message.channel, em)
            await self.client.send_message(message.channel, "Publicly available at: " + url +
                                           "\n\nMore Info with: " + self.config.prefix +
                                           "statsfornerds", )
            return
        if func in dir(self):
            if getattr(self, func).__doc__ is None:
                return "No help info for function: " + func
            else:
                helptext = getattr(self, func).__doc__.split("\n")
                em = discord.Embed(title=func, description=helptext[1],
                                   colour=0x0acdff)

                em.set_author(name="Petal Help",
                              icon_url=self.client.user.avatar_url)

                em.set_thumbnail(url=self.client.user.avatar_url)
                em.add_field(name="Syntax", value=helptext[2])
                await self.client.embed(message.channel, em)
        else:
            try:
                dir(self.config.aliases[func])
            except KeyError:
                return func + " is not a valid command"
            else:
                pass

            if getattr(self, self.config.aliases[func]).__doc__ is None:
                return "No help for function: " + func
            else:
                helptext = getattr(self, (self.config.aliases[func]).
                                   __doc__.split("\n"))
                em = discord.Embed(title=func, description=helptext[1],
                                   colour=0x0acdff)
                em.set_author(name="Petal Help",
                              icon_url=self.client.user.avatar_url)
                em.set_thumbnail(url=self.client.user.avatar_url)
                em.add_field(name="Syntax", value=helptext[2])
                await self.client.embed(message.channel, em)
                return ("__**Help Information For {}**__:\n{}"
                        .format(func,
                                getattr(self,
                                        self.config.aliases[func]).__doc__))

    async def freehug(self, message):
        """
        Requests a freehug from a hug donor
        `freehug add | foo` - adds user to donor list
        'freehug del | foo' - removes user from donor list
        'freehug donate' - toggles your donor status, your request counter will reset if you un-donate
        'freehug status' - If you're a donor, see how many requests you have recieved
        'freehug' - requests a hug
        """
        args = self.cleanInput(message.content)

        if args[0] == '':
            valid = []
            for m in self.config.hugDonors:
                user = self.getMember(message, m)
                if user is not None:
                    if (user.status == discord.Status.online
                       and user != message.author):
                        valid.append(user)

            if len(valid) == 0:
                return "Sorry, no valid hug donors are online right now"

            pick = valid[random.randint(0, len(valid) - 1)]

            try:
                await self.client.send_message(pick, "Hello there. " +
                                               "This message is to inform " +
                                               "you that " +
                                               message.author.name +
                                               " has requested a hug from you", )
            except discord.ClientException:
                return ("Your hug donor was going to be: " + pick.mention +
                        " but unfortunately they were unable to be contacted")
            else:
                self.config.hugDonors[pick.id]["donations"] += 1
                self.config.save()
                return "A hug has been requested of: " + pick.name

        if args[0].lower() == 'add':
            if len(args) < 2:
                return "To add a user, please tag them after add | "
            user = self.getMember(message, args[1].lower())
            if user is None:
                return "No valid user found for " + args[1]
            if user.id in self.config.hugDonors:
                return "That user is already a hug donor"

            self.config.hugDonors[user.id] = {"name": user.name,
                                              "donations": 0}
            self.config.save()
            return "{} added to the donor list".format(user.name)

        elif args[0].lower() == 'del':
            if len(args) < 2:
                return "To remove a user, please tag them after del | "
            user = self.getMember(message, args[1].lower())
            if user is None:
                return "No valid user for " + args[1]
            if user.id not in self.config.hugDonors:
                return "That user is not a hug donor"

            del self.config.hugDonors[user.id]
            return "{} was removed from the donor list".format(user.name)

        elif args[0].lower() == 'status':
            if message.author.id not in self.config.hugDonors:
                return ("You are not a hug donor, user `freehug donate` to " +
                        "add yourself")

            return ("You have received {} requests since you became a donor"
                    .format(self.config.hugDonors
                            [message.author.id]["donations"]))

        elif args[0].lower() == 'donate':
            if message.author.id not in self.config.hugDonors:
                self.config.hugDonors[message.author.id] = {"name":
                                                            message.author
                                                            .name,
                                                            "donations": 0}
                self.config.save()
                return "Thanks! You have been added to the donor list <3"
            else:
                del self.config.hugDonors[message.author.id]
                self.config.save()
                return "You have been removed from the donor list."

    async def promote(self, message):
        """
        Promotes a member up one level. You must be at least one level higher to give them a promotion
        Syntax: `>promote (user tag)`
        """

        if not self.level4(message.author):
            return ("Dude, you don't have any perms at all. " +
                    "You can't promote people.")
        args = self.cleanInput(message.content)
        if args[0] == '':
            return "Tag someone first ya goof"
        mem = self.getMember(message, args[0])
        if mem is None:
            return "Couldn't find a member with that tag/id"

        if self.getlevel(message.author) < self.getlevel(mem):
            mlv = self.getlevel(mem)
            if mlv < 2:
                return ("You cannot promote this person any further. " +
                        " There can only be one level 0 (owner)")

            for l in self.config.get("level"):
                if mem.id in self.config.get("level")[l]:
                    self.config.get("level")[l].remove(mem.id)

            self.config.get("level")["l" + str(mlv - 1)].append(mem.id)

            self.config.save()
            return mem.name + " was promoted to level: " + str(mlv - 1)
        else:
            return "You cannot promote this person"

    async def demote(self, message):
        """
        Demotes a member down one level. You must be at least one level higher to demote someone
        Syntax: `>demote (user tag)`
        """

        if not self.level4(message.author):
            return ("Dude, you don't have any perms at all. " +
                    "You can't demote people")

        args = self.cleanInput(message.content)
        if args[0] == '':
            return "Tag someone first ya goof"
        mem = self.getMember(message, args[0])
        if mem is None:
            return "Couldn't find a member with that tag/id"

        if self.getlevel(message.author) < self.getlevel(mem):
            mlv = self.getlevel(mem)
            if mlv == 4:
                for l in self.config.get("level"):
                    if mem.id in self.config.get("level")[l]:
                        self.config.get("level")[l].remove(mem.id)
                return "All perms removed"
            if mlv == 5:
                return "Person has no perms, and therefor cannot be demoted"
            for l in self.config.get("level"):
                if mem.id in self.config.get("level")[l]:
                    self.config.get("level")[l].remove(mem.id)

            self.config.get("level")["l" + str(mlv + 1)].append(mem.id)
            self.config.save()
            return mem.name + " was promoted to level: " + str(mlv + 1)
        else:
            return "You cannot promote this person"

    async def sub(self, message, force=None):
        """
        Returns a random image from a given subreddit.
        Syntax: '>sub (subreddit)'
        """
        args = self.cleanInput(message.content)
        if args[0] == '':
            sr = "cat"
        else:
            sr = args[0]
        if force is not None:
            sr = force
        try:
            self.i
        except AttributeError:
            return "Imgur Support is disabled by administrator"

        try:
            ob = self.i.get_subreddit(sr)
            if ob is None:
                return ("Sorry, I couldn't find any images in subreddit: `" +
                        sr + "`")

            if ob.nsfw and not self.config.permitNSFW:
                return ("Found a NSFW image, currently NSFW images are " +
                        " disallowed by administrator")

        except ConnectionError as e:
            return ("A Connection Error Occurred, this usually means imgur " +
                    " is over capacity. I cant fix this part :(")

        except Exception as e:
            self.log.err("An unknown error occurred "
                         + type(e).__name__
                         + " " + str(e))
            return "Unknown Error " + type(e).__name__
        else:
            return ob.link

    async def subs(self, message):
        """
        Add or Remove subscription keys (requires level 3)
        >subs <add/remove/list> | <name of game> | <game key>
        """
        if not self.level3(message.author):
            return "You must have level 3 or above to use this"

        args = self.cleanInput(message.content)
        if args[0] == '':
            return ("Type, add remove or list after " +  self.config.prefix +
                    "args")
        if args[0].lower() == "add":
            if len(args) < 3:
                return ("Format is: " + self.config.prefix
                        + "subs <game name> | <game code (4 digit)>")

            check_duplicate = ("SELECT * FROM subKeys WHERE friendly=\""
                              + args[1].lower() + "\";")
            self.log.f("subs", check_duplicate)
            conn = pymysql.connect(self.config.get("mysql")["hostname"],
                                  self.config.get("mysql")["username"],
                                  self.config.get("mysql")["password"],
                                  self.config.get("mysql")["eventdatabase"])
            cursor = conn.cursor()
            cursor.execute(check_duplicate)

            data = cursor.fetchall()
            if len(data) > 0:
                for row in data:
                    if row[1].lower() == args[1].lower():
                        conn.close()
                        return (row[2] + " Already corresponds to a key: " +
                                row[1])

            try:
                insert_code = ("INSERT INTO subKeys VALUE (\"" + args[2].upper() + "\",\"" +
                               args[1] + "\");")
                self.log.f("subs", insert_code)
                cursor.execute(insert_code)
                conn.commit()
            except:
                self.log.err("An SQL error occurred")
                conn.rollback()
            finally:
                conn.close()

            return "Added " + args[1] + " with key: " + args[2]

        elif args[0].lower() == "list":

            conn = pymysql.connect(self.config.get("mysql")["hostname"],
                                  self.config.get("mysql")["username"],
                                  self.config.get("mysql")["password"],
                                  self.config.get("mysql")["eventdatabase"])
            cursor = conn.cursor()
            get_all = ("SELECT * FROM subKeys")
            cursor.execute(get_all)
            data = cursor.fetchall()
            if len(data) == 0:
                return "No entries found..."

            codelist =""
            for row in data:
                codelist += row[0] + " - " + row[1] + "\n"
            conn.close()
            return codelist


    async def event(self, message):
        """
        Dialog-styled event poster
        >event
        """
        if (not self.hasRole(message.author,
                             self.config.get("xPostRole"))
           and not self.level4(message.author)):

            return ("You need the: " + self.config.get("xPostRole") +
                    " role to use this command")

        chanList = []
        msg = ""
        for chan in self.config.get("xPostList"):
            channel = self.client.get_channel(chan)
            if channel is not None:
                msg += (str(len(chanList)) +
                        ". (" +
                        channel.name + " [{}]".format(channel.server.name)
                        + ")\n")
                chanList.append(channel)
            else:
                self.log.warn(chan +
                              " is not a valid channel. " +
                              " I'd remove it if I were you.")

        while True:
            await self.client.send_message(message.channel, "Hi there, " +
                                           message.author.name +
                                           "! Please select the number of " +
                                           " each server you want to post " +
                                           " to. (dont separate the numbers) ", )

            await self.client.send_message(message.channel, msg, )

            chans = await self.client.wait_for_message(channel=message.channel,
                                                       author=message.author,
                                                       check=self.isNumeric,
                                                       timeout=20)

            if chans is None:
                return ("Sorry, the request timed out. Please make sure you" +
                        " type a valid sequence of numbers")
            if self.validateChan(chanList, chans):
                break
            else:
                await self.client.send_message(message.channel, "Invalid channel choices", )
        await self.client.send_message(message.channel, "What do you want to send?" +
                                       " (remember: {e} = @ev and {h} = @her)", )

        msg = await self.client.wait_for_message(channel=message.channel,
                                                 author=message.author,
                                                 timeout=120)

        msgstr = msg.content.format(e="@everyone",
                                    h="@here")

        toPost = []
        for i in chans.content:
            print(chanList[int(i)])
            toPost.append(chanList[int(i)])

        channames = []
        for i in toPost:
            channames.append(i.name + " [" + i.server.name + "]")

        embed = discord.Embed(title="Message to post",
                              description=msgstr,
                              colour=0x0acdff)

        embed.add_field(name="Channels",
                        value="\n".join(channames))
        subkey, friendly = self.getSubscriptionKey(msgstr)
        if subkey is None:
            await self.client.send_message(message.channel, "I was unable to auto-detect " +
                                           "any game titles in your post " +
                                           "subscribers will not be notified", )
        else:
            tempm = await self.client.send_message(message.channel, "auto-detect found: **" +
                                                   friendly + "** Is this " +
                                                   "correct?[yes/no]", )
            n = await self.client.wait_for_message(channel=tempm.channel,
                                                   author=message.author,
                                                   check=self.yesNoCheck,
                                                   timeout=15)
            if n is None:
                return "Timed out..."


            if n.content == "yes":
                embed.add_field(name="Subscription Key:",
                                value=friendly + "({})".format(subkey),
                                inline=False)
                await self.notifySubs(message, subkey)

        await self.client.embed(message.channel, embed)
        await self.client.send_message(message.channel, "If this is ok, type confirm. " +
                                       " Otherwise, wait for it to timeout " +
                                       " and try again", )

        msg2 = await self.client.wait_for_message(channel=message.channel,
                                                  author=message.author,
                                                  content="confirm",
                                                  timeout=10)
        if msg2 is None:
            return "Event post timed out"

        for i in toPost:
            await self.client.send_message(i, msgstr, )
            await asyncio.sleep(2)

        await self.client.send_message(message.channel, "Messages have been posted", )

    # =========REDEFINITIONS============ #

    async def cat(self, message):
        """
        what...
        """
        return await self.sub(message, "cat")
    async def birb(self, message):
        """
        flapflap...
        """
        return await self.sub(message, "birb")
    async def dog(self, message):
        """
        what...
        """
        return await self.sub(message, "dog")

    async def doggo(self, message):
        """
        what...
        """
        return await self.sub(message, "dog")

    async def pupper(self, message):
        """
        what...
        """
        return await self.sub(message, "dog")

    async def penguin(self, message):
        """
        what...
        """
        return await self.sub(message, "penguin")

    async def ferret(self, message):
        """
        what...
        """
        return await self.sub(message, "ferret")

    async def panda(self, message):
        """
        what...
        """
        return await self.sub(message, "panda")

    async def ping(self, message):
        """
        Shows the round trip time from this bot to you and back
        Syntax: `>ping`
        """
        msg = await self.client.send_message(message.channel, "*hugs*", )
        delta = int((datetime.now() - msg.timestamp).microseconds / 1000)
        self.config.stats['pingScore'] += delta
        self.config.stats['pingCount'] += 1

        self.config.save(vb=0)
        truedelta = int(self.config.stats['pingScore'] /
                        self.config.stats['pingCount'])

        return ("Current Ping: {}ms\nPing till now: {}ms of {} pings"
                .format(str(delta),
                        str(truedelta),
                        str(self.config.stats['pingCount'])))

    async def weather(self, message):
        """
        Displays the weather for a location.
        Syntax: `>weather (location)`
        """
        args = self.cleanInput(message.content)
        return "Weather support is not available on petal just yet"

        if args[0] == '':
            self.log.warn("The member module is not ready yet.\n " +
                          "It will be implemented in a future update")

            return ("This function requires membership storage.\n " +
                    "If you're the owner of the bot. Check the logs.")
        elif len(args) == 2:

            key = self.config.get("weather")

            if not key:
                return "Weather support has not been set up by adminstrator"
            # url = ("http://api.openweathermap.org/data/2.5/weather/?APPID=" +
            # "{}&q={}&units={}".format(key, args[1], "c"))

    async def commands(self, message):
        """
        Lists all commands
        >commands
        """
        method_list = [func for func in dir(Commands) if callable(getattr(
                                                              Commands,
                                                                  func))]
        formattedList = ""
        for f in method_list:
            methodToCall = getattr(Commands, str(f))
            if methodToCall.__doc__ is None:
                self.log.f("Command List", "Ignoring " + f)
            elif str(f).startswith("__"):
                self.log.f("Command List", "Ignoring Builtin" + f)
            else:
                formattedList += (str(f) + "\n")

        return "```\n" + formattedList + "```"

    async def reddit(self, message):
        """
        Allows posting to a subreddit. Requires level 2 authorization as well as a reddit api key and an account.
        Syntax: `>reddit (post title) | (Your message) | (subreddit)`
        """
        if not self.level3(message.author):
            return "You must have level4 access to perform this command"

        args = self.cleanInput(message.content)
        if len(args) < 3:
            return ("You must have a title, a post and a subreddit. " +
                    "Check the help text")
        title = args[0]
        postdata = args[1]
        subredditstr = args[2]
        sub1 = self.r.subreddit(subredditstr)
        try:
            response = sub1.submit(title,
                                   selftext=postdata,
                                   send_replies=False)
            self.log.f("reddit", "Response Data: " + str(response))

        except praw.exceptions.APIException as e:
            return ("The post did not send, this key has been ratelimited. " +
                    "Please wait for about 8-10 minutes before posting again")
        else:
            return "Submitted post to " + subredditstr

    async def kick(self, message):
        """
        Kick's a user from a server. User must have level 2 perms. (>help promote/demote)
        >kick <user tag/id>
        """

        logChannel = message.server.get_channel(self.config.get("logChannel"))

        if logChannel is None:
            return ("I'm sorry, you must have logging enabled to use" +
                    " administrative functions")

        if not self.hasRole(message.author, "mod"):
            return "You must have the `mod` role"

        await self.client.send_message(message.channel, "Please give a reason" +
                                       "(just reply below): ", )

        msg = await self.client.wait_for_message(channel=message.channel,
                                                 author=message.author,
                                                 timeout=30)
        if msg is None:
            return "Timed out while waiting for input"

        userToBan = self.getMember(message,
                                   self.cleanInput(message.content)[0])
        if userToBan is None:
            return "Could not get user with that id"

        else:
            try:
                petal.logLock = True
                await self.client.kick(userToBan)
            except discord.errors.Forbidden as ex:
                return "It seems I don't have perms to kick this user"
            else:
                logEmbed = discord.Embed(title="User Kick",
                                         description=msg.content,
                                         colour=0xff7900)
                logEmbed.set_author(name=self.client.user.name,
                                    icon_url="https:" +
                                             "//puu.sh/tAAjx/2d29a3a79c.png")
                logEmbed.add_field(name="Issuer",
                                   value=message.author.name +
                                        "\n" + message.author.id)
                logEmbed.add_field(name="Recipient",
                                   value=userToBan.name +
                                        "\n" + userToBan.id)
                logEmbed.add_field(name="Server",
                                   value=userToBan.server.name)
                logEmbed.add_field(name="Timestamp",
                                   value=str(datetime.utcnow())[:-7])
                logEmbed.set_thumbnail(url=userToBan.avatar_url)

                await self.client.embed(self.client.get_channel(
                                        self.config.modChannel), logEmbed)
                await self.client.send_message(message.channel, "Cleaning up...", )
                await self.client.send_typing(message.channel)
                await asyncio.sleep(4)
                petal.lockLog = False
                return (userToBan.name + " (ID: " +
                        userToBan.id + ") was successfully kicked")

    async def ban(self, message):
        """
        Bans a user permenantly. Temp ban coming when member module works.
        >ban <user tag/id>
        """

        logChannel = message.server.get_channel(self.config.get("logChannel"))

        if logChannel is None:
            return ("I'm sorry, you must have logging enabled " +
                    "to use administrative functions")

        if not self.hasRole(message.author, "mod"):
            return "You must have the `mod` role"

        await self.client.send_message(message.channel, "Please give a reason" +
                                       " (just reply below): ", )

        msg = await self.client.wait_for_message(channel=message.channel,
                                                 author=message.author,
                                                 timeout=30)
        if msg is None:
            return "Timed out while waiting for input"

        userToBan = self.getMember(message,
                                   self.cleanInput(message.content)[0])
        if userToBan is None:
            return "Could not get user with that id"

        else:
            await self.client.send_message(message.channel, "You are about to ban: " +
                                           userToBan.name +
                                           ". If this is correct, type `yes`", )
            msg = await self.client.wait_for_message(channel=message.channel,
                                                     author=message.author,
                                                     timeout=10)
            if msg is None:
                return "Timed out... user was not banned"
            else:
                if msg.content != "yes":
                    return userToBan.name + " was not banned"

            try:
                petal.logLock = True
                await asyncio.sleep(1)
                await self.client.ban(userToBan)
            except discord.errors.Forbidden as ex:
                return "It seems I don't have perms to ban this user"
            else:
                logEmbed = discord.Embed(title="User Ban",
                                         description=msg.content,
                                         colour=0xff0000)
                logEmbed.set_author(name=self.client.user.name,
                                    icon_url="https://" +
                                             "puu.sh/tACjX/fc14b56458.png")
                logEmbed.add_field(name="Issuer",
                                   value=message.author.name +
                                   "\n" + message.author.id)
                logEmbed.add_field(name="Recipient",
                                   value=userToBan.name
                                   + "\n" + userToBan.id)
                logEmbed.add_field(name="Server",
                                   value=userToBan.server.name)
                logEmbed.add_field(name="Timestamp",
                                   value=str(datetime.utcnow())[:-7])

                logEmbed.set_thumbnail(url=userToBan.avatar_url)

                await self.client.embed(self.client.get_channel(
                                        self.config.modChannel),
                                        logEmbed)
                await self.client.send_message(message.channel, "Clearing out messages... ", )
                await asyncio.sleep(4)
                petal.logLock = False
                return (userToBan.name + " (ID: " + userToBan.id
                        + ") was successfully banned")

    async def tempban(self, message):
        """
        Temporarily bans a user
        >tempban <user tag/id>
        """
        logChannel = message.server.get_channel(self.config.get("logChannel"))
        if logChannel is None:
            return ("I'm sorry, you must have logging enabled to" +
                    " use administrative functions")

        await self.client.send_message(message.channel, "Please give a reason " +
                                       " (just reply below): ", )
        msg = await self.client.wait_for_message(channel=message.channel,
                                                 author=message.author,
                                                 timeout=30)
        if msg is None:
            return "Timed out while waiting for input"

        await self.client.send_message(message.channel, "How long? (days) ", )
        msg2 = await self.client.wait_for_message(channel=message.channel,
                                                  author=message.author,
                                                  check=self.isNumeric,
                                                  timeout=30)
        if msg2 is None:
            return "Timed out while waiting for input"

        userToBan = self.getMember(message,
                                   self.cleanInput(message.content)[0])
        if userToBan is None:
            return "Could not get user with that id"

        else:
            try:
                petal.logLock = True
                self.client.members.addMember(userToBan)
                if await self.client.members.tempBan(userToBan,
                                                     message.author,
                                                     msg.content,
                                                     int(msg2.content)):
                    return "Successfully temp banned user"
                else:
                    return "Unable to tempban user, are they already banned?"

            except discord.errors.Forbidden as ex:
                return "It seems I don't have perms to ban this user"
            else:
                logEmbed = discord.Embed(title="User Ban",
                                         description=msg.content,
                                         colour=0xff0000)

                logEmbed.add_field(name="Issuer",
                                   value=message.author.name + "\n" +
                                   message.author.id)
                logEmbed.add_field(name="Recipient",
                                   value=userToBan.name + "\n" +
                                   userToBan.id)
                logEmbed.add_field(name="Server", value=userToBan.server.name)
                logEmbed.add_field(name="Timestamp",
                                   value=str(datetime.utcnow())[:-7])
                logEmbed.set_thumbnail(url=userToBan.avatar_url)

                await self.client.embed(self.client.get_channel(
                                        self.config.modChannel), logEmbed)
                await self.client.send_message(message.channel, "Clearing out messages... ", )
                await asyncio.sleep(4)
                petal.logLock = False
                return (userToBan.name + " (ID: " + userToBan.id +
                        ") was successfully banned")

    async def warn(self, message):
        """
        Sends an official, logged, warning to a user.
        >warn <user tag/id>
        """
        logChannel = message.server.get_channel(self.config.get("logChannel"))

        if logChannel is None:
            return ("I'm sorry, you must have logging enabled " +
                    "to use administrative functions")

        if not self.level2(message.author):
            return "You must have lv2 perms to use the warn command"

        await self.client.send_message(message.channel, "Please give a message to send " +
                                       "(just reply below): ", )
        msg = await self.client.wait_for_message(channel=message.channel,
                                                 author=message.author,
                                                 timeout=30)
        if msg is None:
            return "Timed out while waiting for input"

        userToWarn = self.getMember(message,
                                    self.cleanInput(message.content)[0])
        if userToWarn is None:
            return "Could not get user with that id"

        else:
            try:
                warnEmbed = discord.Embed(title="Official Warning",
                                          description="The server has sent " +
                                          " you an official warning",
                                          colour=0xfff600)

                warnEmbed.add_field(name="Reason", value=msg.content)
                warnEmbed.add_field(name="Issuing Server",
                                    value=message.server.name,
                                    inline=False)
                await self.client.embed(userToWarn, warnEmbed)

            except discord.errors.Forbidden as ex:
                return "It seems I don't have perms to warn this user"
            else:
                logEmbed = discord.Embed(title="User Warn",
                                         description=msg.content,
                                         colour=0xff600)
                logEmbed.set_author(name=self.client.user.name,
                                    icon_url=(
                                     "https://puu.sh/tADFM/dc80dc3a5d.png"))
                logEmbed.add_field(name="Issuer",
                                   value=message.author.name +
                                   "\n" + message.author.id)
                logEmbed.add_field(name="Recipient",
                                   value=userToWarn.name +
                                   "\n" + userToWarn.id)
                logEmbed.add_field(name="Server", value=userToWarn.server.name)
                logEmbed.add_field(name="Timestamp",
                                   value=str(datetime.utcnow())[:-7])
                logEmbed.set_thumbnail(url=userToWarn.avatar_url)

                await self.client.embed(self.client.get_channel(
                                        self.config.modChannel), logEmbed)
                return (userToWarn.name + " (ID: " + userToWarn.id +
                        ") was successfully warned")

    async def mute(self, message):
        """
        Toggles the mute tag on a user if your server supports that role.
        >mute <user tag/ id>
        """
        muteRole = discord.utils.get(message.server.roles, name="mute")
        if muteRole is None:
            return ("This server does not have a `mute` role. " +
                    "To enable the mute function, set up the " +
                    "roles and name one `mute`.")
        logChannel = message.server.get_channel(self.config.get("logChannel"))

        if logChannel is None:
            return ("I'm sorry, you must have logging enabled to " +
                    "use administrative functions")

        if (not self.level3(message.author) and
           not self.hasRole(message.author, "mod")):
            return ("You must have lv3 perms or the `mod`" +
                    " role to use the mute command")

        await self.client.send_message(message.channel, "Please give a " +
                                       "reason for the mute " +
                                       "(just reply below): ", )
        msg = await self.client.wait_for_message(channel=message.channel,
                                                 author=message.author,
                                                 timeout=30)
        if msg is None:
            return "Timed out while waiting for input"

        userToWarn = self.getMember(message,
                                    self.cleanInput(message.content)[0])
        if userToWarn is None:
            return "Could not get user with that id"

        else:
            try:

                if muteRole in userToWarn.roles:
                    await self.client.remove_roles(userToWarn, muteRole)
                    warnEmbed = discord.Embed(title="User Unmute",
                                              description="You have been " +
                                              "unmuted by" +
                                              message.author.name,
                                              colour=0x00ff11)


                    warnEmbed.add_field(name="Reason",
                                        value=msg.content)
                    warnEmbed.add_field(name="Issuing Server",
                                        value=message.server.name,
                                        inline=False)
                    muteswitch = "Unmute"
                else:
                    await self.client.add_roles(userToWarn, muteRole)
                    warnEmbed = discord.Embed(title="User Mute",
                                              description="You have been " +
                                                          "muted by" +
                                                          message.author.name,
                                                          colour=0xff0000)
                    warnEmbed.set_author(name=self.client.user.name,
                                         icon_url="https://puu.sh/tB2KH/" +
                                                  "cea152d8f5.png")
                    warnEmbed.add_field(name="Reason", value=msg.content)
                    warnEmbed.add_field(name="Issuing Server",
                                        value=message.server.name,
                                        inline=False)
                    muteswitch = "Mute"
                await self.client.embed(userToWarn, warnEmbed)

            except discord.errors.Forbidden as ex:
                return "It seems I don't have perms to mute this user"
            else:
                logEmbed = discord.Embed(title="User {}".format(muteswitch),
                                         description=msg.content,
                                         colour=0x1200ff)

                logEmbed.add_field(name="Issuer",
                                   value=message.author.name + "\n" +
                                        message.author.id)
                logEmbed.add_field(name="Recipient",
                                   value=userToWarn.name + "\n" +
                                        userToWarn.id)
                logEmbed.add_field(name="Server",
                                   value=userToWarn.server.name)
                logEmbed.add_field(name="Timestamp",
                                   value=str(datetime.utcnow())[:-7])
                logEmbed.set_thumbnail(url=userToWarn.avatar_url)

                await self.client.embed(self.client.get_channel(
                                        self.config.modChannel), logEmbed)
                return (userToWarn.name + " (ID: " + userToWarn.id +
                        ") was successfully {}d".format(muteswitch))

    async def purge(self, message):
        """
        purges up to 200 messages in the current channel
        >purge <number of messages to delete>
        """
        if message.author == self.client.user:
            return
        if not self.level2(message.author):
            return ("You do not have sufficient permissions to use the purge" +
                    " function")
        args = self.cleanInput(message.content)
        if len(args) < 1:
            return "Please provide a number between 1 and 200"
        try:
            numDelete = int(args[0].strip())
        except ValueError:
            return "Please make sure your input is a number"
        else:
            if numDelete > 200 or numDelete < 0:
                return "That is an invalid number of messages to delete"
        await self.client.send_message(message.channel, "You are about to delete {} messages " +
                                       "(including these confirmations) in " +
                                       "this channel. Type: confirm if this " +
                                       "is correct.".format(str(numDelete + 3)), )
        msg = await self.client.wait_for_message(channel=message.channel,
                                                 content="confirm",
                                                 author=message.author,
                                                 timeout=10)
        if msg is None:
            return "Purge event cancelled"
        try:
            petal.logLock = True
            await self.client.purge_from(channel=message.channel,
                                         limit=numDelete + 3,
                                         check=None)
        except discord.errors.Forbidden:
            return "I don't have enough perms to purge messages"
            await asyncio.sleep(2)

            logEmbed = discord.Embed(title="Purge Event",
                                     description="{} messages were purged " +
                                                 "from {} in {} by {}#{}"
                                                 .format(str(numDelete),
                                                         message.channel.name,
                                                         message.server.name,
                                                         message.author.name,
                                                         message.author.
                                                         discriminator),
                                                 color=0x0acdff)
            await self.client.embed(self.client.get_channel(
                                    self.config.modChannel),
                                    logEmbed)
            await asyncio.sleep(4)
            petal.logLock = False
            return

    async def void(self, message):
        """
        >void grabs a random item from the void and displays/prints it.
        >void <link or text message> sends to void forever
        """
        args = self.cleanInput(message.content)
        if args[0] == "":
            response = self.db.get_void()
            author = response["author"]
            num = response["number"]
            response = response["content"]

            if "@everyone" in response or "@here" in response:
                self.db.delete_void()
                return "Someone (" + author + ") is a butt and tried to " \
                                              "sneak an @ev tag into the void." \
                                              "\n\nIt was deleted..."

            if response.startswith("http"):
                return "*You grab a link from the void* \n" + response
            else:
                self.log.f("VOID", message.author.name + " retrieved " + str(response["number"]) + " from the void")
                return response
        else:
            count = self.db.save_void(args[0],
                                      message.author.name,
                                      message.author.id)

            if count is not None:
                return "Added item number " + str(count) + " to the void"

    async def update(self, message):
        """
        >update
        Post updates to social media
        """

        if not self.hasRole(message.author,
                            self.config.get("socialMediaRole")):
            return "You must have `{}` to post social media updates"
        modes = []
        names = []
        using = []
        if self.config.get("reddit") is not None:

            names.append(str(len(modes)) + " reddit")
            modes.append(self.r)
            using.append("reddit")
        if self.config.get("twitter") is not None:

            names.append(str(len(modes)) + " twitter")
            modes.append(self.t)
            using.append("twitter")
        if self.config.get("facebook") is not None:

            names.append(str(len(modes)) + " facebook")
            modes.append(self.fb)
            using.append("facebook")
        if self.config.get("tumblr") is not None:

            names.append(str(len(modes)) + " tumblr")
            modes.append(self.tb)
            using.append("tumblr")

        if len(modes) == 0:
            return "No modules enabled for social media posting"

        await self.client.send_message(message.channel, "Hello, " +
                                       message.author.name +
                                       " here are the enabled social media " +
                                       "services \n" + "\n".join(names) +
                                       "\n\n Please select which ones you " +
                                       "want to use (e.g. 023) ", )

        sendto = await self.client.wait_for_message(channel=message.channel,
                                                    author=message.author,
                                                    check=self.isNumeric,
                                                    timeout=20)
        if sendto is None:
            return ("The process timed out, " +
                    "please enter a valid string of numbers")
        if not self.validateChan(modes, sendto):
            return "Invalid selection, please try again"

        await self.client.send_message(message.channel, "Please type a title for your post " +
                                       "(timeout after 1 minute)", )
        mtitle = await self.client.wait_for_message(channel=message.channel,
                                                    author=message.author,
                                                    timeout=60)
        if mtitle is None:
            return "The process timed out, you need a valid title"
        await self.client.send_message(message.channel, "Please type the content of the post " +
                                       "below. Limit to 140 characters for " +
                                       "twitter posts (this process will " +
                                       "time out after 2 minutes)", )
        mcontent = await self.client.wait_for_message(channel=message.channel,
                                                      author=message.author,
                                                      timeout=120)

        if mcontent is None:
            return "The process timed out, you need content to post"

        if "1" in sendto.content:
            if len(mcontent.content) > 140:
                return "This post is too long for twitter"

        await self.client.send_message(message.channel, "Your post is ready. Please type: " +
                                       "`send`", )
        meh = await self.client.wait_for_message(channel=message.channel,
                                                 author=message.author,
                                                 content="send",
                                                 timeout=10)
        if meh is None:
            return "Timed out, message not send"
        if "0" in sendto.content:
            sub1 = self.r.subreddit(self.config.get("reddit")["targetSR"])
            try:
                response = sub1.submit(mtitle.content,
                                       selftext=mcontent.clean_content,
                                       send_replies=False)
                self.log.f("smupdate", "Reddit Response: " + str(response))
            except praw.exceptions.APIException as e:
                await self.client.send_message(message.channel, "The post did not send, " +
                                               "this key has been " +
                                               "ratelimited. Please wait for" +
                                               " about 8-10 minutes before " +
                                               "posting again", )
            else:
                await self.client.send_message(message.channel, "Submitted post to " +
                                               self.config.get("reddit")
                                               ["targetSR"], )
                await asyncio.sleep(2)

        if "1" in sendto.content:
            status = self.t.PostUpdate(mcontent.clean_content)
            await self.client.send_message(message.channel, "Submitted tweet", )
            await asyncio.sleep(2)

        if "2" in sendto.content:

            # Setting up facebook takes a bit of digging around to see how
            # their API works. Basically you have to be admin'd on a page
            # and have its ID as well as generate an OAUTH2 long-term key.
            # Facebook python API was what I googled

            resp = self.fb.get_object('me/accounts')
            page_access_token = None
            for page in resp['data']:
                if page['id'] == self.config.get("facebook")["pageID"]:
                    page_access_token = page['access_token']
            postpage = facebook.GraphAPI(page_access_token)

            if postpage is None:
                await self.client.send_message(message.channel, "Invalid page id for " +
                                               "facebook, will not post", )
            else:
                status = postpage.put_wall_post(mcontent.clean_content)
                await self.client.send_message(message.channel, "Posted to facebook under " +
                                               " page: " + page["name"], )
                self.log.f("smupdate", "Facebook Response: " + str(status))
                await asyncio.sleep(2)

        if "3" in sendto.content:
            self.tb.create_text(self.config.get("tumblr")["targetBlog"],
                                state="published",
                                slug="post from petalbot",
                                title=mtitle.content,
                                body=mcontent.clean_content)

            await self.client.send_message(message.channel, "Posted to tumblr: " +
                                           self.config.get("tumblr")
                                           ["targetBlog"], )

        return "Done posting"

    async def blacklist(self,  message):
        """
        Prevents tagged user from using petal
        >blacklist <tag>
        """

        args = self.cleanInput(message.content)
        if not self.level2(message.author) and self.hasRole(message.author,
                                                            "mod"):
            return "You need level 2 or the `mod` role"
        if len(args) < 1:
            return "Tag someone ya goof"
        else:
            mem = self.getMember(message, args[0])
            if mem is None:
                return "Couldnt find user with ID: " + args[0]

            if mem.id in self.config.blacklist:
                self.config.blacklist.remove(mem.id)
                return mem.name + " was given the ability to use petal again"
            else:
                self.config.blacklist.append(mem.id)
                return mem.name + " was blacklisted"

    async def calm(self, message):
        """
        Brings up a random image from the calm gallery. Or adds it.
        >calm <link to add to calm>
        """

        args = self.cleanInput(message.content)
        gal = self.config.get("calmGallery")
        if gal is None:
            return "Sadly, calm hasn't been set up correctly"
        if self.level4(message.author) and args[0] != '':
            await self.client.send_message(message.channel, "You will be held accountable for" +
                                           " whatever is posted in here." +
                                           " Just a heads up ^_^ ", )
            gal.append({"author": message.author.name + " " +
                       message.author.id,
                       "content": args[0].strip()})
            self.config.save()
        else:
            return gal[random.randint(0, len(gal)-1)]["content"]

    async def comfypixel(self, message):
        """
        Brings up a random image from the comfypixel gallery. Or adds it
        >comfypixel <link to add to comfypixel>
        """

        args = self.cleanInput(message.content)
        gal = self.config.get("comfyGallery")
        if gal is None:
            return "Sadly, comfypixel hasn't been set up correctly"
        if self.level4(message.author) and args[0] != '':
            await self.client.send_message(message.channel, "You will be held accountable " +
                                           "for whatever is posted in here." +
                                           " Just a heads up ^_^ ", )
            gal.append({"author": message.author.name + " " +
                        message.author.id,
                        "content": args[0].strip()})
            self.config.save()
        else:
            return gal[random.randint(0, len(gal)-1)]["content"]

    async def gmt(self, message):
        """
        >Returns UTC time
        >GMT
        """

        return ("It is " + str(datetime.utcnow())[:-7] +
                "\n\n Num time: " + str(datetime.utcnow() -
                                        timedelta(hours=12))[:-7] +
                "\n if this number is weird looking, then its AM)")

    async def askpatch(self, message):
        """
        >Gives access to the askpatch database
        >askpatch <submit/approve/ignore> | <extra sometimes required info>
        """

        # Like I said ealier in checkUpdate(), ask patch is really only
        # designed to work with discord.gg/patchgaming. If you want to dig
        # around in here and change things, feel free.
        # (mySql Schema in checkUpdate() )

        if message.channel.id != self.config.get("motdChannel"):
            self.log.f("ap", str(message.server.id ) + " != " + self.config.get("motdChannel")  )
            return "Sorry, you are not permitted to use this"
        args = self.cleanInput(message.content)
        print(str(args))
        if args[0] == "submit":
            conn = pymysql.connect(self.config.get("mysql")["hostname"],
                                  self.config.get("mysql")["username"],
                                  self.config.get("mysql")["password"],
                                  self.config.get("mysql")["padatabase"])
            cursor = conn.cursor()
            add_question = ("INSERT INTO questions (author, id, content, " +
                            "used) VALUES (\"{}\", \"{}\", \"{}\", false)"
                            .format(message.author.name,
                                    message.author.id,
                                    " ".join(args[1:])))
            get_entry = "SELECT MAX(entryid) from questions;"
            await self.client.send_message(message.channel, "Your message will be added to " +
                                           "the database. Is this correct? " +
                                           "(type yes if yes)\n" +
                                           " ".join(args[1:]), )

            res = await self.client.wait_for_message(author=message.author,
                                                     channel=message.channel,
                                                     timeout=20)
            if res is None:
                return "Timed out without response"
            else:
                if res.content == "yes":
                    cursor.execute(add_question)
                    conn.commit()
                    cursor.execute(get_entry)
                    r = cursor.fetchone()
                    entryid =  r[0]
                    entryid = str(entryid).lstrip("('").rstrip("',)")
                    chan = self.client.get_channel(self.config.get("motdChannel"))
                    newEmbed = discord.Embed(title="Entry " + str(entryid),
                                             description="New question from "
                                             + message.author.name,
                                             colour=0x8738f9)

                    newEmbed.add_field(name="Question",
                                       value=" ".join(args[1:]))
                    conn.close()

                    await self.client.embed(chan, newEmbed)
                else:
                    return "Okie dokie, try again if you like"
            return "Question added to database"

        elif args[0] == "approve":
            if message.channel.id != self.config.get("motdChannel"):
                return "You can't use that here"
            else:
                if len(args) < 2:
                    return "You need to specify an entry"
                else:
                    conn = pymysql.connect(self.config.get("mysql")["hostname"],
                                          self.config.get("mysql")["username"],
                                          self.config.get("mysql")["password"],
                                          self.config.get("mysql")["padatabase"])
                    cursor = conn.cursor()
                    find_entry = ("SELECT entryid, author, content, used," +
                                  " approved FROM questions WHERE entryid=" +
                                  args[1])
                    approve_entry = ("UPDATE questions SET approved = true" +
                                     " WHERE entryid=" + args[1])
                    cursor.execute(find_entry)
                    entry = cursor.fetchone()

                    if not entry:
                        return "Could not find any row with"

                    entryid = entry[0]
                    # author = entry[1].decode("utf-8")
                    content = entry[2]
                    # used = entry[3]
                    approved = entry[4]
                    if approved == "1":
                        newEmbed = discord.Embed(title="Already Approved " +
                                                       str(entryid),
                                                 description=content,
                                                 colour=0xFFA500)
                        newEmbed.set_author(name="AskPatch",
                                            icon_url="http://images.clipart" +
                                                     ".panda.com/question-" +
                                                     "mark-icon-Question-" +
                                                     "Mark-Icon.jpg")
                        chan = self.client.get_channel(self.config.get("motdChannel"))
                        await self.client.embed(chan, newEmbed)
                        return ("Entry has already been approved, " +
                                "use reject to remove it from the queue")

                    cursor.execute(approve_entry)
                    conn.commit()
                    conn.close()

                    newEmbed = discord.Embed(title="Approved " + str(entryid),
                                             description=content,
                                             colour=0x00FF00)

                    newEmbed.add_field(name="Has been Approved",
                                       value="True")
                    chan = self.client.get_channel(self.config.get("motdChannel"))
                    await self.client.embed(chan, newEmbed)

        elif args[0] == "ignore":
            if message.channel.id != self.config.get("motdChannel"):
                return "You can't use that here"
            else:
                if len(args) < 2:
                    return "You need to specify an entry"
                else:
                    conn = pymysql.connect(self.config.get("mysql")["hostname"],
                                          self.config.get("mysql")["username"],
                                          self.config.get("mysql")["password"],
                                          self.config.get("mysql")["padatabase"])
                    cursor = conn.cursor()
                    find_entry = ("SELECT entryid, author, content, used," +
                                  " approved FROM questions WHERE entryid=" +
                                  args[1])
                    approve_entry = ("UPDATE questions SET approved = false " +
                                     "WHERE entryid=" + args[1])
                    cursor.execute(find_entry)
                    entry = cursor.fetchone()

                    if not entry:
                        return "Could not find any row with"


                    entryid = entry[0]
                    # author = entry[1].decode("utf-8")
                    content = entry[2]
                    # used = entry[3]
                    approved = entry[4]
                    if approved == "0":
                        newEmbed = discord.Embed(title="Rejected " +
                                                       str(entryid),
                                                 description=content,
                                                 colour=0xFFA500)

                        chan = self.client.get_channel(self.config.get("motdChannel"))
                        await self.client.embed(chan, newEmbed)
                        return ("Entry has already been rejected or has not " +
                                "been approved yet, use approve to add it to" +
                                " the queue")

                    cursor.execute(approve_entry)
                    conn.commit()
                    cursor.close()

                    newEmbed = discord.Embed(title=" " + str(entryid),
                                             description=content,
                                             colour=0xFF0000)

                    newEmbed.add_field(name="Rejected", value="True")
                    chan = self.client.get_channel(self.config.get("motdChannel"))
                    await self.client.embed(chan, newEmbed)
                    return "Entry has been removed from the queue"
        elif args[0] == 'list':
            return ("Patch Asks info can be found at " +
                    " http://drunkencode.net/askpatch")

    async def paforce(self, message):
        """
        >Allows a manager to force patch asks without regard for the timer
        >paforce
        """
        if self.level2(message.author):
            await self.checkUpdate(force=True)

            self.log.f("pa", message.author.name + " with ID: " +
                       message.author.id +
                       " used the force!")
            await self.client.delete_message(message)
            return
        else:
            return "You may not use this command"

    async def forcesave(self, message):
        """
        Owner only, forces save to config.yaml
        >save
        """
        if self.level0(message.author):
            self.config.save(vb=1)
            return "Saved"

    async def forceload(self, message):
        """
        Owner only, forces config to load
        >load
        """
        if self.level0(message.author):
            self.config.load()
            return "Loaded config file"

    async def anon(self, message):
        """
        For use in PMs only, connects you anonymously to a listeners
        >anon or >anon <tagged user>
        """
        alpha = ["giraffe", "panda", "whale", "raccoon", "rabbit",
                 "squirell", "moose", "sheep", "ferret", "stoat", "cow",
                 "noperope", "kitten", "puppy", "snail", "turtle", "tortoise",
                 "zebra", "lion", "elephant", "sloth", "drop bear", "octopus",
                 "turkey", "pelican", "GreaterDog", "lesserDog", "seahorse"]

        beta = ["Apple", "Apricots", "Avocado", "Banana", "Cherries",
                "Cherimoya", "Blackberry", "Raspberry",  "Coconut",
                "Orange", "Grapefruit", "Guava", "Honeydew", "Melon",
                "Cantaloupe", "Lime", "Lemon", "MangoQuince", "Kiwi",
                "Sapodilla"]
        name1 = (beta[randint(0, len(beta)-1)] +
                alpha[randint(0, len(alpha)-1)].title())
        name2 = (beta[randint(0, len(beta)-1)] +
                alpha[randint(0, len(alpha)-1)].title())


        anondb = self.config.get("anon")

        if (message.author.id in self.activeSads
           or message.author.id in self.activeHelpers):
            return "You're already in a call..."

        if anondb is None:
            return "Unfortunately anon support is turned off in config"

        server = self.client.get_server(anondb["server"])
        if not message.channel.is_private:
            args = self.cleanInput(message.content)
            if len(args) == 0:
                return "For private chat only, unless adding users"
            if not self.level2(message.author):
                return "You cannot use this"


            m = self.getMember(message, args[0])
            try:
                anondb = self.config.get("anon")["help"]
                anonserver = self.client.get_server(self.config
                                                        .get("anon")["server"])
            except KeyError:
                return "Anon is misconfigured, check config.yaml"

            if discord.utils.get(anonserver.members, id=m.id) is None:
                return "User must be a member of " + anonserver.name

            if m.id not in anondb:

                anondb.append(m.id)
                self.config.save(vb=1)
                self.log.f("anon", message.author.name +
                                   " added " + m.name + " to anon list")
                return "Added " + m.mention + " to anon list!"
            else:
                del anondb[anondb.index(m.id)]
                self.config.save(vb=1)
                self.log.f("anon", message.author.name +
                                   " removed " + m.name + " from anon list")
                return "Removed " + m.mention + " from anon list!"

        await self.client.send_message(message.channel, "One moment while I " +
                                       "connect you to a listener", )
        self.activeSads.append(message.author.id)

        await asyncio.sleep(1)
        x = await self.client.send_message(message.channel, "Your name is: "
                                           + name1, )

        availableHelpers = []
        for z in anondb["help"]:
            if z not in self.activeHelpers and z != message.author.id:
                h = discord.utils.get(server.members, id=z)
                if h is not None and h.status == discord.Status.online:
                    availableHelpers.append(z)



        saduser = message.author
        if len(availableHelpers) == 0:
            del self.activeSads[self.activeSads.index(message.author.id)]
            return ("All helpers are currently assisting others right now, " +
                    " please try again later")
        await self.client.send_message(message.channel, "There are currently: " +
                                       str(len(availableHelpers)) +
                                       " available helpers.", )
        self.log.info(str(anondb["help"]))

        helpid = availableHelpers[randint(0, len(availableHelpers)-1)]

        helpuser = discord.utils.get(server.members, id=helpid)
        if helpuser is None:
            self.log.warn(helpid + " is an invalid id for anon")
            del self.activeSads[self.activeSads.index(message.author.id)]
            return "Found invalid user, try again"
        self.activeHelpers.append(helpid)
        m = await self.client.send_message(helpuser, "Hello, there is someone " +
                                           "who wants to chat " +
                                           "anonymously.\n " +
                                           "Type accept to begin", )
        n = await self.client.wait_for_message(channel=m.channel,
                                               author=helpuser,
                                               content="accept", timeout=15)
        if n is None:
            await self.client.send_message(helpuser, "Timed out...", )
            del self.activeHelpers[self.activeHelpers.index(helpid)]
            del self.activeSads[self.activeSads.index(message.author.id)]
            return "Sorry, the user didnt respond"
        await self.client.send_message(helpuser, "The chat will automatically dis" +
                                       "connect if either user is idle " +
                                       "for more than 5 minutes" +
                                       "\n(or type !end)", )
        await self.client.send_message(saduser, "The chat will automatically dis" +
                                       "connect if either user is idle " +
                                       "for more than 5 minutes" +
                                       "\n(or type !end)", )

        await self.client.send_message(helpuser, "Connected! Your name is: " +
                                       name2 + ".\n Type a message.", )

        await self.client.send_message(helpuser, "*Just a small note, while this is " +
                                       "designed to be completely anon, " +
                                       "petal still keeps a hidden record of" +
                                       " your userID corresponding to your " +
                                       "fake name. Only admins can see this " +
                                       "and we will not view it unless abuse " +
                                       " is reported from either party*", )
        await self.client.send_message(saduser, "*Just a small note, while this is " +
                                       "designed to be completely anon, " +
                                       "petal still keeps a hidden record of" +
                                       " your userID corresponding to your " +
                                       "fake name. Only admins can see this " +
                                       "and we will not view it unless abuse " +
                                       " is reported from either party*", )

        self.log.f("anon", name1 + " is " + saduser.name + " " + saduser.id)
        self.log.f("anon", name2 + " is " + helpuser.name + " " + helpuser.id)
        self.hc= m.channel
        self.sc = x.channel
        while True:

            m = await self.client.wait_for_message(check=self.anonCheck,
                                                   timeout=300)
            if m is None:
                await self.client.send_message(helpuser, "Chat timed out...", )
                del self.activeHelpers[self.activeHelpers.index(helpid)]
                del self.activeSads[self.activeSads.index(message.author.id)]
                return "Chat timed out..."
            if m.content == "!end":
                await self.client.send_message(helpuser, "Chat ended", )
                del self.activeHelpers[self.activeHelpers.index(helpid)]
                del self.activeSads[self.activeSads.index(message.author.id)]
                return "Chat ended"
            if m.channel == self.sc:
                await self.client.send_message(self.hc, "**" + name1 + "**: " +
                                               m.content, )
            else:
                await self.client.send_message(self.sc, "**" + name2 + "**: " +
                                               m.content, )

    async def support(self, message):
        """
        >Notifies the listeners that you need help
        >support <optional message>
        """
        if self.config.get("supportChannel") is None:
            self.log.err("supportChannel not found")
            return "SupportChannel not configured in settings."

        if message.author.id in self.supportdict:
            if time.time() - self.supportdict[message.author.id] < 300:
                tval = 500 - round(time.time()
                                   - self.supportdict[message.author.id], 2)
                em = discord.Embed(title="Spam prevention",
                                   description="You are doing that too much",
                                   colour=0x0acdff)
                em.add_field(name="Command", value="support")
                em.add_field(name="Time Remaining", value=tval)
                await self.client.embed(message.channel, em)
                return ("If this is an emergency, please call your local"
                        + " emergency line (911, 999, etc)")

            else:
                self.supportdict[message.author.id] = time.time()
        else:
            self.supportdict[message.author.id] = time.time()
        args = self.cleanInput(message.content)

        if len(args) == 0:
            await self.client.send_message(self.client.get_channel(
                self.config.get("supportChannel")), "@here, " +
                                                    message.author.mention +
                                                    " (mobile friendly: " +
                                                    message.author.name +
                                                    ") has requested " +
                                                    "listener support in " +
                                                    message.channel.name +
                                                    " (" + message.server
                                                    .name + ")" +
                                                    "\n (They gave no " +
                                                    "message)", )

        else:
            await self.client.send_message(self.client.get_channel(self.config.get("supportChannel")),
                                           "@here, " + message.author.mention + " (mobile friendly: " +
                                           message.author.name + ") has requested listener support " +
                                           "in " + message.channel.name + " (" + message.server.name +
                                           ")." + "\n Message: `" + ' '.join(args) + "`", )

            return (message.author.mention +
                    " do not worry, your request has been sent to the " +
                    "listener server and someone should be with you shortly")

    async def statsfornerds(self, message):
        """
        Displays stats for nerds
        !statsfornerds
        """
        truedelta = int(self.config.stats['pingScore'] /
                        self.config.stats['pingCount'])

        em = discord.Embed(title="Stats",
                           description="*for nerds*",
                           colour=0x0acdff)
        em.add_field(name="Version", value=version)
        em.add_field(name="Uptime", value=self.getUptime())
        em.add_field(name="Void Count", value=str(self.db.void.count()))
        em.add_field(name="Servers", value=str(len(self.client.servers)))
        em.add_field(name="Total Number of Commands run",
                     value=str(self.config.get("stats")["comCount"]))
        em.add_field(name="Average Ping", value=str(truedelta))
        mc = 0
        for x in self.client.get_all_members():
            mc += 1
        em.add_field(name="Total Members",
                     value=str(mc))
        role = discord.utils.get(self.client.get_server(
                                 self.config.get("mainServer")).roles,
                                 name=self.config.get("mainRole"))
        c = 0
        if role is not None:
            for m in self.client.get_all_members():

                if role in m.roles:
                    c += 1
            em.add_field(name="Total Validated Members", value=str(c))

        await self.client.embed(message.channel, em)

    async def wiki(self, message):
        """
        Retrieves information about a query from wikipedia
        !wiki <query>
        """
        query = message.content.lstrip(self.config.prefix + "wiki")
        self.log.f("wiki", "Query string: " + query)
        response = Pidgeon(query, version=version).get_summary()
        if response[0] == 0:
            return response[1]
        else:
            if "may refer to:" in response[1]["content"]:
                em = discord.Embed( color=0xffcc33)
                if "may refer to:" in response[1]["content"]:
                    em.add_field(name="Developer Note",
                                 value="It looks like this entry may have multiple results, "
                                       "try and refine your search for better accuracy")

            else:
                em = discord.Embed(title=response[1]["title"], color=0xf8f9fa,
                               description= response[1]["content"])


            await self.client.embed(message.channel, em)
            return "Full article: <http://en.wikipedia.org/?curid=" + str(response[1]["id"]) + ">"

    async def xkcd(self, message):
        """
        Gets an xkcd. Random if number isn't specified
        !xkcd <optional: number>
        """
        args = self.cleanInput(message.content)
        target_number = 0
        try:
            indexresp = json.loads(requests.get("http://xkcd.com/info.0.json").content.decode())
        except requests.exceptions.ConnectionError:
            return "XKCD did not return a valid response. It may be down."
        except ValueError as e:
            return "XKCD response was missing data. Try again. [{}]".format(str(e))

        if args[0] != '':
            try:
                target_number = int(args[0])

            except ValueError:
                return "You must enter a **number** for a custom xkcd"
            else:
                if int(target_number) == 404:
                    return "Don't be that guy"

        else:
            number = indexresp["num"]
            target_number = randint(0, number)
            while target_number == 404:
                target_number = randint(0, number)

        try:
            if target_number != 0:
                resp = json.loads(requests.get("http://xkcd.com/{0}/info.0.json".format(target_number)).content.decode())
            else:
                resp = json.loads(requests.get("http://xkcd.com/info.0.json").content.decode())
            number = resp["num"]

        except requests.exceptions.ConnectionError:
            return "XKCD did not return a valid response. It may be down."
        except ValueError as e:
            return "XKCD response was missing data. Try again. [{}]".format(str(e))

        embed = discord.Embed(title= str(resp["num"]) + ". " + resp["safe_title"],
                              description="*" + resp["alt"] + "*",
                              color=0x96A8C8)
        embed.add_field(name="Date Published", value=resp["year"] + "-" + resp["month"] + "-" + resp["day"])

        await self.client.embed(message.channel, embed)
        return "link: " + resp["img"]

    async def lpromote(self, message, user=None):
        
        if user is None:
            await self.client.send_message(message.channel, "Who would you like to promote?")
            response = await self.client.wait_for_message(channel=message.channel, author=message.author, timeout=60)
            response = response.content
            user = self.getMember(message, response.strip())
            if response is None:
                return "Timed out after 1 minute..."

            if user is None:
                return "No user found for that name, try again"

        cb = self.config.get("choppingBlock")

        if user.id in cb:
            if (cb[user.id]["timeout"] - datetime.utcnow()).total_seconds() >= 0:
                if message.author.id not in cb[user.id]["votes"]:
                    cb[user.id]["votes"][message.author.id] = 1
                    return "You have voted to promote, " + user.name
                else:
                    return "You already voted..."
            else:
                return "The time to vote on this user has expired. Please run " + self.config.prefix\
                       + "lvalidate to add them to the roster"
        else:
            if self.hasRole(user, "Helping Hands"):
                return "This user is already a Helping Hands..."
            now = datetime.utcnow() + timedelta(days=2)
            cb[user.id] = {"votes": {message.author.id: 1}, "started_by": message.author.id,
                           "timeout": now}
            return "A vote to promote {0}#{1} has been started, it will end in 48 hours.".format(user.name,
                                                                                                 user.discriminator)\
                   + "\nYou man cancel this vote by running " + self.config.prefix \
                   + "lcancel (not to be confused with smash bros)"

    async def ldemote(self, message, user=None):
        if user is None:
            await self.client.send_message(message.channel, "Who would you like to demote?")
            response = await self.client.wait_for_message(channel=message.channel, author=message.author, timeout=60)
            response = response.content
            user = self.getMember(message, response.strip())
            if response is None:
                return "Timed out after 1 minute..."

            if user is None:
                return "No user found for that name, try again"

        cb = self.config.get("choppingBlock")
        if user.id in cb:
            if (cb[user.id]["timeout"] - datetime.utcnow()).total_seconds() >= 0:
                if message.author.id not in cb[user.id]["votes"]:
                    cb[user.id]["votes"][message.author.id] = -1
                    return "You have voted to demote, " + user.name
                else:
                    return "You already voted..."
            else:
                return "The time to vote on this user has expired. Please run " + self.config.prefix \
                       + "lvalidate to add them to the roster"
        else:
            if not self.hasRole(user, "Helping Hands"):
                return "This user is not a member of Helping Hands. I cannot demote them"
            now = datetime.utcnow() + timedelta(days=2)
            cb[user.id] = {"votes": {message.author.id: -1}, "started_by": message.author.id, "timeout": now}
            return "A vote to demote {0}#{1} has been started, it will end in 48 hours.".format(user.name,
                                                                                                user.discriminator) \
                   + "\nYou may cancel this vote by running " + self.config.prefix \
                   + "lcancel (not to be confused with smash bros)"

    async def lvote(self, message):
        """
        ITs back boooyyyysssss!!!!
        !lvote
        """
        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."

        if not self.hasRole(message.author, "Listener"):
            return "You must be a Listener to vote on Helping Hands"
        args = self.cleanInput(message.content)
        user = None
        if args[0] != '':
            user = self.getMember(message, args[0])
            if user is None:
                return "No member with that id..."

        while 1:
            await self.client.send_message(message.channel, "Are we calling to promote or demote?")
            response = await self.client.wait_for_message(channel=message.channel, author=message.author, timeout = 20)

            if response is None:
                return "You didn't reply so I timed out..."
            response = response.content
            if response.lower() in ['promote', 'p']:
                response = await self.lpromote(message, user)
                self.config.save()
                return response
            elif response.lower() in ['demote', 'd']:
                response = await self.ldemote(message, user)
                self.config.save()
                return response
            else:
                await self.client.send_message(message.channel, "Type promote or type demote [pd]")
                await asyncio.sleep(1)

    async def lcancel(self, message):
        """
        Cancels all lvotes you started. Does not validate them.
        !lcancel
        """
        cb = self.config.get("choppingBlock")
        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."

        if not self.hasRole(message.author, "Listener"):
            return "You are not a Listener You cannot use this feature"
        if cb is None:
            return "lvotes are disabled in config, why are you even running this command...?"

        temp = {}
        for entry in cb:
            try:
                if cb["started_by"] == message.author.id:
                    temp[entry] = cb[entry]
            except KeyError as e:
                temp[entry] = cb[entry]

        for e in temp:
            print("Deleted: " + str(self.config.doc["choppingBlock"][e]))
            del self.config.doc["choppingBlock"][e]

        self.config.save()
        return "Deleted all lvotes if you had started any"

    async def lvalidate(self, message, user=None):
        """
        Ends a vote and promotes/demotes user. Can be used prematurely
        !lvalidate <optional: tagged user>
        """

        cb = self.config.get("choppingBlock")

        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."
        if not self.hasRole(message.author, "Listener"):
            return "You are not a Listener You cannot use this feature"
        if user is None:
            await self.client.send_message(message.channel, "Which user would you like to validate?")
            response = await self.client.wait_for_message(channel=message.channel, author=message.author, timeout=60)
            response = response.content
            user = self.getMember(message, response.strip())
            if response is None:
                return "Timed out after 1 minute..."

            if user is None:
                return "No user found for that name, try again"

        if user.id not in cb:

            return "That user is not in the list, therefore I can't do anything. Here's a cat though.\n" + await self.cat(message)

        else:
            votelist = cb[user.id]["votes"]
            if len(votelist) < 2 :
                return "Not enough votes to pass, cancel the poll or wait longer. You may cancel with " \
                       + self.config.prefix + "lcancel"

            score = 0
            for entry in votelist:
                score += votelist[entry]

            if len(votelist) == 2 and score not in [-2, 2]:
                return "Not enough votes to promote/demote. Sorry, maybe discuss more. Or if this is an error," \
                       " let a manager/admin know"

            elif len(votelist) == 2 and score in [-2, 2]:
                if score == -2:
                    await self.client.remove_roles(user,
                                                   discord.utils.get(message.server.roles,
                                                                     name="Helping Hands"))
                    try:
                        await self.client.send_message(user,
                                                       "Following a vote by the listeners: "
                                                       "you have been demoted for the time being.")
                        del self.config.doc["choppingBlock"][user.id]
                        self.config.save()
                    except:
                        return "User could not be PM'd but they are a member of Helping Hands no more"
                    else:
                        return user.name + " has been removed from Helping Hands"
                else:
                    cb[user.id]["pending"] = True
                    cb[user.id]["server_id"] = message.server.id
                    cb[user.id]["channel_id"] = message.channel.id

                    try:
                        mop= await self.client.send_message(user,
                                                       "Following a vote by the listeners: you have been chosen "
                                                       "to be a Helping Hands! Reply !Laccept or !Lreject")

                    except:
                        return "User could not be PM'd but they are a now able to become a member of Helping Hands." \
                               "\nLet them know to type !Laccept or !Lreject in PMs in leaf"
                    else:
                        return user.name + " has been made a member of Helping Hands." \
                                           "\nThey must accept the invite by following the instruction I just sent them"

            else:
                avg = float(score / len(votelist))
                if -0.85 < avg < 0.85:
                    return "You need 85% of votes to pass current score:" + str(abs(avg * 100.00))

                elif avg < -0.85:
                    await self.client.remove_roles(user,
                                                   discord.utils.get(message.server.roles,
                                                                     name="Helping Hands"))
                    try:
                        await self.client.send_message(user,
                                                       "Following a vote by your fellow Helping Handss,"
                                                       " you have been demoted for the time being.")

                        del self.config.doc["choppingBlock"][user.id]
                        self.config.save()

                    except:
                        return "User could not be PM'd but they are a Helping Hands no more"
                    else:
                        return user.name + " has been removed from Helping Hands"

                elif avg > 0.85:
                    cb[user.id]["pending"] = True
                    try:
                        await self.client.send_message(user,
                                                       "Following a vote by your fellow members you have been chosen "
                                                       "to be a Helping Hands! Type !Laccept in any channel. "
                                                       "Or !Lreject if you wanna not become a Helping Hands")
                    except:
                        return "User could not be PM'd but they are a now able to become a Helping Hands." \
                               "\nLet them know to type !Laccept in a channel"
                    else:
                        return user.name + " has been made a Helping Hands!\nThey must accept" \
                                           " the invite by following the instruction I just sent them"

    async def laccept(self, message):
        """
        If you were voted to be a Helping Hands, running this command will accept the offer. Otherwise, run !Lreject
        !laccept
        """
        cb = self.config.get("choppingBlock")

        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."
        if not message.channel.is_private:
            return "You must reply only in PMs with petal. Not in a channel"
        if message.author.id in cb:
            if "pending" in cb[message.author.id]:
                svr = self.client.get_server(cb[message.author.id]["server_id"])
                if svr is None:
                    return "Error fetching server with ID: " + cb[message.author.id]["server_id"] + " ask who promoted you to do it manually"
                member = svr.get_member(message.author.id)
                await self.client.add_roles(member,
                                               discord.utils.get(svr.roles,
                                                                 name="Helping Hands"))

                chan = svr.get_channel(cb[message.author.id]["channel_id"])
                del self.config.doc["choppingBlock"][message.author.id]
                self.config.save()
                if chan is None:
                   return "You will need to tell them you have accepted as I could not notify them"
                else:
                    await self.client.send_message(chan, "Just letting y'all know that " + member.name + " has accepted their role")

                return "Welcome!"
            else:
                return "You don't have a pending invite to join the Helping Hands at this time"

    async def lreject(self, message):
        """
        If you were voted to be a Helping Hands, running this command will reject the offer.
        !lreject
        """
        cb = self.config.get("choppingBlock")

        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."

        if message.author.id in cb:
            if "pending" in cb[message.author.id]:

                    svr = self.client.get_server(cb[message.author.id]["server_id"])
                    if svr is not None:
                        chan = svr.get_channel(cb[message.author.id]["channel_id"])
                    else:
                        chan = None
                    if chan is None:
                        return "You will need to tell them you have accepted as I could not notify them"
                    else:
                        await self.client.send_message(chan,
                                                       "Just letting y'all know that " + message.author.name +
                                                       " has rejected their role")
                    del self.config.doc["choppingBlock"][message.author.id]
                    self.config.save()
                    return "You have rejected to join the helping hands. If this was on accident, let a listener know"
            else:
                return "You don't have a pending invite to join the Helping Handss at this time"

    async def lshow(self, message):
        """
       If you were voted to be a Helping Hands, running this command will reject the offer.
       !lreject
       """
        cb = self.config.get("choppingBlock")

        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."

        if not self.hasRole(message.author, "Listener"):
            return "You are not a Listener. You cannot use this feature"

        msg = ""
        for entry in cb:
            mem = self.getMember(message, entry)
            if mem is None:
                continue
            starter = self.getMember(message, cb[entry]["started_by"])
            if starter is None:
                continue
            msg += "\n------\nVote started by: "  + mem.name+ "\#" + mem.discriminator \
                   + "\nstarted by: " + starter.name + "#" + starter.discriminator + "\n------\n"

        return "Heres what votes are goin on: \n" + msg

    async def setosu(self, message):
        """
        Sets a users preferred osu account
        !setosu <name>
        """
        args = self.cleanInput(message.content)
        if args[0] == "":
            osu = message.author.name
        else:
            osu = args[0]

        if not self.db.useDB:
            return "Database is not enabled, so you can't save an osu name.\n" \
                   "You can still use !osu <osu name> though"


        self.db.update_member(message.author, {"osu": osu})

        return "You have set: " + osu + " as your preferred OSU account. " \
                                        "You can now run, !osu and it " \
                                        "will use this name automatically!"

    async def alias(self, message):
        """
        Returns a list of all previous names a user has had
        !alias <tag/id>
        """
        args = self.cleanInput(message.content)
        if args[0] == "":
            member = message.author
        else:
            member = self.getMember(message, args[0])

        if member is None:
            return "Couldn't find that member in the server\n\nJust a note, " \
                   "I may have record of them, but it's iso's policy to not " \
                   "display userinfo without consent. If you are staff and" \
                   " have a justified reason for this request. Please " \
                   "ask whomever hosts this bot to manually look up the" \
                   " records in their database"

        if not self.db.useDB:
            return "Database is not configured correctly (or at all). " \
                   "Contact your bot developer and tell them if you think" \
                   " this is an error"

        self.db.add_member(member)

        alias = self.db.get_attribute(member, "aliases")
        if len(alias) == 0:
            return "`This member has no aliases`"
        else:
            await self.client.send_message(message.channel,
                                           "__Aliases for "
                                           + member.id
                                           + "__")
            msg = ""

            for a in alias:
                msg += "**" + a + "**\n"

            return msg

    async def dumpvoid(self, message):
        """
        Owner reserved function
        This will dump every single void post in your PMs. It takes ~ 1.2-1.7 seconds per post so please wait

        """
        if not self.level0(message.author):
            return "You must be the bot owner to perform this"
        for i in self.db.void.find():
            try:
                msg = "Number **" + str(i["number"]) + "**\n Author: " + i["author"] + "\nTime Uploaded: " + str(i["time"]) + "\nContent: "+ i["content"]
            except KeyError:
                print(str(i) + " missing key")
                continue
            else:
                try:
                    await self.client.send_message(message.channel, msg)
                except discord.errors.HTTPException:
                    self.log.err("Possible empty message or overflow in void, printing here instead...")
                    self.log.info(msg)

            await asyncio.sleep(1)

    async def journal(self, message):
        """
        Volatile journal System. Allows users to write an entry that anyone can read later.
        !journal <entry> or !journal <user>
        """
        args = self.cleanInput(message.content)
        if args[0] == "":
            entry = self.db.get_attribute(message.author, "journal")
            if entry is None:
                return "*You peek into your own journal...*\n\n" + "But find nothing."
            return "*You peek into your own journal...*\n\nYou find:\n\n" + entry["content"]

        mem = self.getMember(message, args[0])
        if mem is not None:
            entry = self.db.get_attribute(mem, "journal")
            if entry is None:
                return "*You peek into {}'s journal...*\n\n".format(mem.name) + "But find nothing"
            return "*You peek into {}'s journal...*\n\nYou find:\n\n".format(mem.name) + entry["content"]
        entry = self.db.update_member(message.author,
                                      data={"journal": {"content": args[0], "time": str(datetime.utcnow())}})

        return "Your journal has been updated. Anyone can read it with " + message.author.mention


