"""Commands module for NON-ADMINISTRATOR HIGH-LEVEL UTILITIES.
Access: Role-based"""

import discord

from petal.commands import core
from petal.etc import unquote
from petal.exceptions import CommandArgsError, CommandInputError, CommandOperationError
from petal.menu import Menu
from petal.util.fmt import userline


class CommandsMgr(core.Commands):
    auth_fail = "This command requires the `{role}` role."
    role = "role_manager"

    async def cmd_askpatch(self, args, src, **_):
        """Access the AskPatch database. Functionality determined by subcommand.

        Syntax:
        `{p}askpatch submit "<question>"` - Submit a question to Patch Asks. Should be quoted.
        `{p}askpatch approve <question-id>` - Approve a submitted question and add it to the Patch Asks DB.
        `{p}askpatch reject <question-id>` - Reject a submitted question from being added.
        `{p}askpatch count` - Return the number of questions currently queued for use.
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
                title=f"Entry {response['num']}",
                description=f"New question from `{userline(src.author)}`",
                colour=0x8738F,
            )
            em.add_field(name="content", value=response["content"])

            chan = self.client.get_channel(self.config.get("motdModChannel"))
            await self.client.embed(chan, embedded=em)

            return "Question added to database."

        elif subcom == "approve":
            if src.channel.id != self.config.get("motdModChannel"):
                raise CommandOperationError("You can't use that here.")
            if not args:
                raise CommandInputError("You need to specify an entry.")
            if not all(x.isdigit() for x in args):
                raise CommandInputError("Every entry must be an integer.")

            for targ in args:
                result = self.db.update_motd(int(targ), approve=True)
                if result is None:
                    raise CommandOperationError(
                        f"No entries exist with id number: {targ}"
                    )

                em = discord.Embed(
                    title=f"Approved {result['num']}",
                    description=result["content"],
                    colour=0x00FF00,
                ).add_field(name="Submitted by", value=f"<@{result['author']}>")

                return em

        elif subcom == "reject":
            if src.channel.id != self.config.get("motdModChannel"):
                raise CommandOperationError("You can't use that here.")
            if not args:
                raise CommandInputError("You need to specify an entry.")
            if not all(x.isdigit() for x in args):
                raise CommandInputError("Every entry must be an integer.")

            for targ in args:
                result = self.db.update_motd(int(targ), approve=False)
                if result is None:
                    raise CommandOperationError(
                        f"No entries exist with id number: {targ}"
                    )

                em = discord.Embed(
                    title=f"Rejected {result['num']}",
                    description=result["content"],
                    colour=0xFFA500,
                ).add_field(name="Submitted by", value=f"<@{result['author']}>")

                return em

        elif subcom == "count":
            count = self.db.motd.count({"approved": True, "used": False})
            return f"Question queue currently contains `{count}` entries."

        else:
            raise CommandInputError("Unrecognized subcommand.")

    async def cmd_paforce(self, src, **_):
        """Initiate a forced AskPatch."""
        response = await self.router.check_pa_updates(force=True)

        self.log.f(
            "pa",
            src.author.name + " with ID: " + str(src.author.id) + " used the force!",
        )
        await src.delete()
        if response is not None:
            return response

    async def cmd_poll(
        self,
        args,
        src,
        _question: str = "",
        _channel: int = None,
        _time: float = 0,
        **_,
    ):
        """Run a Public Poll, with multiple choices. Anyone can vote for one or
            more of the options provided.

        Syntax: `{p}poll [OPTIONS] <CHOICE>...`

        Parameters
        ----------
        _ : dict
            Dict of additional Keyword Args.
        args : List[str]
            List of Positional Arguments supplied after Command.
        src : discord.Message
            The Discord Message that invoked this Command.
        _question : str
            Specify a Question to be asked.
        _channel : int
            Specify a different Channel ID for the Poll to be posted to.
        _time : float
            Specify the duration of the Poll, in Seconds. Defaults to 3600, or one hour.
        """
        if len(args) < 2:
            return "Must provide at least two options."

        duration = _time if _time > 0 else 3600
        title = unquote(_question) if _question else "Public Poll"

        if _channel:
            targ = self.client.get_channel(_channel)
        else:
            targ = src.channel
        if not targ:
            raise CommandInputError("Invalid Channel")

        poll = Menu(self.client, targ, title)
        await poll.get_poll(args, duration, title="Options")

    async def cmd_vote(
        self, src, _question: str = None, _channel: int = None, _time: float = 0, **_
    ):
        """Run a Public Vote, with choices of Yes or No. Anyone can vote.

        Syntax: `{p}vote [OPTIONS]`

        Parameters
        ----------
        _ : dict
            Dict of additional Keyword Args.
        src : discord.Message
            The Discord Message that invoked this Command.
        _question : str
            Specify a Question to be asked.
        _channel : int
            Specify a different Channel ID for the Poll to be posted to.
        _time : float
            Specify the duration of the Poll, in Seconds. Defaults to 3600, or one hour.
        """
        duration = _time if _time > 0 else 3600
        title = f"Vote: {unquote(_question)}" if _question else "Vote"

        if _channel:
            targ = self.client.get_channel(_channel)
        else:
            targ = src.channel
        if not targ:
            raise CommandInputError("Invalid Channel")

        poll = Menu(self.client, targ, title)
        await poll.get_vote(duration)

    async def cmd_tunnel(
        self,
        args,
        src,
        _disconnect: bool = False,
        _d: bool = False,
        _kill: bool = False,
        _k: bool = False,
        **_,
    ):
        """Establish or manipulate a live connection between multiple Channels.

        A Messaging Tunnel is a live connection between Channels. Any Message sent in any Channel connected to a Tunnel will be forwarded to all other Channels connected to the Tunnel.
        A Tunnel will close automatically if no Messages are sent through it for a given time. This value defaults to ten minutes.

        Syntax: `{p}tunnel [OPTIONS] [<int:channel_id>...]`

        Parameters
        ----------
        _ : dict
            Dict of additional Keyword Args.
        args : List[str]
            List of Positional Arguments supplied after Command.
        src : discord.Message
            The Discord Message that invoked this Command.
        _disconnect, _d : bool
            Remove the current Channel from any connected Tunnels. This will NOT close the Tunnel completely.
        _kill, _k : bool
            Kill the Tunnel connected to the current Channel. This will disconnect ALL channels from the Tunnel.
        """
        if _kill or _k:
            await self.client.kill_tunnel(self.client.get_tunnel(src.channel))
            return "Closed Messaging Tunnel connected to this Channel."

        elif _disconnect or _d:
            await self.client.close_tunnels_to(src.channel)
            return "Disconnected channel from all Messaging Tunnels."

        else:
            dests = [int(x) for x in args if x.isdigit()]
            if not dests:
                return "Must provide at least one integer Channel or User ID."
            await self.client.dig_tunnel(src.channel, *dests)


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMgr
