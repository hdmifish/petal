"""Commands module for BOT ADMINISTRATION.
Access: Config Whitelist"""

from . import core


class CommandsMaintenance(core.Commands):
    def authenticate(self, src):
        return src.author.id in (self.config.get("bot_maintainers") or [])

    async def cmd_list_connected_servers(self, __, src, *_):
        """
        hello
        """
        for s in self.client.servers:
            await self.client.send_message(
                src.author, src.channel, s.name + " " + s.id
            )

    async def cmd_hello(self, *_):
        """
        This is a test, its a test
        """
        return "Hello boss! How's it going?"


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMaintenance
