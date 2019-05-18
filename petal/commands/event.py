"""Commands module for EVENTS UTILITIES.
Access: Role-based"""

import asyncio

import discord

from petal.commands import core
from petal.menu import Menu


class CommandsEvent(core.Commands):
    auth_fail = "This command requires the `{role}` role."
    role = "xPostRole"

    async def cmd_event(
        self, src, _message: str = "", _channels: str = "", _nomenu: bool = False, **_
    ):
        """Post a message announcing the start of an event.

        Define a message which will be sent to one or more predefined channels. The message may include mass pings by way of including tags `{{e}}` and `{{h}}` for substitution.
        Destination channels may be selected conversationally or by way of a reaction-based menu.

        Options:
        `--message=<msg>` :: Define the message to send ahead of time. This will skip the step where Petal asks you what you want the message to say.
        `--nomenu` :: Forsake the Reaction UI and determine destination channels conversationally.
        """
        channels_list = []
        channels_dict = {}
        msg = ""
        for chan in self.config.get("xPostList"):
            channel = self.client.get_channel(chan)
            if channel is not None:
                msg += (
                    str(len(channels_list))
                    + ". ("
                    + channel.name
                    + " [{}]".format(channel.guild.name)
                    + ")\n"
                )
                channels_list.append(channel)
                channels_dict[channel.guild.name + "/#" + channel.name] = channel
            else:
                self.log.warn(
                    chan + " is not a valid channel. I'd remove it if I were you."
                )

        # Get channels to send to.
        if _nomenu:
            # Do it only conversationally.
            while True:
                await self.client.send_message(
                    src.author,
                    src.channel,
                    "Hi there, "
                    + src.author.name
                    + "! Please select the number of "
                    + "each guild you want to post "
                    + "to. (dont separate the numbers)",
                )

                await self.client.send_message(src.author, src.channel, msg)

                chans = await self.client.wait_for_message(
                    channel=src.channel, author=src.author, timeout=20
                )

                if chans is None:
                    return (
                        "Sorry, the request timed out. Please make sure you"
                        + " type a valid sequence of numbers."
                    )
                if self.validate_channel(channels_list, chans.content):
                    break
                else:
                    await self.client.send_message(
                        src.author,
                        src.channel,
                        "Invalid channel choices. You may try again immediately.",
                    )
            post_to = []
            for i in chans.content:
                print(channels_list[int(i)])
                post_to.append(channels_list[int(i)])
        else:
            # Use the ReactionUI.
            menu = Menu(
                self.client,
                src.channel,
                "Where shall the message be posted?",
                user=src.author,
            )
            selection = await menu.get_multi(
                list(channels_dict), prompt="Select one or more Target Channels."
            )
            if not selection:
                return "No target channels selected; Post canceled."
            post_to = [channels_dict[c] for c in selection]

        await self.client.send_message(
            src.author,
            src.channel,
            "What do you want to send? (remember: {e} = `@ev` and {h} = `@here`)",
        )

        msgstr = (
            _message
            or (
                await self.client.wait_for_message(
                    channel=src.channel, author=src.author, timeout=120
                )
            ).content
        ).format(e="@everyone", h="@here")

        embed = discord.Embed(
            title="Message to post", description=msgstr, colour=0x0ACDFF
        )

        embed.add_field(name="Channels", value="\n".join([c.mention for c in post_to]))

        await self.client.embed(src.channel, embed)
        await self.client.send_message(
            src.author,
            src.channel,
            "If this is ok, type confirm. "
            + " Otherwise, wait for it to timeout "
            + " and try again",
        )

        msg2 = await self.client.wait_for_message(
            channel=src.channel, author=src.author, content="confirm", timeout=10
        )
        if msg2 is None:
            return "Event post timed out"

        posted = []
        for i in post_to:
            posted.append(await self.client.send_message(src.author, i, msgstr))
            await asyncio.sleep(2)

        await self.client.send_message(
            src.author, src.channel, "Messages have been posted"
        )

        subkey, subname = self.get_event_subscription(msgstr)

        if subkey is None:
            await self.client.send_message(
                src.author,
                src.channel,
                "I was unable to auto-detect any game titles in your post. "
                + "No subscribers will be notified for this event.",
            )
        else:
            tempm = await self.client.send_message(
                src.author,
                src.channel,
                "I auto-detected a possible game in your announcement: **"
                + subname
                + "**. Would you like to notify subscribers? [y/N]",
            )
            n = await self.client.wait_for_message(
                channel=tempm.channel, author=src.author, timeout=20
            )
            if not n:
                return "Timed out."
            elif n.content.lower() not in ("y", "yes"):
                return "Subscribers will not be notified."
            else:
                response = await self.notify_subscribers(src.channel, posted[0], subkey)
                todelete = "[{}]".format(subkey)
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
