"""Commands module for SOCIAL MEDIA UTILITIES.
Access: Role-based"""

import asyncio
import requests

import discord
import facebook
from twitter import error as twitterror
from praw.exceptions import APIException

from petal.commands import core
from petal.menu import Menu
from petal.util.grammar import sequence_words


class CommandsSocial(core.Commands):
    auth_fail = "This command requires the `{role}` role."
    role = "socialMediaRole"

    async def cmd_update(
        self,
        src,
        _title="",
        _content="",
        _platform="",
        _reddit=False,
        _twitter=False,
        _fb=False,
        _tumblr=False,
        **_
    ):
        """
        Post updates to various Social Media accounts.

        Syntax: `{p}update [OPTIONS]`

        Options:
        `--title="<title>"` :: Set the post title. Only matters for Reddit and Tumblr. Asked for if not provided.
        `--content="<content>"` :: Fill in the post content. This is the long bit. Asked for if not provided.
        `--platform=<0,1,2,3>` :: Old style numeric platform selection. Exactly the same as what is asked for if not provided.
        `--reddit`, `--twitter`, `--fb`, `--tumblr` :: Determine which platform(s) to post to. Alternative to `--platform`.
        """
        modes = []
        names = []
        using = []
        table = {
            "reddit": self.router.reddit,
            "twitter": self.router.twit,
            "facebook": self.router.fb,
            "tumblr": self.router.tumblr,
        }
        flagged = ""
        if _reddit:
            flagged += "0"
        if _twitter:
            flagged += "1"
        if _fb:
            flagged += "2"
        if _tumblr:
            flagged += "3"

        if table["reddit"]:
            names.append(str(len(modes)) + " reddit")
            modes.append(self.router.reddit)
            using.append("reddit")

        if table["twitter"]:
            names.append(str(len(modes)) + " twitter")
            modes.append(self.router.twit)
            using.append("twitter")

        if table["facebook"]:
            names.append(str(len(modes)) + " facebook")
            modes.append(self.router.fb)
            using.append("facebook")

        if table["tumblr"]:
            names.append(str(len(modes)) + " tumblr")
            modes.append(self.router.tumblr)
            using.append("tumblr")

        if not modes:
            return "No modules enabled for social media posting."

        if True not in (_reddit, _twitter, _fb, _tumblr) and _platform == "":
            # No destinations have been sent as a flag. Ask the user.
            sendto = ""
            ui = Menu(
                self.client,
                src.channel,
                "Select platform(s) to publish on.",
                user=src.author,
            )
            await ui.post()

            platforms = await ui.get_multi(using)
            platforms.sort()
            ui.em.description += "\nSelection: " + sequence_words(
                [x.capitalize() for x in platforms]
            )
            await ui.post()

            for i, name in enumerate(using):
                if name in platforms:
                    sendto += str(i)
            if not sendto:
                await ui.close()
                return "Cancelled"
        else:
            sendto = flagged + _platform

        # Check whether sendto contains anything illegal.
        if sendto.strip("0123") != "":
            return "Invalid platform set, please try again."

        if not _title:
            # A title has not been sent as a flag. Ask the user.
            await self.client.send_message(
                src.author,
                src.channel,
                "Please type a title for your post (timeout after 1 minute).",
            )
            _title = await self.client.wait_for_message(
                channel=src.channel, author=src.author, timeout=60
            )
            if _title is None:
                return "The process timed out, you need a valid title."
            _title = _title.content

        if not _content:
            # Post content has not been sent as a flag. Ask the user.
            await self.client.send_message(
                src.author,
                src.channel,
                "Please type the content of the post "
                + "below. Limit to 280 characters for "
                + "Twitter posts. This process will "
                + "time out after 2 minutes.",
            )
            _content = await self.client.wait_for_message(
                channel=src.channel, author=src.author, timeout=120
            )

            if _content is None:
                return "The process timed out, you need content to post."
            _content = _content.content

        # Make sure this would not be an overly long tweet.
        if "1" in sendto:
            if len(_content) > 280:
                return "This post is {} characters too long for Twitter.".format(
                    len(_content) - 280
                )

        # Get final confirmation before sending.
        await self.client.send_message(
            src.author,
            src.channel,
            "Your post is ready. Please type `send` to confirm.",
        )
        confirm = await self.client.wait_for_message(
            channel=src.channel, author=src.author, content="send", timeout=10
        )
        if confirm.content.lower() != "send":
            return "Timed out, message not sent."

        # return str([flagged, sendto, platform, title, content])

        # Post to Reddit
        if "0" in sendto.content:
            sub1 = self.router.reddit.subreddit(self.config.get("reddit")["targetSR"])
            try:
                response = sub1.submit(
                    _title.content, selftext=_content.clean_content, send_replies=False
                )
                self.log.f("smupdate", "Reddit Response: " + str(response))
            except APIException:
                await self.client.send_message(
                    src.author,
                    src.channel,
                    "The post did not send, "
                    + "this key has been "
                    + "ratelimited. Please wait for"
                    + " about 8-10 minutes before "
                    + "posting again",
                )
            else:
                await self.client.send_message(
                    src.author,
                    src.channel,
                    "Submitted post to " + self.config.get("reddit")["targetSR"],
                )
                await asyncio.sleep(2)

        # Post to Twitter
        if "1" in sendto:
            self.router.twit.PostUpdate(_content.clean_content)
            await self.client.send_message(src.author, src.channel, "Submitted tweet")
            await asyncio.sleep(2)

        # Post to Facebook
        if "2" in sendto:
            # Setting up facebook takes a bit of digging around to see how
            # their API works. Basically you have to be admin'd on a page
            # and have its ID as well as generate an OAUTH2 long-term key.
            # Facebook python API was what I googled

            resp = self.router.fb.get_object("me/accounts")
            page_access_token = None
            for page in resp["data"]:
                if page["id"] == self.config.get("facebook")["pageID"]:
                    page_access_token = page["access_token"]
            postpage = facebook.GraphAPI(page_access_token)

            # if postpage is None:
            #     await self.client.send_message(
            #         src.author,
            #         src.channel,
            #         "Invalid page id for " + "facebook, will not post",
            #     )
            # else:
            #     # FIXME: 'postpage.put_wall_post' and 'page' are invalid
            #     # Did you mean to put them in the loop above?
            #     status = postpage.put_wall_post(body.clean_content)
            #     await self.client.send_message(
            #         src.author,
            #         src.channel,
            #         "Posted to facebook under page: " + page["name"],
            #     )
            #     self.log.f("smupdate", "Facebook Response: " + str(status))
            #     await asyncio.sleep(2)

        # Post to Tumblr
        if "3" in sendto:
            self.router.tumblr.create_text(
                self.config.get("tumblr")["targetBlog"],
                state="published",
                slug="post from petalbot",
                title=_title.content,
                body=_content.clean_content,
            )

            await self.client.send_message(
                src.author,
                src.channel,
                "Posted to tumblr: " + self.config.get("tumblr")["targetBlog"],
            )

        return "Done posting"

    async def cmd_retweet(self, args, src, **_):
        """Retweet on behalf of the twitter account linked to Petal.

        Syntax: `{p}retweet <tweet_id>`
        """
        if not args:
            return "You cant retweet nothing, silly :P"

        if not args[0].isnumeric():
            return "Retweet ID must only be numbers"

        try:
            response = self.router.twit.PostRetweet(int(args[0]), trim_user=True)

            self.log.f("TWEET", src.author.name + " posted a retweet!")
            status = response.AsDict()
            #            print("Stats: " + str(status))
            #            if str(status) == "[{'code': 327, 'message': 'You have already retweeted this Tweet.'}]":
            #                return "We've already retweeted this tweet"
            user = self.router.twit.GetUser(
                user_id=status["user_mentions"][0]["id"]
            ).AsDict()

            embed = discord.Embed(
                title="Re-tweeted from: " + status["user_mentions"][0]["name"],
                description=status["retweeted_status"]["text"],
                colour=0x1DA1F2,
            )
            #            print(user['profile_image_url'])
            embed.set_author(
                name=user["screen_name"], icon_url=user["profile_image_url"]
            )
            #            embed.add_field(name="Screen Name", value=status['user_mentions'][0]['screen_name'])
            embed.add_field(name="Created At", value=status["created_at"])
            rtc = status["retweet_count"]
            if rtc == 1:
                suf = " time"
            else:
                suf = " times"
            embed.add_field(name="Retweeted", value=str(rtc) + suf)
            await self.client.embed(src.channel, embedded=embed)
        except twitterror.TwitterError as e:
            print("ex:" + str(e))
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
            }
            res = requests.get("http://aws.random.cat/meow", headers=headers).json()[
                "file"
            ]
            return (
                "Oh :(. Im sorry to say that you've made a goof. As it turns out, we already retweeted this tweet. I'm sure the author would appreciate it if they knew you tried to retweet their post twice! It's gonna be ok though, we'll get through this. Hmmmm.....hold on, I have an idea.\n\n\nHere: "
                + res
            )
        else:
            return "Successfully retweeted!"


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsSocial
