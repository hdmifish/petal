"""Commands module for MINECRAFT-RELATED UTILITIES.
Access: Server Operators"""

from petal.commands import core
from petal.exceptions import CommandOperationError
from petal.mcutil import Minecraft
from petal.util.minecraft import Minecraft as Minecraft_


class CommandsMCAuth(core.Commands):
    auth_fail = "This command requires Operator Level `{op}` on the Minecraft server."

    def __init__(self, mc: Minecraft, *a, **kw):
        super().__init__(*a, **kw)
        self.minecraft: Minecraft = mc
        self.mc2 = Minecraft_(self.client)

    def check(self):
        """Check that the MC config is valid."""
        mclists = (
            self.config.get("minecraftDB"),
            self.config.get("minecraftWL"),
            self.config.get("minecraftOP"),
        )

        if None in mclists:
            raise CommandOperationError(
                "Sorry, Petal has not been configured to manage a Minecraft server."
            )
        mcchan = self.config.get("mc_channel")

        if mcchan is None:
            raise CommandOperationError(
                "Sorry, Petal has not been configured"
                " with a Minecraft Management Channel."
            )
        mcchan = self.client.get_channel(mcchan)

        if mcchan is None:
            raise CommandOperationError(
                "Sorry, the Minecraft Management Channel cannot be found."
            )


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMCAuth
