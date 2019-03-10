"""Commands module for LISTENER-RELATED UTILITIES.
Access: Role-based"""

import discord

from . import core


class CommandsListener(core.Commands):
    def authenticate(self, src):
        target = discord.utils.get(src.author.server.roles, name="Listener")
        if target is None:
            self.log.err("Listener role does not exist")
            return False
        else:
            if target in src.author.roles:
                return True
            else:
                return False


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsListener
