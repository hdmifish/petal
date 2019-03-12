"""SPECIALIZED commands module for USER-DEFINED COMMANDS.
Access: Public"""

from . import core


class CommandsCustom(core.Commands):
    auth_fail = "This command is public. If you are reading this, something went wrong."

    def authenticate(self, *_):
        return True


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsCustom
