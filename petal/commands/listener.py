"""Commands module for LISTENER-RELATED UTILITIES.
Access: Role-based"""

from . import core


class CommandsListener(core.Commands):
    def authenticate(self, *_):
        return False


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsListener
