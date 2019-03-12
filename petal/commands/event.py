"""Commands module for EVENTS UTILITIES.
Access: Role-based"""

from . import core


class CommandsEvent(core.Commands):
    auth_fail = "This command requires the Events role."

    def authenticate(self, src):
        return self.check_user_has_role(src.author, "canPost")


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsEvent
