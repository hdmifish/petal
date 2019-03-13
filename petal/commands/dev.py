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

    async def cmd_blacklist(self, args, src, **_):
        """
        Prevent user of given ID(s) from using Petal.

        The user will not be able to access any features of Petal, but will still be logged in the member database. Multiple IDs may be provided, space-separated.

        Syntax: `{p}blacklist <user_ID> [<user_ID> [<user_ID> [...]]]`
        """
        if not args:
            return "Provide at least one User ID."
        else:
            for uid in args:
                mem = self.get_member(src, uid)
                if mem is None:
                    return "Couldnt find user with ID: " + uid

                if mem.id in self.config.blacklist:
                    self.config.blacklist.remove(mem.id)
                    return mem.name + " was removed from the blacklist."
                else:
                    self.config.blacklist.append(mem.id)
                    return mem.name + " was blacklisted."


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMaintenance
