"""Commands module for EVENTS UTILITIES.
Access: Role-based"""

import asyncio
from typing import List

import discord

from petal.checks import all_checks, Messages
from petal.commands import core, shared
from petal.exceptions import CommandOperationError
from petal.menu import Menu
from petal.types import Src
from petal.util.embeds import Color
from petal.util.questions import ChatReply


class CommandsEvent(core.Commands):
    auth_fail = "This command requires the `{role}` role."
    role = "xPostRole"

    async def cmd_shiftcategory(
            self, args, src: Src, **_):
        return_channel: discord.TextChannel = src.channel
        event_group_id = self.config.get("eventCategory")
        main_chat_id = self.config.get("mainChatCategory")
        default_position = self.config.get("defaultEventChannelPosition")
        event_group: discord.CategoryChannel = self.client.main_guild.get_channel(event_group_id)
        main_chat: discord.CategoryChannel = self.client.main_guild.get_channel(main_chat_id)
        self.log.info(f"Main Chat position is: {main_chat.position}")
        self.log.info(f"Current event chat position is: {event_group.position}")

        if event_group.position > main_chat.position:
            await event_group.move(before=main_chat)
            await return_channel.send(content=f"{event_group.name} was moved right above {main_chat.name}")
        else:
            await event_group.edit(position=default_position)
            await return_channel.send(content=f"{event_group.name} was moved back to its default position ({default_position})")

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
                    f"{len(channels_list)}. ({channel.name} [{channel.guild.name}])\n"
                )
                channels_list.append(channel)
                channels_dict[channel.guild.name + "/#" + channel.name] = channel
            else:
                self.log.warn(
                    f"{chan} is not a valid channel. I'd remove it if I were you."
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
                    raise CommandOperationError(
                        "Sorry, the request timed out. Please make sure you"
                        " type a valid sequence of numbers."
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
            menu = Menu(self.client, src.channel, "Event Announcement", user=src.author)
            if _image:
                menu.em.set_thumbnail(url=_image)
            selection = await menu.get_multi(
                list(channels_dict), title="Available Channels"
            )
            post_to = [channels_dict[c] for c in selection if c in channels_dict]
            if not post_to:
                menu.add_section("No Channels selected; Cancelled.", "Target Channels")
                await menu.post()
                return
            menu.add_section("\n".join(c.mention for c in post_to), "Target Channels")
            await menu.post()

        msgstr = yield ChatReply(
            "What do you want to send? (remember: {e} = `@ev` and {h} = `@here`)",
            120,
        )
        if not msgstr:
            # No reply.
            raise CommandOperationError("Text Input timed out.")

        try:
            msgstr = msgstr.format(e="@everyone", h="@here")
        except Exception as e:
            # Given a bad Format tag.
            raise CommandOperationError(
                "Could not perform `format()`. Make sure you did the braces"
                " around any `{e}`s or `{h}`s correctly."
                "\n(Any other braces in the message should be {{doubled}}.)"
            ) from e

        if _nomenu:
            embed = discord.Embed(
                title="Message to post", description=msgstr, colour=Color.info
            )
            embed.add_field(
                name="Channels", value="\n".join(c.mention for c in post_to)
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
                raise CommandOperationError("Event post timed out.")
            elif msg2.content.lower() != "confirm":
                raise CommandOperationError("Event post cancelled.")
        else:
            menu.add_section(msgstr, "Confirm Message")
            await menu.post()
            proceed = await menu.get_bool()
            if proceed is None:
                menu.add_section("Posting timed out.", "Confirmation")
                await menu.post()
                return
            elif proceed is not True:
                menu.add_section("Posting cancelled.", "Confirmation")
                await menu.post()
                return

        posted: List[discord.Message] = []
        # TODO
        # em = discord.Embed()
        # if _image:
        #     em.set_image(url=_image)
        for i in post_to:
            posted.append(await i.send(msgstr))
            await asyncio.sleep(1)

        if menu:
            menu.add_section("Messages have been posted.", "Confirmation")
            await menu.post()
        else:
            yield "Messages have been posted."

        try:
            subkey, subname = self.get_event_subscription(msgstr)
        except AttributeError:
            pass
        else:
            if subkey is None:
                yield (
                    "I was unable to auto-detect any game titles in your post."
                    " No subscribers will be notified for this event."
                )
            else:
                n = await Messages.waitfor(
                    self.client,
                    all_checks(
                        Messages.by_user(src.author), Messages.in_channel(src.channel)
                    ),
                    timeout=20,
                    channel=src.channel,
                    prompt=f"I auto-detected a possible game in your announcement:"
                    f" **{subname}**. Would you like to notify subscribers? [y/N]",
                )

                if not n:
                    yield "Timed out."
                elif n.content.lower() not in ("y", "yes"):
                    yield "Subscribers will not be notified."
                else:
                    response = await self.notify_subscribers(
                        src.channel, posted[0], subkey
                    )
                    todelete = f"[{subkey}]"
                    for post in posted:
                        content = post.content
                        if todelete in content:
                            content = content.replace(todelete, "")
                            await post.edit(content=content)

                    yield response

    cmd_send = shared.factory_send(
        {
            "events": {"colour": 0x1B6649, "title": "Event Announcement"},
            "staff": {"colour": 0x4CCDDF, "title": "Staff Signal"},
        },
        "events",
    )


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsEvent
