"""Commands module for MINECRAFT-RELATED UTILITIES.
Access: Server Operators"""

from petal.commands.minecraft import auth
from petal.exceptions import CommandInputError
from petal.util.minecraft import new_entry


class CommandsMCPublic(auth.CommandsMCAuth):
    auth_fail = "This command is public. If you are reading this, something went wrong."
    op = -1

    async def cmd_wlme(self, args, src, **_):
        """Submit your Minecraft username to be whitelisted on the community server.

        The whitelist is curated and managed by Petal for convenience, security, and consistency.

        Syntax: `{p}wlme <minecraft_username>`
        """
        if not args:
            raise CommandInputError(
                "You need to include your Minecraft username, or I will not be"
                " able to find you! Like this: `{}wlme Notch` :D".format(
                    self.config.prefix
                )
            )

        submission: str = args[0]

        with self.mc2.db() as db:
            for entry in db:
                if entry["name"].casefold() == submission.casefold():
                    raise CommandInputError("Username already submitted :D")
            else:
                entry = new_entry(src.author.id, name_mc=submission)
                db.append(entry)

        try:
            card = self.mc2.card(entry, True, title="New Whitelist Request")
            chan = self.client.get_channel(self.config.get("mc_channel"))
            await chan.send(embed=card)
        except:
            return (
                "Your Whitelist Request was submitted, but I could not post it"
                " in the Staff Channel. You should DM someone to have them"
                " check it manually."
            )
        else:
            return "Your Whitelist Request has been submitted."

        # reply, uuid = self.minecraft.WLRequest(submission, str(src.author.id))
        #
        # if reply == 0:
        #     self.log.f(
        #         "wl+",
        #         f"{src.author.name}#{src.author.discriminator} ({src.author.id}) creates NEW ENTRY for '{src.content[len(self.config.prefix) + 4:]}'",
        #     )
        #
        #     wlreq = await self.client.send_message(
        #         channel=self.client.get_channel(self.config.get("mc_channel")),
        #         message="`<request loading...>`",
        #     )
        #
        #     if wlreq:
        #         await wlreq.edit(
        #             content="Whitelist Request from: `"
        #             + src.author.name
        #             + "#"
        #             + src.author.discriminator
        #             + "` with request: "
        #             + submission
        #             + "\nTaggable: <@"
        #             + str(src.author.id)
        #             + ">\nDiscord ID:  "
        #             + str(src.author.id)
        #             + "\nMojang UID:  "
        #             + uuid,
        #         )
        #         return "Your whitelist request has been successfully submitted :D"
        #     else:
        #         return "Your request has been submitted, but I could not post the notification. You should DM a member of the Minecraft staff and ask them to check it manually."
        # elif reply == -1:
        #     return "No need, you are already whitelisted :D"
        # elif reply == -2:
        #     return "That username has already been submitted for whitelisting :o"
        # # elif reply == -:
        # #     return "Error (No Description Provided)"
        # elif reply == -7:
        #     return "Could not access the database file D:"
        # elif reply == -8:
        #     return (
        #         "That does not seem to be a valid Minecraft username D: "
        #         + "DEBUG: "
        #         + submission
        #     )
        # elif reply == -9:
        #     return "Sorry, iso and/or dav left in an unfinished function >:l"
        # else:
        #     return "Nondescript Error ({})".format(reply)


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMCPublic
