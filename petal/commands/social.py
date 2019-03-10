"""Commands module for SOCIAL MEDIA UTILITIES.
Access: Role-based"""

from . import core


class CommandsSocial(core.Commands):
    auth_fail = "This command requires the Social Media role."

    def authenticate(self, *_):
        return False


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsSocial
