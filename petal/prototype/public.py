from . import core


class CommandsPublic(core.Commands):
    pass


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsPublic
