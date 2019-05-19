"""Commands module for EVENTS UTILITIES.
Access: Role-based"""

import asyncio

import discord

from petal.checks import all_checks, Messages
from petal.commands import core
from petal.menu import Menu


class CommandsEvent(core.Commands):
    auth_fail = "This command requires the `{role}` role."
    role = "xPostRole"

    async def cmd_event(
        self, src, _image: str = None, _message: str = None, _nomenu: bool = False, **_
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
            menu = None
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

                chans = await Messages.waitfor(
                    self.client,
                    all_checks(
                        Messages.by_user(src.author), Messages.in_channel(src.channel)
                    ),
                    timeout=20,
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
            # Use the Reaction-based GUI.
            menu = Menu(
                self.client,
                src.channel,
                "Event Announcement Post (by {})".format(src.author.display_name),
                "Use the Reaction Buttons to fill out the Announcement.",
                user=src.author,
            )
            if _image:
                menu.em.set_thumbnail(_image)
            selection = await menu.get_multi(
                list(channels_dict), title="Target Channels"
            )
            post_to = [channels_dict[c] for c in selection if c in channels_dict]
            if not post_to:
                # menu.add_section(
                #     "No valid target channels selected; Post canceled.", "Verdict"
                # )
                # await menu.close("No valid target channels selected; Post canceled.")
                menu.add_section(
                    "No Channels selected; Cancelled.", "Target Channels", overwrite=-1
                )
                await menu.post()
                return
            menu.add_section(
                "\n".join([c.mention for c in post_to]), "Target Channels", overwrite=-1
            )
            await menu.post()

        msgstr = (
            _message
            or (
                await Messages.waitfor(
                    self.client,
                    all_checks(
                        Messages.by_user(src.author), Messages.in_channel(src.channel)
                    ),
                    timeout=120,
                    channel=src.channel,
                    prompt="What do you want to send? (remember: {e} = `@ev` and {h} = `@here`)",
                )
            ).content
        ).format(e="@everyone", h="@here")

        if _nomenu:
            embed = discord.Embed(
                title="Message to post", description=msgstr, colour=0x0ACDFF
            )
            embed.add_field(
                name="Channels", value="\n".join([c.mention for c in post_to])
            )
            await self.client.embed(src.channel, embed)

            msg2 = await Messages.waitfor(
                self.client,
                all_checks(
                    Messages.by_user(src.author), Messages.in_channel(src.channel)
                ),
                timeout=20,
                channel=src.channel,
                prompt="If this is correct, type `confirm`.",
            )

            if msg2 is None:
                return "Event post timed out."
            elif msg2.content.lower() != "confirm":
                return "Event post cancelled."
        else:
            # confirmer = Menu(self.client, src.channel, "Confirm Post", user=src.author)
            menu.add_section(msgstr, "Message Preview")
            proceed = await menu.get_bool(
                prompt="Send this Event Announcement?", title="Confirmation"
            )
            if proceed is None:
                # menu.em.description = "[ Closed ]"
                menu.add_section("Posting timed out.", "Confirmation", overwrite=-1)
                return
            elif proceed is not True:
                # menu.em.description = "[ Closed ]"
                menu.add_section("Posting cancelled.", "Confirmation", overwrite=-1)
                return

        posted = []
        # TODO
        # em = discord.Embed()
        # if _image:
        #     em.set_image(url=_image)
        for i in post_to:
            posted.append(await i.send(msgstr))
            await asyncio.sleep(1)

        if menu:
            menu.add_section("Messages have been posted.", "Confirmation", overwrite=-1)
            await menu.post()
        else:
            # menu.em.description = "[ Closed ]"
            await self.client.send_message(
                src.author, src.channel, "Messages have been posted."
            )

        try:
            subkey, subname = self.get_event_subscription(msgstr)
        except AttributeError:
            pass
        else:
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
                    response = await self.notify_subscribers(
                        src.channel, posted[0], subkey
                    )
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
