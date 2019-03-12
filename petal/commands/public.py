"""Commands module for PUBLIC COMMANDS.
Access: Public"""

from datetime import datetime as dt
import random

import discord

from . import core


class CommandsPublic(core.Commands):
    auth_fail = "This command is public. If you are reading this, something went wrong."

    def authenticate(self, *_):
        return True

    async def cmd_hello(self, **_):
        """
        Echo.
        """
        return "Hey there!"

    async def cmd_choose(self, args, **_):
        """
        Choose a random option from a list.

        Syntax: `{p}choose <option> [<option> [<option> [...]]]`
        """
        response = "From what you gave me, I believe `{}` is the best choice".format(
            args[random.randint(0, len(args) - 1)]
        )
        return response

    async def cmd_osu(self, args, src, **_):
        """
        Display information about an Osu player.

        A username to search may be provided to this command. If no username is provided, the command will try to display your profile instead. If you have not provided your username, your Discord username will be used.
        Your Osu username may be provided with `{p}setosu`.

        Syntax: `{p}osu [<username>]`
        """
        if not self.router.osu:
            return "Osu Support is not configured."
        if not args:
            # No username specified; Print info for invoker
            if self.db.useDB:
                # Check whether the user has provided a specific name
                username = self.db.get_attribute(src.author, "osu") or src.author.name
            else:
                # Otherwise, try their Discord username
                username = src.author.name

            user = self.router.osu.get_user(username)

            if user is None:
                return "You have not set an Osu username, and no data was found under your Discord username."
        else:
            user = self.router.osu.get_user(args[0])
            if user is None:
                return "No user found with Osu! name: " + args[0]

        em = discord.Embed(
            title=user.name,
            description="https://osu.ppy.sh/u/{}".format(user.id),
            colour=0x0ACDFF,
        )

        em.set_author(name="Osu Data", icon_url=self.client.user.avatar_url)
        em.set_thumbnail(url="http://a.ppy.sh/" + user.id)
        em.add_field(name="Maps Played", value="{:,}".format(int(user.playcount)))
        em.add_field(name="Total Score", value="{:,}".format(int(user.total_score)))
        em.add_field(name="Level", value=str(round(float(user.level), 2)), inline=False)
        em.add_field(name="Accuracy", value=str(round(float(user.accuracy), 2)))
        em.add_field(name="PP Rank", value="{:,}".format(int(user.rank)), inline=False)
        em.add_field(
            name="Local Rank ({})".format(user.country),
            value="{:,}".format(int(user.country_rank)),
        )
        await self.client.embed(src.channel, embedded=em)
        return None

    async def setosu(self, args, src, **_):
        """
        Sets a users preferred osu account
        !setosu <name>
        """
        osu = args[0] if args else src.author.name

        if not self.db.useDB:
            return (
                "Database is not enabled, so you can't save an osu name.\n"
                + "You can still use `{}osu <name>` though.".format(self.config.prefix)
            )

        self.db.update_member(src.author, {"osu": osu})

        return (
            "You have set `"
            + osu
            + "` as your preferred OSU account. "
            + "You can now run `{}osu` and it ".format(self.config.prefix)
            + "will use this name automatically!"
        )

    async def cmd_freehug(self, args, src, **_):
        """
        Request a free hug from a hug donor.

        Syntax: `{p}freehug` - requests a hug
        `{p}freehug donate` - toggles your donor status. Your request counter will reset if you opt out.
        `{p}freehug add <user-id>` - adds user to donor list
        `{p}freehug del <user-id>` - removes user from donor list
        `{p}freehug status` - If you're a donor, see how many requests you have recieved
        """
        if args[0] == "":
            valid = []
            for m in self.config.hugDonors:
                user = self.get_member(src, m)
                if user is not None:
                    if user.status == discord.Status.online and user != src.author:
                        valid.append(user)

            if len(valid) == 0:
                return "Sorry, no valid hug donors are online right now"

            pick = valid[random.randint(0, len(valid) - 1)]

            try:
                await self.client.send_message(
                    src.author,
                    pick,
                    "Hello there. "  # GENERAL KENOBI, YOU ARE A BOLD ONE
                    + "This message is to inform "
                    + "you that "
                    + src.author.name
                    + " has requested a hug from you",
                )
            except discord.ClientException:
                return (
                    "Your hug donor was going to be: "
                    + pick.mention
                    + " but unfortunately they were unable to be contacted"
                )
            else:
                self.config.hugDonors[pick.id]["donations"] += 1
                self.config.save()
                return "A hug has been requested of: " + pick.name

        if args[0].lower() == "add":
            if len(args) < 2:
                return "To add a user, please tag them after add | "
            user = self.get_member(src, args[1].lower())
            if user is None:
                return "No valid user found for " + args[1]
            if user.id in self.config.hugDonors:
                return "That user is already a hug donor"

            self.config.hugDonors[user.id] = {"name": user.name, "donations": 0}
            self.config.save()
            return "{} added to the donor list".format(user.name)

        elif args[0].lower() == "del":
            if len(args) < 2:
                return "To remove a user, please tag them after del | "
            user = self.get_member(src, args[1].lower())
            if user is None:
                return "No valid user for " + args[1]
            if user.id not in self.config.hugDonors:
                return "That user is not a hug donor"

            del self.config.hugDonors[user.id]
            return "{} was removed from the donor list".format(user.name)

        elif args[0].lower() == "status":
            if src.author.id not in self.config.hugDonors:
                return (
                    "You are not a hug donor, user `freehug donate` to "
                    + "add yourself"
                )

            return "You have received {} requests since you became a donor".format(
                self.config.hugDonors[src.author.id]["donations"]
            )

        elif args[0].lower() == "donate":
            if src.author.id not in self.config.hugDonors:
                self.config.hugDonors[src.author.id] = {
                    "name": src.author.name,
                    "donations": 0,
                }
                self.config.save()
                return "Thanks! You have been added to the donor list <3"
            else:
                del self.config.hugDonors[src.author.id]
                self.config.save()
                return "You have been removed from the donor list."

    async def cmd_sub(self, args, **_):
        """
        Return a random image from a given subreddit. Defaults to /r/cats.

        Syntax: '{p}sub [<subreddit>]'
        """
        sr = args[0] if args else "cats"
        # if force is not None:
        #     sr = force
        try:
            self.router.i
        except AttributeError:
            return "Imgur Support is disabled by administrator"

        try:
            ob = self.router.i.get_subreddit(sr)
            if ob is None:
                return "Sorry, I couldn't find any images in subreddit: `" + sr + "`"

            if ob.nsfw and not self.config.permitNSFW:
                return (
                    "Found a NSFW image, currently NSFW images are "
                    + " disallowed by administrator"
                )

        except ConnectionError:
            return (
                "A Connection Error Occurred, this usually means imgur "
                + " is over capacity. I cant fix this part :("
            )

        except Exception as e:
            self.log.err("An unknown error occurred " + type(e).__name__ + " " + str(e))
            return "Unknown Error " + type(e).__name__
        else:
            return ob.link

    async def cmd_void(self, args, src, **_):
        """
        Reach into the Void, a bottomless pit of various links and strings.

        The Void contains countless entries of all types. Images, Youtube videos, poetry, quips, puns, memes, and best of all, dead links. Anything is possible with the power of the Void.

        *Note that you will be held accountable if you add malicious content or user pings of any type.*

        Syntax: `{p}void` - Grab a random item from the Void and display/print it.
        `{p}void <link or text message>` - Drop an item into the Void to be randomly retrieved later.
        """
        if not args:
            response = self.client.db.get_void()
            author = response["author"]
            num = response["number"]
            response = response["content"]

            if "@everyone" in response or "@here" in response:
                self.client.db.delete_void()
                return (
                    "Someone (" + author + ") is a butt and tried to "
                    "sneak an @ev tag into the void."
                    "\n\nIt was deleted..."
                )

            if response.startswith("http"):
                return "*You grab a link from the void* \n" + response
            else:
                self.log.f(
                    "VOID",
                    src.author.name + " retrieved " + str(num) + " from the void",
                )
                return response
        else:
            count = self.client.db.save_void(
                src.split(" ", 1)[1], src.author.name, src.author.id
            )

            if count is not None:
                return "Added item number " + str(count) + " to the void"

    async def cmd_spookyclock(self, **_):
        """
        Be careful, Skeletons are closer than you think...
        """
        td = (dt(2019, 10, 31, 0, 0) - dt.utcnow()).total_seconds()
        if td < 0:
            return ":ghost: Beware! The skeletons are already here! :ghost:"
        d = divmod(td, 86400)
        h = divmod(d[1], 3600)
        m = divmod(h[1], 60)
        s = int(m[1])
        return ":ghost: **Spooky Clock Says:** Skeletons are `{} days, {} hours, {} minutes, and {} seconds` away :ghost:".format(
            str(int(d[0])), str(int(h[0])), str(int(m[0])), str(s)
        )

    async def cmd_santaclock(self, **_):
        """
        How long is it till you have to buy people nerdy tshirts?
        """
        td = (dt(2019, 12, 25, 0, 0) - dt.utcnow()).total_seconds()
        if td < 0:
            return "Christmas already happened...Gotta wait a bit more for presents. Enjoy the snow! Unless you live in the south where climate change prevents snow now."
        d = divmod(td, 86400)
        h = divmod(d[1], 3600)
        m = divmod(h[1], 60)
        s = int(m[1])
        return ":christmas_tree: **Santa Clock Says:** Santa is `{} days, {} hours, {} minutes, and {} seconds` away :christmas_tree:".format(
            str(int(d[0])), str(int(h[0])), str(int(m[0])), str(s)
        )


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsPublic
