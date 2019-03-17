"""Commands module for MINECRAFT-RELATED UTILITIES.
Access: Server Operators"""

from petal.commands import core


class CommandsMCAuth(core.Commands):
    auth_fail = "This command requires Operator Level `{op}` on the Minecraft server."

    def __init__(self, mc, *a, **kw):
        super().__init__(*a, **kw)
        self.minecraft = mc

    def authenticate(self, src):
        if 0 <= self.op <= 4:
            return self.minecraft.WLAuthenticate(src, self.op)
        else:
            return True

    def check(self):
        """Check that the MC config is valid."""
        mclists = (
            self.config.get("minecraftDB"),
            self.config.get("minecraftWL"),
            self.config.get("minecraftOP"),
        )
        if None in mclists:
            return (
                "Looks like the bot owner doesn't have the whitelist configured. Sorry."
            )
        mcchan = self.config.get("mc_channel")
        if mcchan is None:
            return (
                "Looks like the bot owner doesn't have an mc_channel configured. Sorry."
            )
        mcchan = self.client.get_channel(mcchan)
        if mcchan is None:
            return (
                "Looks like the bot owner doesn't have an mc_channel configured. Sorry."
            )


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMCAuth
