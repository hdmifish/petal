"""Commands module for MINECRAFT-RELATED UTILITIES.
Access: Server Ops"""

from . import core


class CommandsMinecraft(core.Commands):
    auth_fail = "This command requires Operator status on the Minecraft server."

    def authenticate(self, *_):
        return False


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMinecraft
