"""Commands module for NON-ADMINISTRATOR HIGH-LEVEL UTILITIES.
Access: Role-based"""

import discord

from petal.commands import core


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
            return "Subcommand required."

        subcom = args.pop(0)

        if subcom == "submit":
            # msg = msg.split(maxsplit=2)
            # if len(msg) < 3:
            #     return "Question cannot be empty."
            # msg = msg[2]
            if not args:
                return "Question cannot be empty."
            elif len(args) > 1:
                return "Question should be put in quotes."
            else:
                msg = args[0]

            response = self.db.submit_motd(src.author.id, msg)
            if response is None:
                return "Unable to add to database, ask your bot owner as to why."

            newEmbed = discord.Embed(
                title="Entry " + str(response["num"]),
                description="New question from " + src.author.name,
                colour=0x8738F,
            )
            newEmbed.add_field(name="content", value=response["content"])

            chan = self.client.get_channel(self.config.get("motdModChannel"))
            await self.client.embed(chan, embedded=newEmbed)

            return "Question added to database."

        elif subcom == "approve":
            if src.channel.id != self.config.get("motdModChannel"):
                return "You can't use that here."
            if not args:
                return "You need to specify an entry."
            if not all([x.isdigit() for x in args]):
                return "Every entry must be an integer."

            for targ in args:
                result = self.db.update_motd(int(targ), approve=True)
                if result is None:
                    return "No entries exist with id number: " + targ

                newEmbed = discord.Embed(
                    title="Approved " + str(result["num"]),
                    description=result["content"],
                    colour=0x00FF00,
                ).add_field(name="Submitted by", value="<@{}>".format(result["author"]))

                chan = self.client.get_channel(self.config.get("motdModChannel"))
                await self.client.embed(chan, newEmbed)

        elif subcom == "reject":
            if src.channel.id != self.config.get("motdModChannel"):
                return "You can't use that here."
            if not args:
                return "You need to specify an entry."
            if not all([x.isdigit() for x in args]):
                return "Every entry must be an integer."

            for targ in args:
                result = self.db.update_motd(int(targ), approve=False)
                if result is None:
                    return "No entries exist with id number: " + targ

                newEmbed = discord.Embed(
                    title="Rejected " + str(result["num"]),
                    description=result["content"],
                    colour=0xFFA500,
                ).add_field(name="Submitted by", value="<@{}>".format(result["author"]))

                chan = self.client.get_channel(self.config.get("motdModChannel"))
                await self.client.embed(chan, newEmbed)

        elif subcom == "count":
            count = self.db.motd.count({"approved": True, "used": False})
            return "Question queue currently contains `{}` entries.".format(count)

        else:
            return "Unrecognized subcommand."

    async def cmd_paforce(self, src, **_):
        """Initiate a forced AskPatch."""
        response = await self.router.check_pa_updates(force=True)

        self.log.f(
            "pa",
            src.author.name
            + " with ID: "
            + str(src.author.id)
            + " used the force!",
        )
        await src.delete()
        if response is not None:
            return response

    async def cmd_tunnel(
        self,
        args,
        src,
        _disconnect: bool = False,
        _d: bool = False,
        _kill: bool = False,
        _k: bool = False,
        **_
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
