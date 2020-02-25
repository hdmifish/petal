"""Commands module for MINECRAFT-RELATED UTILITIES.
Access: Server Operators"""

from petal.commands.minecraft import auth
from petal.exceptions import CommandArgsError, CommandInputError


class CommandsMCAdmin(auth.CommandsMCAuth):
    op = 4

    async def cmd_wlmod(self, args, src, **_):
        """Flag a person to be given a level of operator status.

        Level 1: Can bypass spawn protection.
        Level 2: Can use all singleplayer cheats commands (except /publish, as it is not on servers; along with /debug and /reload) and use command blocks. Command blocks, along with Realms owners/operators, have the same permissions as this level.
        Level 3: Can use most multiplayer-exclusive commands, including /debug, /reload, and commands that manage players (/ban, /op, etc).
        Level 4: Can use all commands including /stop, /save-all, /save-on, /save-off, /forceload add, and /forceload remove.

        Syntax: `{p}wlmod <profile_identifier> (0|1|2|3|4)`
        """
        target = args[0]
        try:
            level = int(args[1])
        except:
            level = -1
        if not 0 <= level <= 4:
            raise CommandArgsError(
                f"You need to specify an Operator level for {target!r} between"
                f" `0` and `4`."
            )

        with self.minecraft.db(target) as db:
            db = list(db)
            if len(db) != 1:
                raise CommandInputError(
                    f"Ambiguous Target: {len(db)} possible targets found."
                )
            elif str(src.author.id) == db[0]["discord"]:
                raise CommandInputError("You cannot change your own Operator status.")
            else:
                db[0]["operator"] = level
                self.minecraft.export()
                return f"{db[0]['name']!r} has been assigned Operator Level {level}."

        # victim = self.minecraft.WLQuery(target)
        # if victim == -7:
        #     return "Could not access database file."
        # elif not victim:
        #     return "No valid target found."
        # elif len(victim) > 1:
        #     return "Ambiguous command: {} possible targets found.".format(
        #         str(len(victim))
        #     )
        # elif str(src.author.id) == victim[0]["discord"]:
        #     return "You cannot change your own Operator status."
        #
        # # rep, doSend, targetid, targetname, wlwin = self.minecraft.WLMod(victim[0], level)
        # rep = self.minecraft.WLMod(victim[0]["discord"], level)
        #
        # return "{} has been granted __Level {} Operator__ status. Return values: `{}`".format(
        #     victim[0]["name"], level, "`, `".join([str(term) for term in rep])
        # )


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMCAdmin
