"""Commands module for SERVER ADMINISTRATION.
Access: Config Whitelist"""

from petal.commands import core
from petal.menu import Menu


class CommandsAdmin(core.Commands):
    auth_fail = "This command is whitelisted."

    def authenticate(self, src):
        return src.author.id in (self.config.get("server_admins") or [])

    async def cmd_menu(self, src, **_):
        m = Menu(self.client, src.channel, src.author, "Choice")
        await m.post()

        m.em.title = "Result: `{}`".format(
            await m.get_option(["asdf", "qwert", "asdfqwert", "qwertyuiop"])
        )
        await m.close()


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsAdmin
