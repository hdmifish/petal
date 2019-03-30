"""Commands module for SERVER ADMINISTRATION.
Access: Config Whitelist"""

from petal.commands import core
from petal.menu import Menu


class CommandsAdmin(core.Commands):
    auth_fail = "This command is whitelisted."

    def authenticate(self, src):
        return src.author.id in (self.config.get("server_admins") or [])

    async def cmd_menu(self, src, **_):
        m = Menu(self.client, src.channel, "Choice", user=src.author)
        await m.post()

        m.em.title = "Result: `{}`".format(
            await m.get_choice(["asdf", "qwert", "asdfqwert", "qwertyuiop"])
        )
        await m.close()

    async def cmd_menu2(self, src, **_):
        m = Menu(self.client, src.channel, "Choice", user=src.author)
        await m.post()

        m.em.title = "Results: `{}`".format(
            await m.get_multi(["asdf", "qwert", "asdfqwert", "qwertyuiop"])
        )
        await m.close()

    async def cmd_poll(self, args, src, question=None, channel=None, time=None, **_):
        if len(args) < 2:
            return "Must provide at least two options."

        if time and not time.isnumeric():
            return "Time must be numeric."
        elif not time:
            duration = 3600
        else:
            duration = int(time)

        title = "Poll"
        if question:
            title += ": " + question

        if channel:
            targ = self.client.get_channel(channel)
        else:
            targ = src.channel
        if not targ:
            return "Invalid Channel"

        poll = Menu(self.client, targ, title=title)
        await poll.post()
        outcome = await poll.get_poll(args, duration)
        return str(outcome)


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsAdmin
