"""Commands module for BOT ADMINISTRATION.
Access: Config Whitelist"""

from . import core


class CommandsMaintenance(core.Commands):
    auth_fail = "This command is whitelisted."

    def authenticate(self, src):
        return src.author.id in (self.config.get("bot_maintainers") or [])

    async def cmd_list_connected_servers(self, src, **_):
        """
        Return a list of all servers Petal is in.
        """
        for s in self.client.servers:
            await self.client.send_message(
                src.author, src.channel, s.name + " " + s.id
            )

    async def cmd_hello(self, **_):
        """
        Echo.
        """
        return "Hello boss! How's it going?"


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMaintenance
