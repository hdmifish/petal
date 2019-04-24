"""Commands module for GUILD ADMINISTRATION.
Access: Config Whitelist"""

from petal.commands import core


class CommandsAdmin(core.Commands):
    auth_fail = "This command is whitelisted."
    whitelist = "guild_admins"


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsAdmin
