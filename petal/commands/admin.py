"""Commands module for SERVER ADMINISTRATION.
Access: Config Whitelist"""

from . import core


class CommandsAdmin(core.Commands):
    def authenticate(self, src):
        return src.author.id in (self.config.get("server_admins") or [])


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsAdmin
