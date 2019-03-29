"""Commands module for SERVER ADMINISTRATION.
Access: Config Whitelist"""

from time import sleep

from petal.commands import core
from petal.menu import Menu


class CommandsAdmin(core.Commands):
    auth_fail = "This command is whitelisted."

    def authenticate(self, src):
        return src.author.id in (self.config.get("server_admins") or [])

    async def cmd_menu(self, args, src, **_):
        if not args:
            return "need arg"

        m = Menu(self.client, src.channel, args[0])
        await m.post()

        sleep(3)

        m.retitle("asdfqwert")
        await m.post()


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsAdmin
