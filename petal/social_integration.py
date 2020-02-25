"""This module provides a class framework that establishes integrations between
    the CommandRouter and Social Media APIs.

It exists solely to be subclassed by CommandRouter to keep the code clean.
"""

from datetime import datetime as dt

import discord
import facebook
import praw
import pytumblr
import twitter

from petal.grasslands import Giraffe, Octopus, Peacock


class Integrated:
    def __init__(self, client):
        self.client = client
        self.config = client.config
        self.log = Peacock()

        key_osu = self.config.get("osu")
        if key_osu:
            self.osu = Octopus(key_osu)
        else:
            self.osu = None
            self.log.warn("No OSU! key found.")

        key_imgur = self.config.get("imgur")
        if key_imgur:
            self.imgur = Giraffe(key_imgur)
        else:
            self.imgur = None
            self.log.warn("No imgur key found.")

        reddit = self.config.get("reddit")
        if reddit:
            self.reddit = praw.Reddit(
                client_id=reddit["clientID"],
                client_secret=reddit["clientSecret"],
                user_agent=reddit["userAgent"],
                username=reddit["username"],
                password=reddit["password"],
            )
            if self.reddit.read_only:
                self.log.warn(
                    "This account is in read only mode. "
                    + "You may have done something wrong. "
                    + "This will disable reddit functionality."
                )
                self.reddit = None
                return
            else:
                self.log.ready("Reddit support enabled!")
        else:
            self.reddit = None
            self.log.warn("No Reddit keys found")

        tweet = self.config.get("twitter")
        # Twitter support disabled till api fix
        if tweet and False:
            self.twit = twitter.Api(
                consumer_key=tweet["consumerKey"],
                consumer_secret=tweet["consumerSecret"],
                access_token_key=tweet["accessToken"],
                access_token_secret=tweet["accessTokenSecret"],
                tweet_mode="extended",
            )
            if "id" not in str(self.twit.VerifyCredentials()):
                self.log.warn(
                    "Your Twitter authentication is invalid, "
                    + " Twitter posting will not work"
                )
                self.twit = None
                return
        else:
            self.twit = None
            self.log.warn("No Twitter keys found.")

        fb = self.config.get("facebook")
        if fb:
            self.fb = facebook.GraphAPI(
                access_token=fb["graphAPIAccessToken"], version=fb["version"]
            )
        else:
            self.fb = None
            self.log.warn("No Facebook keys found.")

        tumblr = self.config.get("tumblr")
        if tumblr:
            self.tumblr = pytumblr.TumblrRestClient(
                tumblr["consumerKey"],
                tumblr["consumerSecret"],
                tumblr["oauthToken"],
                tumblr["oauthTokenSecret"],
            )
            self.log.ready("Tumblr support Enabled!")
        else:
            self.tumblr = None
            self.log.warn("No Tumblr keys found.")

    @staticmethod
    def get_member_name(guild, member):
        try:
            m = guild.get_member(member).name
            if m is None:
                m = member
        except AttributeError:
            m = member

        return m

    async def check_pa_updates(self, force=False):
        if force:
            self.config.doc["lastRun"] = dt.utcnow()
            self.config.save()

        else:
            last_run = self.config.get("lastRun")
            self.log.f("pa", "Last run at: " + str(last_run))
            if last_run is None:
                last_run = dt.utcnow()
                self.config.doc["lastRun"] = last_run
                self.config.save()
            else:
                difference = (
                    dt.utcnow() - dt.strptime(str(last_run), "%Y-%m-%d %H:%M:%S.%f")
                ).total_seconds()
                self.log.f("pa", "Difference: " + str(difference))
                if difference < 86400:
                    return
                else:
                    self.config.doc["lastRun"] = dt.utcnow()
                    self.config.save()

        self.log.f("pa", "Searching for entries...")
        response = self.client.db.get_motd_entry(update=True)

        if response is None:
            if force:
                return "Could not find suitable entry, make sure you have added questions to the DB"

            self.log.f("pa", "Could not find suitable entry")

        else:
            try:
                em = discord.Embed(
                    title="Patch Asks",
                    description="Today Patch asks: \n " + response["content"],
                    colour=0x0ACDFF,
                )

                msg = await self.client.embed(
                    self.client.get_channel(self.config.get("motdChannel")), em
                )

                await self.client.send_message(
                    msg.author,
                    msg.channel,
                    "*today's question was "
                    + "written by "
                    + self.get_member_name(msg.guild, response["author"])
                    + "*",
                )
                self.log.f(
                    "pa",
                    "Going with entry: "
                    + str(response["num"])
                    + " by "
                    + self.get_member_name(msg.guild, response["author"]),
                )

            except KeyError:
                self.log.f("pa", "Malformed entry, dumping: " + str(response))
