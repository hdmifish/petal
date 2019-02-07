"""Commands module for MINECRAFT-RELATED UTILITIES.
Access: Server Ops"""

from . import core


class CommandsMinecraft(core.Commands):
    def authenticate(self, *_):
        return False


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMinecraft
