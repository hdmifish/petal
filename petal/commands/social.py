"""Commands module for SOCIAL MEDIA UTILITIES.
Access: Role-based"""

import asyncio

import facebook
from praw.exceptions import APIException

from . import core


class CommandsSocial(core.Commands):
    auth_fail = "This command requires the Social Media role."

    def authenticate(self, src):
        return self.check_user_has_role(src.author, self.config.get("socialMediaRole"))

    @staticmethod
    def validate_channel(chanlist, msg):
        for i in range(len(msg.content)):
            try:
                chanlist[int(msg.content[int(i)])]
            except AttributeError:
                return False
        return True

    async def update(self, src, **_):
        """
        >update
        Post updates to social media
        """
        modes = []
        names = []
        using = []

        if self.config.get("reddit") is not None:
            names.append(str(len(modes)) + " reddit")
            modes.append(self.router.reddit)
            using.append("reddit")

        if self.config.get("twitter") is not None:
            names.append(str(len(modes)) + " twitter")
            modes.append(self.router.twit)
            using.append("twitter")

        if self.config.get("facebook") is not None:
            names.append(str(len(modes)) + " facebook")
            modes.append(self.router.fb)
            using.append("facebook")

        if self.config.get("tumblr") is not None:
            names.append(str(len(modes)) + " tumblr")
            modes.append(self.router.tumblr)
            using.append("tumblr")

        if len(modes) == 0:
            return "No modules enabled for social media posting"

        await self.client.send_message(
            src.author,
            src.channel,
            "Hello, "
            + src.author.name
            + " here are the enabled social media "
            + "services \n"
            + "\n".join(names)
            + "\n\n Please select which ones you "
            + "want to use (e.g. 023) ",
        )

        sendto = await self.client.wait_for_message(
            channel=src.channel,
            author=src.author,
            check=str.isnumeric,
            timeout=20,
        )
        if sendto is None:
            return "The process timed out, please enter a valid string of numbers"
        if not self.validate_channel(modes, sendto):
            return "Invalid selection, please try again"

        await self.client.send_message(
            src.author,
            src.channel,
            "Please type a title for your post (timeout after 1 minute)",
        )
        mtitle = await self.client.wait_for_message(
            channel=src.channel, author=src.author, timeout=60
        )
        if mtitle is None:
            return "The process timed out, you need a valid title"
        await self.client.send_message(
            src.author,
            src.channel,
            "Please type the content of the post "
            + "below. Limit to 140 characters for "
            + "twitter posts (this process will "
            + "time out after 2 minutes)",
        )
        mcontent = await self.client.wait_for_message(
            channel=src.channel, author=src.author, timeout=120
        )

        if mcontent is None:
            return "The process timed out, you need content to post"

        if "1" in sendto.content:
            if len(mcontent.content) > 280:
                return "This post is too long for twitter"

        await self.client.send_message(
            src.author,
            src.channel,
            "Your post is ready. Please type: `send`",
        )
        meh = await self.client.wait_for_message(
            channel=src.channel, author=src.author, content="send", timeout=10
        )
        if meh is None:
            return "Timed out, message not send"
        if "0" in sendto.content:
            sub1 = self.router.reddit.subreddit(self.config.get("reddit")["targetSR"])
            try:
                response = sub1.submit(
                    mtitle.content, selftext=mcontent.clean_content, send_replies=False
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

        if "1" in sendto.content:
            self.router.twit.PostUpdate(mcontent.clean_content)
            await self.client.send_message(
                src.author, src.channel, "Submitted tweet"
            )
            await asyncio.sleep(2)

        if "2" in sendto.content:

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
            #     status = postpage.put_wall_post(mcontent.clean_content)
            #     await self.client.send_message(
            #         src.author,
            #         src.channel,
            #         "Posted to facebook under page: " + page["name"],
            #     )
            #     self.log.f("smupdate", "Facebook Response: " + str(status))
            #     await asyncio.sleep(2)

        if "3" in sendto.content:
            self.router.tumblr.create_text(
                self.config.get("tumblr")["targetBlog"],
                state="published",
                slug="post from petalbot",
                title=mtitle.content,
                body=mcontent.clean_content,
            )

            await self.client.send_message(
                src.author,
                src.channel,
                "Posted to tumblr: " + self.config.get("tumblr")["targetBlog"],
            )

        return "Done posting"


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsSocial
