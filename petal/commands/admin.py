"""Commands module for SERVER ADMINISTRATION.
Access: Config Whitelist"""

from petal.commands import core


class CommandsAdmin(core.Commands):
    auth_fail = "This command is whitelisted."

    def authenticate(self, src):
        return src.author.id in (self.config.get("server_admins") or [])


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsAdmin
