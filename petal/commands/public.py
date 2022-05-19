"""Commands module for PUBLIC COMMANDS.
Access: Public"""

import json
import re
from datetime import datetime as dt
from random import choice, randint
from subprocess import PIPE, run

import discord
import requests
import requests_cache
from requests.utils import requote_uri

from bs4 import BeautifulSoup

from petal.commands import core
from petal.exceptions import (
    CommandArgsError,
    CommandAuthError,
    CommandInputError,
    CommandOperationError,
)
from petal.grasslands import Pidgeon, Define, UrbanPidgeon
from petal.types import Args, Src
from petal.util import dice
from petal.util.embeds import Color, membership_card

link = re.compile(r"\b\w{1,8}://\S+\.\w+\b")
requests_cache.install_cache("lazy_money_cache", expire_after=1800)


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
            response = requests.get(url, params=params)

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

        response = requests.post("https://api.trello.com/1/cards", params=params)

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
            if not self.db.useDB:
                raise CommandOperationError(
                    "Database is not enabled, so you can't save an osu name.\n"
                    "You can still use `{}osu <username>` though.".format(
                        self.config.prefix
                    )
                )

            self.db.update_member(src.author, {"osu": name})

            return (
                "You have set `{}` as your preferred Osu account. You can now"
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
                raise CommandInputError(f"No user found with Osu name: {args[0]}")

        em = discord.Embed(
            title=user.name,
            description=f"https://osu.ppy.sh/u/{user.id}",
            colour=Color.info,
        )

        em.set_author(name="Osu Data", icon_url=self.client.user.avatar_url)
        em.set_thumbnail(url=f"https://a.ppy.sh/{user.id}")
        em.add_field(
            name="Maps Played",
            value=f"{int(user.playcount):,}" if user.playcount is not None else "None",
        )
        em.add_field(
            name="Total Score",
            value=f"{int(user.total_score):,}"
            if user.total_score is not None
            else "None",
        )
        em.add_field(
            name="Level",
            value=str(round(float(user.level), 2))
            if user.level is not None
            else "None",
            inline=False,
        )
        em.add_field(
            name="Accuracy",
            value=str(round(float(user.accuracy), 2))
            if user.accuracy is not None
            else "None",
        )
        em.add_field(
            name="PP Rank",
            value=f"{int(user.rank):,}" if user.rank is not None else "None",
            inline=False,
        )
        em.add_field(
            name="Local Rank ({!r})".format(user.country),
            value=f"{int(user.country_rank):,}"
            if user.country_rank is not None
            else "None",
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
                self.config.hugDonors[str(pick.id)]["donations"] += 1
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
            if str(src.author.id) not in self.config.hugDonors:
                return (
                    "You are not a hug donor, use `{}freehug donate` "
                    "to add yourself.".format(self.config.prefix)
                )

            return "You have received {} requests since you became a donor".format(
                self.config.hugDonors[str(src.author.id)]["donations"]
            )

        elif args[0].lower() == "donate":
            if str(src.author.id) not in self.config.hugDonors:
                self.config.hugDonors[str(src.author.id)] = {
                    "name": src.author.name,
                    "donations": 0,
                }
                self.config.save()
                return "Thanks! You have been added to the donor list <3"
            else:
                del self.config.hugDonors[str(src.author.id)]
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
                colour=Color.question,
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
                em = discord.Embed(color=Color.wiki_vague)
                em.add_field(
                    name="Developer Note",
                    value="It looks like this entry may have multiple results, "
                    "try to refine your search for better accuracy.",
                )

            else:
                em = discord.Embed(color=Color.wiki, description=response[1]["content"])
                em.set_author(
                    name="'{}' on Wikipedia".format(title),
                    url=requote_uri(url),
                    icon_url="https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/1122px-Wikipedia-logo-v2.svg.png",
                )

            await self.client.embed(src.channel, em)

    async def cmd_urband(self, args: Args, src: Src, **_):
        """Find the definition of a word from Urban Dictionary

        Syntax: `{p}urband <word>`
        """
        if not args:
            return "Urban Dictionary, <https://www.urbandictionary.com/>"

        word = " ".join(args)
        if src.channel.id not in self.config.get(
            "nsfwChannels"
        ):
            return "This command is only allowed in NSFW channels"

        async with src.channel.typing():
            urb = UrbanPidgeon(word)
            code, result = urb.get_definition()

            if code:
                em = discord.Embed(color=Color.urban, description=f"{result['definition']}\n\nExample:\n{result['example']}")
                em.set_author(
                    name=f"'{result['word']}' defined by {result['author']}",
                    url=result['permalink']
                )

                em.add_field(name="Thumbs Up 👍", value=f"{result['thumbs_up']}", inline=True)
                em.add_field(name="Thumbs Down 👎", value=f"{result['thumbs_down']}", inline=True)
                em.set_footer(text=f"This definition was written on {result['written_on'][:-5]}")
                await self.client.embed(src.channel, em)
            else:
                return "*Unable to get a definition of that word from UrbanDictionary.com*"


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
                em = discord.Embed(color=Color.wiki)
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

    async def cmd_xkcd(self, args: Args, _explain: int = None, _e: int = None, **_):
        """Display a comic from XKCD. If no number is specified, pick one randomly.

        Syntax: `{p}xkcd [<int>]`

        Options: `--explain=<int>`, `-e <int>` :: Provide a link to the explanation of the given comic number.
        """
        ex = _explain if _explain is not None else _e
        if ex is not None:
            return (
                f"This is what XKCD #{ex} means:"
                f"\n<https://www.explainxkcd.com/wiki/index.php?title={ex}>"
            )

        try:
            indexresp = json.loads(
                requests.get("https://xkcd.com/info.0.json").content.decode()
            )
        except requests.exceptions.ConnectionError as e:
            raise CommandOperationError(
                "XKCD did not return a valid response. It may be down."
            ) from e
        except ValueError as e:
            raise CommandOperationError(
                f"XKCD response was missing data. Try again. [{e}]"
            ) from e

        number = indexresp["num"]
        if args:
            try:
                target_number = int(args[0])

                if not (0 <= target_number <= number):
                    raise CommandInputError(
                        "Cannot find an XKCD comic with that Index."
                    )

            except ValueError as e:
                raise CommandInputError(
                    "You must enter a **number** for a custom xkcd"
                ) from e
            else:
                if target_number == 404:
                    return "Don't be that guy."
        else:
            target_number = randint(0, number)
            while target_number == 404:
                target_number = randint(0, number)

        try:
            if target_number != 0:
                resp = json.loads(
                    requests.get(
                        f"https://xkcd.com/{target_number}/info.0.json"
                    ).content.decode()
                )
            else:
                resp = indexresp

        except requests.exceptions.ConnectionError as e:
            raise CommandOperationError(
                "XKCD did not return a valid response. It may be down."
            ) from e
        except ValueError as e:
            raise CommandOperationError(
                f"XKCD response was missing data. Try again. [{e}]"
            ) from e

        embed = (
            discord.Embed(
                color=Color.xkcd,
                timestamp=dt(
                    int(resp["year"]), int(resp["month"]), int(resp["day"]), 12
                ),
            )
            .set_image(url=resp["img"])
            .set_author(
                name="XKCD #{num}: {safe_title}".format(**resp),
                url="https://www.xkcd.com/{}".format(resp["num"]),
                icon_url="https://is1-ssl.mzstatic.com/image/thumb/Purple128/v4"
                "/e0/a4/67/e0a467b3-dedf-cc50-aeeb-2efd42bb0386/source/512x512bb.jpg",
            )
            .set_footer(text=resp["alt"])
        )

        return embed

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
        em = discord.Embed(title="Dice Output", colour=Color.info)

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
            raise CommandOperationError("Sadly, calm hasn't been set up correctly")
        if args:
            yield (
                "You will be held accountable for whatever is posted in here."
                " Just a heads up ^_^"
            )
            gal.append(
                {
                    "author": f"{src.author.name} {src.author.id}",
                    "content": args[0].strip(),
                }
            )
            self.config.save()
        else:
            yield choice(gal)["content"]

    async def cmd_comfypixel(self, args: Args, src: Src, **_):
        """Bring up a random image from the "comfypixel" gallery, or add one.

        Syntax: `{p}comfypixel [<link to add to comfypixel>]`
        """
        gal = self.config.get("comfyGallery")
        if gal is None:
            raise CommandOperationError(
                "Sadly, comfypixel hasn't been set up correctly"
            )
        if args:
            yield (
                "You will be held accountable for whatever is posted in here."
                " Just a heads up ^_^"
            )
            gal.append(
                {
                    "author": f"{src.author.name} {src.author.id}",
                    "content": args[0].strip(),
                }
            )
            self.config.save()
        else:
            yield choice(gal)["content"]

    async def cmd_aww(self, args: Args, src: Src, **_):
        """Bring up a random image from the "cute" gallery, or add one.

        Syntax: `{p}aww [<link to add to aww>]`
        """
        gal = self.config.get("cuteGallery")
        if gal is None:
            raise CommandOperationError("Sadly, aww hasn't been set up correctly")
        if args:
            yield (
                "You will be held accountable for whatever is posted in here."
                " Just a heads up ^_^"
            )
            gal.append(
                {
                    "author": f"{src.author.name} {src.author.id}",
                    "content": args[0].strip(),
                }
            )
            self.config.save()
        else:
            yield choice(gal)["content"]

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
                self.log.f("VOID", f"{src.author.name} retrieved {num} from the void")
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
        today = dt.today()
        td = (dt(today.year, 10, 31, 0, 0) - dt.utcnow()).total_seconds()
        if td < 0:
            return ":ghost: Beware! The skeletons are already here! :ghost:"
        d = divmod(td, 86400)
        h = divmod(d[1], 3600)
        m = divmod(h[1], 60)
        s = int(m[1])
        return (
            ":ghost: **Spooky Clock Says:** Skeletons are"
            " `{} days, {} hours, {} minutes, and {} seconds`"
            " away :ghost:".format(int(d[0]), int(h[0]), int(m[0]), s)
        )

    async def cmd_santaclock(self, **_):
        """How long is it till you have to buy people nerdy tshirts?"""
        today = dt.today()
        td = (dt(today.year, 12, 25, 0, 0) - dt.utcnow()).total_seconds()
        if td < 0:
            return (
                "Christmas already happened...Gotta wait a bit more for"
                " presents. Enjoy the snow! Unless you live in the south where"
                " climate change prevents snow now."
            )
        d = divmod(td, 86400)
        h = divmod(d[1], 3600)
        m = divmod(h[1], 60)
        s = int(m[1])
        return (
            ":christmas_tree: **Santa Clock Says:** Santa is"
            " `{} days, {} hours, {} minutes, and {} seconds`"
            " away :christmas_tree:".format(int(d[0]), int(h[0]), int(m[0]), s)
        )

    async def cmd_trees(self, **_):
        """how many trees has the internet planted?"""
        ua = {"User-Agent": "Petal/python3.7 DiscordBot"}
        raw = requests.get("https://teamtrees.org", headers=ua).text
        bs = BeautifulSoup(raw, features="html.parser")
        tag = bs.find("h2", {"id": "totalTrees"})
        return (
            "According to https://teamtrees.org, money has been raised to plant"
            " **{:,}** trees so far!\n\nThis is {}% of the initial goal of **20"
            " million** trees".format(
                int(tag.attrs["data-count"]),
                int((float(tag.attrs["data-count"]) / 20000000.00) * 100.00),
            )
        )

    async def cmd_userinfo(self, args, src: Src, **_):
        """Display information about yourself.

        Syntax: `{p}userinfo`
        """
        if not args:
            args = [src.author.id]

        if args != [src.author.id]:
            raise CommandAuthError(
                "Only a Moderator can view the info of another User."
            )

        if not all(map(lambda x: isinstance(x, int) or x.isdigit(), args)):
            raise CommandArgsError("All IDs must be positive Integers.")

        for userid in args:
            target: discord.Member = src.guild.get_member(
                int(userid)
            ) or self.client.main_guild.get_member(int(userid))

            if target is None:
                raise CommandInputError(f"Could not get user with ID `{userid}`.")
            else:
                yield membership_card(target)

    async def cmd_dsmsg(
        self,
        # NOTE: Change to `_bb1` upon announcement of Bloodborne II.
        _bb: bool = False,
        _ds1: bool = False,
        _ds2: bool = False,
        _ds3: bool = False,
        _des: bool = False,
        # NOTE: Change to `_er1` upon announcement of Elden Ring II.
        _er: bool = False,
        _sek: bool = False,
        **_,
    ):
        """Randomly generate a message that you might find in games by
            FromSoftware.

        The message may be in the format used by any of the games. Also requires
            that a path to an executable is set in the bot config.

        Options:
        `--bb`  :: Generate messages from Bloodborne.
        `--des` :: Generate messages from Demon's Souls.
        `--ds1` :: Generate messages from Dark Souls I.
        `--ds2` :: Generate messages from Dark Souls II.
        `--ds3` :: Generate messages from Dark Souls III.
        `--er`  :: Generate messages from Elden Ring.
        `--sek` :: Generate messages from Sekiro.
        """
        binary = self.config.get("dsmsg_executable")
        if not binary:
            raise CommandOperationError(
                "Sorry, I have not been set up with a path to `dsmsg`."
            )

        dsmsg = [binary]

        if _bb:
            dsmsg.append("--bb")
        if _des:
            dsmsg.append("--des")
        if _ds1:
            dsmsg.append("--ds1")
        if _ds2:
            dsmsg.append("--ds2")
        if _ds3:
            dsmsg.append("--ds3")
        if _er:
            dsmsg.append("--er1")
        if _sek:
            dsmsg.append("--sek")

        print(repr(dsmsg))

        proc = run(dsmsg, stdout=PIPE)
        if proc.returncode != 0:
            raise CommandOperationError("Sorry, something went wrong with dsmsg.")

        return "You seek out guidance from another world...```\n{}```".format(
            proc.stdout.decode()
        )

    async def cmd_lazymath(self, args, src: Src, **_):
        """Converter for all your basic unit conversions

        Syntax: `{p}lazymath [number]`
        """
        if not args:
            raise CommandArgsError("Give me numbers. Try again (or edit your message) to have a number")

        i = args[0]
        if len(i) > 12:
            CommandArgsError("Number must be an integer, or float, with less than 12 characters")

        try:
            i = float(i)
        except ValueError:
            CommandArgsError("Number must be a valid integer or float")

        em = discord.Embed(
            title=f"Lazy Math for: {i}",
            colour=src.author.colour,
            description="(Rounded to 3 places)",
        )

        ctof = i * 1.800 + 32.000
        ftoc = (i - 32.000) / 1.800
        mtok = i * 1.609
        ktom = i / 1.609
        ftom = i / 3.281
        mtof = i * 3.281
        ltok = i / 2.205
        ktol = i * 2.205

        em.add_field(name="C to F", value=str(round(ctof, 3)) + " F°", inline=True)
        em.add_field(name="F to C", value=str(round(ftoc, 3)) + " C°", inline=True)
        em.add_field(name="\u200B", value="\u200B")
        em.add_field(
            name="MPH to KPH", value=str(round(mtok, 3)) + " km/h", inline=True
        )
        em.add_field(name="KPH to MPH", value=str(round(ktom, 3)) + " MPH", inline=True)
        em.add_field(name="\u200B", value="\u200B")
        em.add_field(
            name="Ft to M", value=str(round(ftom, 3)) + " Metre(s)", inline=True
        )
        em.add_field(name="M to Ft", value=str(round(mtof, 3)) + " Feet", inline=True)
        em.add_field(name="\u200B", value="\u200B")
        em.add_field(name="Lb to Kg", value=str(round(ltok, 3)) + " Kg", inline=True)
        em.add_field(name="Kg to Lb", value=str(round(ktol, 3)) + " Lbs", inline=True)
        em.add_field(name="\u200B", value="\u200B")

        return em

    async def cmd_lazymoney(self, args, src: Src, **_):
        """Get up to date exchange information for a given monetary amount Valid Currency Codes: AUD, BGN, BRL, BTC,
        CAD, CHF, CNY, CZK, DKK, DOGE, ETH, ETC, EUR, GBP, HKD, HRK, HUF, IDR, ILS, INR, IOTA, ISK, JPY, KRW, LITE,
        MXN, MYR, NOK, NZD, OSRS, PHP, PLN,RON, RUB, RPL, SEK, SGD, THB, TRY, USD, WOW, XRP, ZAR

        Currency values are cached for 30 minutes

        Syntax: `{p}lazymoney [FROM KEY] [TO KEY] <value>`
        """

        if not args:
            raise CommandArgsError("Please provide a value to convert.\nOptionally, put a currency symbol (3 or 4 digits) first and then a value")

        if len(args) > 0:
            isym = "USD"
            osym = args[0].upper()
            val = "1.00"

        if len(args) > 1:
            isym = args[0].upper()
            osym = args[1].upper()
            val = "1.00"

        if len(args) > 2:
            val = args[2]

        if len(val) > 12:
            raise CommandArgsError("This number is a bit long, please choose a shorter one.")

        try:
            val = float(val)
        except ValueError:
            return "If you are only supplying a value, you will need it to be a valid float"

        if len(isym) not in [3, 4] or len(osym) not in [3, 4]:
            return "Valid symbols are 3 or 4 characters long"

        crypto_cur = ["BTC", "DOGE", "ETC", "ETH", "LTC", "NEO", "RPL", "XRP", "IOTA"]
        normal_cur = [
            "AUD",
            "BELL",
            "BGN",
            "BRL",
            "CAD",
            "CHF",
            "CNY",
            "CZK",
            "DKK",
            "EUR",
            "GBP",
            "HKD",
            "HRK",
            "HUF",
            "IDR",
            "ILS",
            "INR",
            "ISK",
            "JPY",
            "KRW",
            "MXN",
            "MYR",
            "NOK",
            "NZD",
            "PHP",
            "PLN",
            "RON",
            "RUB",
            "SEK",
            "SGD",
            "THB",
            "TRY",
            "USD",
            "ZAR",
        ]
        gamer_cur = ["OSRS", "WOW", "BELL"]

        if isym == "WOW" or osym == "WOW":
            r = requests.get(
                f"https://api-pn.playerauctions.com/markettracker/api/WoW/CurrencyOrder"
            )
            if r.status_code != 200:
                raise CommandOperationError("World of Warcraft conversion api did not return a valid result. Please try again later")

            rate = r.json()["Result"]["AvgOrderPrice"]["USD"] * 200.00
            em = discord.Embed(
                title="World of Warcraft (US)",
                colour=src.author.colour,
                description=f"200K Gold per {rate} USD",
            )

            if osym == "WOW":
                rate = 1.00 / rate
                em.add_field(
                    name=f"{val} USD to WOW",
                    value=str(round(val * rate * 200.00, 2)) + "K gold",
                )
            else:
                em.add_field(
                    name=f"{val} WOW to USD",
                    value=str(round(val * rate / 200000.00, 2)) + " USD",
                )

            em.set_footer(
                text="Note, OSRS and WOW symbols can only be converted to USD at the moment"
            )
            return em

        if isym == "OSRS" or osym == "OSRS":
            r = requests.get(
                f"https://api-pn.playerauctions.com/markettracker/api/OSRS/CurrencyOrder"
            )
            if r.from_cache:
                self.log.f("Money", "Using cached response for playerauctions.com")
            if r.status_code != 200:
                raise CommandOperationError("Old School Runescape conversion api did not return a valid result. Please try again later")

            rate = r.json()["Result"]["AvgOrderPrice"]["USD"] * 30.00

            em = discord.Embed(
                title="Old School Runescape",
                colour=src.author.colour,
                description=f"Rate per 30M GP: {rate} USD",
            )

            if osym == "OSRS":
                rate = 1.00 / rate
                em.add_field(
                    name=f"{val} USD to OSRS",
                    value=str(round(val * rate * 30.00, 2)) + "M GP",
                )
            else:

                em.add_field(
                    name=f"{val} OSRS to USD",
                    value=str(round(val * rate / 30000000.00, 2)) + " USD",
                )

            em.set_footer(
                text="Note, OSRS and WOW symbols can only be converted to USD at the moment"
            )
            return em

        if isym == "BELL" or osym == "BELL":
            r = requests.get(
                f"https://api-pn.playerauctions.com/markettracker/api/Animal-Crossing-NH/CurrencyOrder"
            )
            if r.from_cache:
                self.log.f("Money", "Using cached response for playerauctions.com")
            if r.status_code != 200:
                raise CommandOperationError("Animal Crossing Bells conversion api did not return a valid result. Please try again later")

            rate = r.json()["Result"]["AvgOrderPrice"]["USD"] * 5.00

            em = discord.Embed(
                title="Animal Crossing New Horizons",
                colour=src.author.colour,
                description=f"Rate per 5M Bells: {rate} USD",
            )

            if osym == "BELL":
                rate = 1.00 / rate
                em.add_field(
                    name=f"{val} USD to BELL",
                    value=str(round(val * rate * 5.00, 2)) + "M Bells",
                )
            else:

                em.add_field(
                    name=f"{val} BELL to USD",
                    value=str(round(val * rate / 5000000.00, 2)) + " USD",
                )

            em.set_footer(
                text="Note, Animal Crossing symbols can only be converted to USD at the moment"
            )
            return em

        if not all([v for v in [isym, osym] if v in crypto_cur + normal_cur]):
            raise CommandArgsError("One or both of the inputs are not valid. Use the `help lazymoney` command for a list of valid currency symbols")

        if any([v for v in [isym, osym] if v in crypto_cur]):
            if len(args) == 1:
                isym = osym
                osym = "USD"

            if isym in crypto_cur:
                r = requests.get(
                    f"https://min-api.cryptocompare.com/data/price?fsym={osym}&tsyms=BTC,DOGE,ETH,ETC,RPL,IOTA,XRP,NEO,LTC,IOTA"
                )
                if r.from_cache:
                    self.log.f("Money", "Using cached response for cryptocompare.com")
                if r.status_code != 200:
                    raise CommandOperationError("Crypto API did not return a valid result. Please try again later")
                rate = 1 / r.json()[isym]

            if osym in crypto_cur:
                r = requests.get(
                    f"https://min-api.cryptocompare.com/data/price?fsym={isym} \&tsyms=BTC,DOGE,ETH,ETC,RPL,IOTA,XRP,NEO,LTC,IOTA"
                )
                if r.from_cache:
                    self.log.f("Money", "Using cached response for cryptocompare.com")
                if r.status_code != 200:
                    raise CommandOperationError("Crypto API did not return a valid result. Please try again later")
                rate = r.json()[osym]

            em = discord.Embed(
                title=f"Crypto Conversion",
                colour=src.author.colour,
                description=f"Rate: 1 {isym} = {rate} {osym}",
            )
            em.add_field(
                name=f"{val} {isym} to {osym}",
                value=f"{str(round(val * rate, 2))} {osym}",
            )
            return em

        r = requests.get(f"https://api.exchangeratesapi.io/latest?base={isym}")

        if r.from_cache:
            self.log.f("Money", "Using cached response for exchangeratesapi.io")
        if r.status_code != 200:
            raise CommandOperationError("Exchange Rate API did not return a valid result. Please try again later")

        rate = r.json()["rates"][osym]
        em = discord.Embed(
            title="Currency Conversion",
            colour=src.author.colour,
            description=f"Rate: 1 {isym} = {rate} {osym}",
        )
        em.add_field(
            name=f"{val} {isym} to {osym}", value=f"{str(round(val * rate, 2))} {osym}"
        )
        return em


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsPublic
