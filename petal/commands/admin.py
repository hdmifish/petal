"""Commands module for SERVER ADMINISTRATION.
Access: Config Whitelist"""

import discord

from petal.commands import core


class CommandsAdmin(core.Commands):
    auth_fail = "This command is whitelisted."
    whitelist = "server_admins"

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
                return "You can't use that here"

            if not args:
                return "You need to specify an entry."
            targ = args[0]

            if not targ.isnumeric():
                return "Entry must be an integer."

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
                title="Rejected " + str(result["num"]),
                description=result["content"],
                colour=0xFFA500,
            )

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
            + src.author.id
            + " used the force!",
        )
        await self.client.delete_message(src)
        if response is not None:
            return response


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsAdmin
