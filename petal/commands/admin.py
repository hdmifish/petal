"""Commands module for SERVER ADMINISTRATION.
Access: Config Whitelist"""

import discord

from petal.commands import core


class CommandsAdmin(core.Commands):
    auth_fail = "This command is whitelisted."
    whitelist = "server_admins"

    async def cmd_askpatch(self, args, src, **_):
        """Access the AskPatch database.

        Syntax:
        `{p}askpatch submit`
        `{p}askpatch approve`
        `{p}askpatch ignore`
        `{p}askpatch list`
        """
        if not args:
            return "Subcommand required."

        if src.channel.id != self.config.get("motdModChannel"):
            self.log.f(
                "ap",
                str(src.server.id) + " != " + self.config.get("motdModChannel"),
            )
            return "Sorry, you are not permitted to use this"

        subcom = args.pop(0)

        if subcom == "submit":
            response = self.db.submit_motd(src.author.id, " ".join(args[1:]))
            if response is None:
                return "Unable to add to database, ask your bot owner as to why"

            newEmbed = discord.Embed(
                title="Entry " + str(response["num"]),
                description="New question from " + src.author.name,
                colour=0x8738F,
            )
            newEmbed.add_field(name="content", value=response["content"])

            chan = self.client.get_channel(self.config.get("motdModChannel"))
            await self.client.embed(chan, embedded=newEmbed)

            return "Question added to database"

        elif subcom == "approve":
            if src.channel.id != self.config.get("motdModChannel"):
                return "You can't use that here"

            if not args:
                return "You need to specify an entry"
            targ = args[0]

            if not targ.isnumeric():
                return "Entry must be an integer"

            result = self.db.update_motd(int(args[1]))
            if result is None:
                return "No entries exist with id number: " + args[1]

            newEmbed = discord.Embed(
                title="Approved " + str(result["num"]),
                description=result["content"],
                colour=0x00FF00,
            )

            chan = self.client.get_channel(self.config.get("motdModChannel"))
            await self.client.embed(chan, newEmbed)

        elif subcom == "reject":
            if src.channel.id != self.config.get("motdModChannel"):
                return "You can't use that here"

            if not args:
                return "You need to specify an entry"
            targ = args[0]

            if not targ.isnumeric():
                return "Entry must be an integer"

            result = self.db.update_motd(int(args[1]), approve=False)
            if result is None:
                return "No entries exist with id number: " + args[1]

            newEmbed = discord.Embed(
                title="Rejected" + str(result["num"]),
                description=result["content"],
                colour=0xFFA500,
            )

            chan = self.client.get_channel(self.config.get("motdModChannel"))
            await self.client.embed(chan, newEmbed)

        elif subcom == "list":
            count = self.db.motd.count({"approved": True, "used": False})
            return (
                "Patch Asks list is not a thing, scroll up in the channel to see whats up\n"
                + str(count)
                + " available in the queue."
            )

    async def cmd_paforce(self, src, **_):
        """Initiate a forced AskPatch."""
        response = await self.check_pa_updates(force=True)

        self.log.f(
            "pa",
            src.author.name
            + " with ID: "
            + src.author.id
            + " used the force!",
        )
        await self.client.delete_message(src)
        if response is not None:
            return response


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsAdmin
