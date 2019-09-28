"""Commands module for PUBLIC COMMANDS.
Access: Public"""

from datetime import datetime as dt
import json
from random import randint
import re

import requests
import discord

from petal.commands import core
from petal.exceptions import (
    CommandArgsError,
    CommandAuthError,
    CommandInputError,
    CommandOperationError,
)
from petal.grasslands import Pidgeon, Define
from petal.types import Args, Src
from petal.util import dice


link = re.compile(r"\b\w{1,8}://\S+\.\w+\b")


class CommandsPublic(core.Commands):
    auth_fail = "This command is public. If you are reading this, something went wrong."

    async def cmd_hello(self, **_):
        """Echo."""
        return "Hey there!"

    async def cmd_choose(self, args: Args, **_):
        """Choose a random option from a list.

        Syntax: `{p}choose <option>...`
        """
        response = "From what you gave me, I believe `{}` is the best choice".format(
            args[randint(0, len(args) - 1)]
        )
        return response

    async def cmd_bugger(self, args: Args, src: Src, **_):
        """Report a bug, adding it to the Trello board.

        Syntax: `{p}bugger "<bug report>"`
        """
        if self.config.get("trello") is None:
            raise CommandOperationError(
                "Sorry, the bot maintainer has not enabled Trello bug reports."
            )
        try:
            url = f"https://api.trello.com/1/lists/{self.config.get('trello/list_id')}/cards"
            params = {
                "key": self.config.get("trello/app_key"),
                "token": self.config.get("trello/token"),
            }
            response = requests.request("GET", url, params=params)

        except KeyError:
            raise CommandOperationError(
                "The Trello keys are misconfigured, check your config file"
            )

        if not response:
            raise CommandOperationError(
                "Could not get cards for the list ID provided. Talk to your bot"
                " owner."
            )

        ticketnumber = str(
            max(
                (
                    int(card["name"])
                    for card in (response.json())
                    if card["name"].isnumeric()
                )
            )
            + 1
        )

        params.update(
            {
                "name": ticketnumber.zfill(3),
                "desc": (
                    "{message}\n\n\n\n\n"
                    "Submitted by: {author.name} ({author.id})\n"
                    "Timestamp: {time}\n"
                    "Guild: {guild.name} ({guild.id})\n"
                    "Channel: {channel.name} ({channel.id})".format(
                        message=" ".join(args),
                        author=src.author,
                        channel=src.channel,
                        guild=src.guild,
                        time=dt.utcnow(),
                    )
                ),
                "pos": "bottom",
                "idList": self.config.get("trello/list_id"),
                "username": self.config.get("trello/username"),
            }
        )

        response = requests.request(
            "POST", "https://api.trello.com/1/cards", params=params
        )

        if not response:
            raise CommandOperationError(
                "Could not create bug report. Talk to your bot owner."
            )

        return f"Created bug report with ID `{ticketnumber}`"

    async def cmd_osu(
        self, args: Args, src: Src, _set: str = None, _s: str = None, **_
    ):
        """Display information about an Osu player.

        A username to search may be provided to this command. If no username is provided, the command will try to display your profile instead. If you have not provided your username, your Discord username will be used.
        Your Osu username may be provided with `{p}osu --set <username>`.

        Syntax: `{p}osu [<username>]`

        Options:
        `--set <username>`, `-s <username>` :: Save your Osu username, so you can simply use `{p}osu`.
        """
        if not self.router.osu:
            raise CommandOperationError("Osu Support is not configured.")
        name = _set or _s
        if name:
            osu = args[0] if args else src.author.name

            if not self.db.useDB:
                raise CommandOperationError(
                    "Database is not enabled, so you can't save an osu name.\n"
                    "You can still use `{}osu <username>` though.".format(
                        self.config.prefix
                    )
                )

            self.db.update_member(src.author, {"osu": osu})

            return (
                "You have set `{}` as your preferred OSU account. You can now"
                " run `{}osu` and it will use this name automatically!".format(
                    name, self.config.prefix
                )
            )

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
                raise CommandOperationError(
                    "You have not set an Osu username, and no data was found"
                    " under your Discord username."
                )
        else:
            user = self.router.osu.get_user(args[0])
            if user is None:
                raise CommandInputError("No user found with Osu! name: " + args[0])

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
        return em

    async def cmd_plane(self, args: Args, **_):
        """Write down a worry on a piece of paper, then fold it into a plane and send it away."""
        if not args:
            raise CommandArgsError(
                "I can't make a plane without a worry, that would be a waste of"
                " paper D:\n`#SaveTheTrees`"
            )
        elif len(args) > 1:
            raise CommandArgsError(
                "You will need to put your worry in quotes so I can write it down."
            )
        else:
            return (
                "I wrote down your worry on a sheet of paper. Then, I folded it"
                " into a plane and threw it. It flew {} meters before landing."
                " Now your worry is {} :D".format(
                    randint(10000, 99999) / 10,
                    "far far away"
                    if randint(0, 1000)
                    else "farther out than Woodstock",
                )
            )

    # async def cmd_setosu(self, args, src, **_):
    #     """Specify your Osu username so that `{p}osu` can find you automatically.
    #
    #     Syntax: `{p}setosu <name>`
    #     """
    #     osu = args[0] if args else src.author.name
    #
    #     if not self.db.useDB:
    #         return (
    #             "Database is not enabled, so you can't save an osu name.\n"
    #             + "You can still use `{}osu <name>` though.".format(self.config.prefix)
    #         )
    #
    #     self.db.update_member(src.author, {"osu": osu})
    #
    #     return (
    #         "You have set `"
    #         + osu
    #         + "` as your preferred OSU account. "
    #         + "You can now run `{}osu` and it ".format(self.config.prefix)
    #         + "will use this name automatically!"
    #     )

    async def cmd_freehug(self, args: Args, src: Src, **_):
        """Request a free hug from, or register as, a hug donor.

        When this command is run with no arguments, a randomly selected online user from the Hug Donors database will be messaged with a notification that a hug has been requested. That user can then descend upon whoever invoked the command and initiate mutual arm enclosure.

        Syntax:
        `{p}freehug` - Request a hug.
        `{p}freehug status` - If you are a donor, see how many requests you have recieved.
        `{p}freehug donate` - Toggle your donor status. Your request counter will reset if you opt out.
        """
        if not args:
            valid = []
            for m in self.config.hugDonors:
                user = self.get_member(src, m)
                if user is not None:
                    if user.status == discord.Status.online and user != src.author:
                        valid.append(user)

            if len(valid) == 0:
                return "Sorry, no valid hug donors are online right now"

            pick = valid[randint(0, len(valid) - 1)]

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

        # if args[0].lower() == "add":
        #     if len(args) < 2:
        #         return "To add a user, please tag them after `{}freehug add`.".format(
        #             self.config.prefix
        #         )
        #     user = self.get_member(src, args[1].lower())
        #     if user is None:
        #         return "No valid user found for " + args[1]
        #     if user.id in self.config.hugDonors:
        #         return "That user is already a hug donor"
        #
        #     self.config.hugDonors[user.id] = {"name": user.name, "donations": 0}
        #     self.config.save()
        #     return "{} added to the donor list".format(user.name)
        #
        # elif args[0].lower() == "del":
        #     if len(args) < 2:
        #         return "To remove a user, please tag them after `{}freehug del`.".format(
        #             self.config.prefix
        #         )
        #     user = self.get_member(src, args[1].lower())
        #     if user is None:
        #         return "No valid user for " + args[1]
        #     if user.id not in self.config.hugDonors:
        #         return "That user is not a hug donor"
        #
        #     del self.config.hugDonors[user.id]
        #     return "{} was removed from the donor list".format(user.name)

        elif args[0].lower() == "status":
            if src.author.id not in self.config.hugDonors:
                return (
                    "You are not a hug donor, use `{}freehug donate` "
                    "to add yourself.".format(self.config.prefix)
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

    async def cmd_askpatch(self, args: Args, src: Src, **_):
        """Access the AskPatch database. Functionality determined by subcommand.

        Syntax:
        `{p}askpatch submit "<question>"` - Submit a question to Patch Asks. Should be quoted.
        """
        if not args:
            raise CommandArgsError("Subcommand required.")

        subcom = args.pop(0)

        if subcom == "submit":
            if not args:
                raise CommandInputError("Question cannot be empty.")
            elif len(args) > 1:
                raise CommandInputError("Question should be put in quotes.")
            else:
                msg = args[0]

            response = self.db.submit_motd(src.author.id, msg)
            if response is None:
                raise CommandOperationError(
                    "Unable to add to database, ask your bot owner as to why."
                )

            em = discord.Embed(
                title="Entry " + str(response["num"]),
                description="New question from " + src.author.name,
                colour=0x8738F,
            )
            em.add_field(name="content", value=response["content"])

            chan = self.client.get_channel(self.config.get("motdModChannel"))
            await self.client.embed(chan, embedded=em)

            return "Question added to database."

        elif subcom in ("approve", "reject", "count"):
            raise CommandAuthError("Restricted subcommand.")
        else:
            raise CommandInputError("Unrecognized subcommand.")

    async def cmd_wiki(self, args: Args, src: Src, **_):
        """Retrieve information about a query from Wikipedia.

        Syntax: `{p}wiki <query>`
        """
        if not args:
            return "Wikipedia, the Free Encyclopedia\nhttps://en.wikipedia.org/"
        query = " ".join(args)
        self.log.f("wiki", "Query string: " + query)

        response = Pidgeon(query).get_summary()
        title = response[1]["title"]
        url = "https://en.wikipedia.org/wiki/" + title
        if response[0] == 0:
            return response[1]
        else:
            if "may refer to:" in response[1]["content"]:
                em = discord.Embed(color=0xFFCC33)
                em.add_field(
                    name="Developer Note",
                    value="It looks like this entry may have multiple results, "
                    "try to refine your search for better accuracy.",
                )

            else:
                em = discord.Embed(color=0xF8F9FA, description=response[1]["content"])
                em.set_author(
                    name="'{}' on Wikipedia".format(title),
                    url=url,
                    icon_url="https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/1122px-Wikipedia-logo-v2.svg.png",
                )

            await self.client.embed(src.channel, em)

    async def cmd_define(
        self,
        args: Args,
        src: Src,
        _language: str = None,
        _l: str = None,
        _etymology: int = None,
        _e: int = None,
        **_,
    ):
        """Find the definition of a word from Wiktionary.

        Syntax: `{p}define <word>`

        Options:
        `--language=<str>`, `-l <str>` :: Specify a language in which to search for the word.
        `--etymology=<int>`, `-e <int>` :: Specify a certain number etymology to be shown.
        """
        if not args:
            return "Wiktionary, the Free Dictionary\nhttps://en.wiktionary.org/"
        word = args[0]
        self.log.f("dict", "Query string: " + word)

        async with src.channel.typing():
            which = _etymology or _e or 0

            ref = Define(word, _language or _l, which)
            url = "https://en.wiktionary.org/wiki/" + word
            if ref.valid:
                em = discord.Embed(color=0xF8F9FA)
                em.set_author(
                    name="'{}' on Wiktionary ({} etymolog{} available)".format(
                        word, ref.alts, "y" if ref.alts == 1 else "ies"
                    ),
                    url=url,
                    icon_url="https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/1122px-Wikipedia-logo-v2.svg.png",
                )
                em.add_field(name="Etymology", value=ref.etymology, inline=False)
                for definition in ref.definitions:
                    em.add_field(
                        name="`{}` ({}):".format(word, definition["partOfSpeech"]),
                        value="\n- ".join(
                            [
                                text
                                for text in definition["text"]
                                if not re.search(r"^\(.*vulgar.*\)", text.lower())
                            ]
                        ),
                        inline=False,
                    )

                return em
            else:
                raise CommandOperationError("No definition found.")

    async def cmd_xkcd(
        self, args: Args, src: Src, _explain: int = None, _e: int = None, **_
    ):
        """Display a comic from XKCD. If no number is specified, pick one randomly.

        Syntax: `{p}xkcd [<int>]`

        Options: `--explain=<int>`, `-e <int>` :: Provide a link to the explanation of the given comic number.
        """
        ex = _explain if _explain is not None else _e
        if ex is not None:
            return "This is what XKCD #{0} means:\n<https://www.explainxkcd.com/wiki/index.php?title={0}>".format(
                ex
            )

        try:
            indexresp = json.loads(
                requests.get("http://xkcd.com/info.0.json").content.decode()
            )
        except requests.exceptions.ConnectionError:
            return "XKCD did not return a valid response. It may be down."
        except ValueError as e:
            return "XKCD response was missing data. Try again. [{}]".format(str(e))

        if args:
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
                resp = json.loads(
                    requests.get(
                        "http://xkcd.com/{0}/info.0.json".format(target_number)
                    ).content.decode()
                )
            else:
                resp = json.loads(
                    requests.get("http://xkcd.com/info.0.json").content.decode()
                )

        except requests.exceptions.ConnectionError:
            return "XKCD did not return a valid response. It may be down."
        except ValueError as e:
            return "XKCD response was missing data. Try again. [{}]".format(str(e))

        embed = (
            discord.Embed(color=0x96A8C8)
            .set_image(url=resp["img"])
            .set_author(
                name="XKCD #{}: {}".format(resp["num"], resp["safe_title"]),
                url="https://www.xkcd.com/{}".format(resp["num"]),
                icon_url="https://is1-ssl.mzstatic.com/image/thumb/Purple128/v4/e0/a4/67/e0a467b3-dedf-cc50-aeeb-2efd42bb0386/source/512x512bb.jpg",
            )
            .set_footer(text=resp["alt"])
        )

        await self.client.embed(src.channel, embed)

    async def cmd_roll(
        self,
        args: Args,
        _total: bool = False,
        _t: bool = False,
        _sums: bool = False,
        _s: bool = False,
        **_,
    ):
        """Roll the dice and try your luck.

        This function uses the strongest source of randomness available to the system, with a quality generally considered to be sufficient for use in cryptographic applications. While the fairness of these dice cannot be *guaranteed*, it is as good as it possibly could be on the hardware running this bot.

        A roll specification should be in the format `[n]d[s]`, where *n* is the number of dice to roll, *d* is a literal `d`, and *s* is the number of sides per die. For example, to roll one die with twenty sides, invoke `{p}roll 1d20`. To roll three dice with four sides, invoke `{p}roll 3d4`.
        Omitting the number of dice, e.g. `{p}roll d20`, will default to rolling one.

        Additionally, one may include an addition or subtraction in the expression, which will be applied to the total. For example, `{p}roll 3d4+2` will roll `3d4`, and then add two to the result.

        Syntax: `{p}roll [options] (<number>d<sides>)...`

        Options:
        `--sums`, `-s` :: Display only the sum of each group of dice, not every individual roll.
        `--total`, `-t` :: Display ONLY the final, cumulative, total of all rolls. Overrides `--sums`/`-s`.
        """
        _total = _total or _t  # Print ONLY final cumulative total
        _sums = _sums or _s  # Print ONLY sums of groups

        dice_ = [dice.get_dice(term) for term in args]

        # Look for an excuse not to do anything.
        count = [die.quantity for die in dice_ if die]
        if sum(count) > 100_000:
            # Number of dice might start to slow down the bot.
            raise CommandInputError(
                "I may be a bot, but even I only have so many dice. Try rolling"
                " fewer at a time."
            )
        if sum(count) > 20 and not (_total or _sums):
            # Number of dice would be spammy.
            raise CommandInputError(
                "Nobody can hold that many dice at once. Try rolling fewer"
                " dice, or invoking with `--total` or `--sums`."
            )
        if len(count) > 6 and not _total:
            # Number of groups would be spammy.
            raise CommandInputError(
                "That is a lot of groups to display at once. You should invoke"
                " this command with `--total` to do that."
            )

        rolls = [die.roll() for die in dice_ if die]
        if not rolls:
            raise CommandInputError("Sorry, no valid Roll Expressions provided.")
        em = discord.Embed(title="Dice Output", colour=0x0ACDFF)

        cumulative: int = 0
        for roll in rolls:
            cumulative += roll.total
            if not _total:
                section: str = ""

                if not _sums:
                    for single in roll.results:
                        section += f"{roll.src.one}: `{single}`\n"
                    if roll.add_sum:
                        section += f"Added to total: `{roll.add_sum}`\n"

                # section += f"**{roll.src} TOTAL:** `{roll.total}`\n"
                em.add_field(name=f"{roll.src} - Total: {roll.total}", value=section)

        if _total or len(rolls) > 1:
            # em.add_field(name="Cumulative Total", value=str(cumulative), inline=False)
            em.description = f"Cumulative Total: **__`{cumulative}`__**"

        return em

    async def cmd_sub(self, args: Args, **_):
        """Return a random image from a given subreddit. Defaults to /r/cats.

        Syntax: `{p}sub [<subreddit>]`
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

    async def cmd_calm(self, args: Args, src: Src, **_):
        """Bring up a random image from the "calm" gallery, or add one.

        Syntax: `{p}calm [<link to add to calm>]`
        """
        gal = self.config.get("calmGallery")
        if gal is None:
            return "Sadly, calm hasn't been set up correctly"
        if args:
            await self.client.send_message(
                src.author,
                src.channel,
                "You will be held accountable for whatever you post in here. Just a heads up ^_^",
            )
            gal.append(
                {
                    "author": src.author.name + " " + src.author.id,
                    "content": args[0].strip(),
                }
            )
            self.config.save()
        else:
            return gal[randint(0, len(gal) - 1)]["content"]

    async def cmd_comfypixel(self, args: Args, src: Src, **_):
        """Bring up a random image from the "comfypixel" gallery, or add one.

        Syntax: `{p}comfypixel [<link to add to comfypixel>]`
        """
        gal = self.config.get("comfyGallery")
        if gal is None:
            return "Sadly, comfypixel hasn't been set up correctly"
        if args:
            await self.client.send_message(
                src.author,
                src.channel,
                "You will be held accountable for whatever is posted in here. Just a heads up ^_^",
            )
            gal.append(
                {
                    "author": src.author.name + " " + src.author.id,
                    "content": args[0].strip(),
                }
            )
            self.config.save()
        else:
            return gal[randint(0, len(gal) - 1)]["content"]

    async def cmd_aww(self, args: Args, src: Src, **_):
        """Bring up a random image from the "cute" gallery, or add one.

        Syntax: `{p}aww [<link to add to aww>]`
        """
        gal = self.config.get("cuteGallery")
        if gal is None:
            return "Sadly, aww hasn't been set up correctly"
        if args:
            await self.client.send_message(
                src.author,
                src.channel,
                "You will be held accountable for whatever is posted in here. Just a heads up ^_^",
            )
            gal.append(
                {
                    "author": src.author.name + " " + src.author.id,
                    "content": args[0].strip(),
                }
            )
            self.config.save()
        else:
            return gal[randint(0, len(gal) - 1)]["content"]

    async def cmd_void(self, args: Args, src: Src, **_):
        """Reach into the Void, a bottomless pit of various links and strings.

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
                    f"{author} tried to sneak a mass tag into the void."
                    f"\n\nI have deleted it."
                )

            # if response.startswith("http"):
            if link.search(response):
                return f"*You grab a link from the void:*\n{response}"
            else:
                self.log.f(
                    "VOID",
                    f"{src.author.name} retrieved {num} from the void",
                )
                return response
        else:
            msg: str = src.content.split(" ", 1)[1]

            if "@everyone" in msg or "@here" in msg:
                raise CommandAuthError("Mass tags are not permitted into the Void.")
            else:
                count = self.client.db.save_void(
                    msg, src.author.name, str(src.author.id)
                )

                if count is not None:
                    return f"Added item number {count} to the void"

    async def cmd_spookyclock(self, **_):
        """Be careful, Skeletons are closer than you think..."""
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
        """How long is it till you have to buy people nerdy tshirts?"""
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
