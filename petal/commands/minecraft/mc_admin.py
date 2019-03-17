"""Commands module for MINECRAFT-RELATED UTILITIES.
Access: Server Operators"""

from petal.commands.minecraft import auth


class CommandsMCAdmin(auth.CommandsMCAuth):
    op = 4

    async def cmd_wlmod(self, args, src, **_):
        """Flag a person to be given a level of operator status.

        Level 1 can: Bypass spawn protection.
        Level 2 can: Use `/clear`, `/difficulty`, `/effect`, `/gamemode`, `/gamerule`, `/give`, `/summon`, `/setblock`, and `/tp`, and can edit command blocks.
        Level 3 can: Use `/ban`, `/deop`, `/whitelist`, `/kick`, and `/op`.
        Level 4 can: Use `/stop`.
        (<https://gaming.stackexchange.com/questions/138602/what-does-op-permission-level-do>)

        Syntax: `{p}wlmod <profile_identifier> (0|1|2|3|4)`
        """
        target = args[0]
        try:
            level = int(args[1])
        except:
            level = -1
        if not 0 <= level <= 4:
            return "You need to specify an op level for {} between `0` and `4`.".format(
                target
            )

        victim = self.minecraft.WLQuery(target)
        if victim == -7:
            return "Could not access database file."
        elif not victim:
            return "No valid target found."
        elif len(victim) > 1:
            return "Ambiguous command: {} possible targets found.".format(
                str(len(victim))
            )
        elif src.author.id == victim[0]["discord"]:
            return "You cannot change your own Operator status."

        # rep, doSend, targetid, targetname, wlwin = self.minecraft.WLMod(victim[0], level)
        rep = self.minecraft.WLMod(victim[0]["discord"], level)

        return "{} has been granted __Level {} Operator__ status. Return values: `{}`".format(
            victim[0]["name"], level, "`, `".join([str(term) for term in rep])
        )


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMCAdmin
