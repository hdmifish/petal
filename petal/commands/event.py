"""Commands module for EVENTS UTILITIES.
Access: Role-based"""

from petal.commands import core


class CommandsEvent(core.Commands):
    auth_fail = "This command requires the Events role."

    def authenticate(self, src):
        return self.check_user_has_role(src.author, self.config.get("xPostRole"))

    async def event(self, src, **_):
        """
        Dialog-styled event poster
        >event
        """
        if not self.check_user_has_role(
            src.author, self.config.get("xPostRole")
        ) and not self.level4(src.author):

            return (
                "You need the: "
                + self.config.get("xPostRole")
                + " role to use this command"
            )

        chanList = []
        msg = ""
        for chan in self.config.get("xPostList"):
            channel = self.client.get_channel(chan)
            if channel is not None:
                msg += (
                    str(len(chanList))
                    + ". ("
                    + channel.name
                    + " [{}]".format(channel.server.name)
                    + ")\n"
                )
                chanList.append(channel)
            else:
                self.log.warn(
                    chan + " is not a valid channel. " + " I'd remove it if I were you."
                )

        while True:
            await self.client.send_message(
                src.author,
                src.channel,
                "Hi there, "
                + src.author.name
                + "! Please select the number of "
                + " each server you want to post "
                + " to. (dont separate the numbers) ",
            )

            await self.client.send_message(src.author, src.channel, msg)

            chans = await self.client.wait_for_message(
                channel=src.channel,
                author=src.author,
                check=self.check_is_numeric,
                timeout=20,
            )

            if chans is None:
                return (
                    "Sorry, the request timed out. Please make sure you"
                    + " type a valid sequence of numbers"
                )
            if self.validate_channel(chanList, chans):
                break
            else:
                await self.client.send_message(
                    src.author, src.channel, "Invalid channel choices"
                )
        await self.client.send_message(
            src.author,
            src.channel,
            "What do you want to send?" + " (remember: {e} = @ev and {h} = @her)",
        )

        msg = await self.client.wait_for_message(
            channel=src.channel, author=src.author, timeout=120
        )

        msgstr = msg.content.format(e="@everyone", h="@here")

        toPost = []
        for i in chans.content:
            print(chanList[int(i)])
            toPost.append(chanList[int(i)])

        channames = []
        for i in toPost:
            channames.append(i.name + " [" + i.server.name + "]")

        embed = discord.Embed(
            title="Message to post", description=msgstr, colour=0x0ACDFF
        )

        embed.add_field(name="Channels", value="\n".join(channames))

        await self.client.embed(src.channel, embed)
        await self.client.send_message(
            src.author,
            src.channel,
            "If this is ok, type confirm. "
            + " Otherwise, wait for it to timeout "
            + " and try again",
        )

        msg2 = await self.client.wait_for_message(
            channel=src.channel,
            author=src.author,
            content="confirm",
            timeout=10,
        )
        if msg2 is None:
            return "Event post timed out"

        posted = []
        for i in toPost:
            posted.append(await self.client.send_message(src.author, i, msgstr))
            await asyncio.sleep(2)

        await self.client.send_message(
            src.author, src.channel, "Messages have been posted"
        )

        subkey, friendly = self.get_event_subscription(msgstr)

        if subkey is None:
            await self.client.send_message(
                src.author,
                src.channel,
                "I was unable to auto-detect "
                + "any game titles in your post. "
                + "No subscribers will not be notified for this event.",
            )
        else:
            tempm = await self.client.send_message(
                src.author,
                src.channel,
                "I auto-detected a possible game in your announcement: **"
                + friendly
                + "**. Would you like to notify subscribers?[yes/no]",
            )
            n = await self.client.wait_for_message(
                channel=tempm.channel,
                author=src.author,
                check=self.check_yes_no,
                timeout=20,
            )
            if n is None:
                return "Timed out..."

            if n.content == "yes":
                response = await self.notify_subscribers(
                    src.channel, posted[0], subkey
                )
                todelete = "[{}]".format(subkey)
                ecount = 0
                for post in posted:
                    content = post.content
                    #    print(content)
                    #    print(todelete)
                    if todelete in content:
                        # print("replacing")
                        content = content.replace(todelete, "")
                        # print("replaced: " + content)
                        await self.client.edit_message(post, content)

                return response


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsEvent
