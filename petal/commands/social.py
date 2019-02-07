"""Commands module for SOCIAL MEDIA UTILITIES.
Access: Role-based"""

from . import core


class CommandsSocial(core.Commands):
    def authenticate(self, *_):
        return False


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsSocial
