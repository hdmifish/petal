"""Commands module for SERVER ADMINISTRATION.
Access: Config Whitelist"""

from . import core


class CommandsAdmin(core.Commands):
    def authenticate(self, *_):
        return False


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsAdmin
