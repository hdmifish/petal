"""Commands module for BOT ADMINISTRATION.
Access: Config Whitelist"""

from . import core


class CommandsMaintenance(core.Commands):
    def authenticate(self, *_):
        return False


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMaintenance
