"""Commands module for MINECRAFT-RELATED UTILITIES.
Access: Server Operators"""

from typing import List

from petal.commands.minecraft import auth
from petal.exceptions import CommandInputError
from petal.util.minecraft import new_entry, type_entry_db


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
                f"You need to include your Minecraft username, or I will not be"
                f" able to find you! Like this: `{self.config.prefix}wlme"
                f" Dinnerbone` :D"
            )

        submission: str = args[0]
        alts: List[type_entry_db] = []

        with self.minecraft.db() as db:
            for entry in db:
                if entry["name"].casefold() == submission.casefold():
                    raise CommandInputError("Username already submitted :D")
                elif int(entry["discord"]) == src.author.id:
                    alts.append(entry)
            else:
                entry_new = new_entry(src.author.id, name_mc=submission)
                db.append(entry_new)

        try:
            card = self.minecraft.card(entry_new, True, title="New Whitelist Request")

            if alts:
                card.add_field(
                    name="Alternate Accounts",
                    value="\n".join(
                        "{name!r} (`{suspended}`)".format(**alt) for alt in alts
                    ),
                    inline=False,
                )

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


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMCPublic
