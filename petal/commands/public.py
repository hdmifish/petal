"""Commands module for PUBLIC COMMANDS.
Access: Public"""

from . import core


class CommandsPublic(core.Commands):
    def authenticate(self, *_):
        return True


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsPublic
