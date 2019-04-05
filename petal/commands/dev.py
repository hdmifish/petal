"""Commands module for BOT ADMINISTRATION.
Access: Config Whitelist"""

from petal.commands import core
from petal.menu import Menu


class CommandsMaintenance(core.Commands):
    auth_fail = "This command is whitelisted."
    whitelist = "bot_maintainers"

    async def cmd_servers(self, src, **_):
        """Return a list of all servers Petal is in."""
        for s in self.client.servers:
            await self.client.send_message(src.author, src.channel, s.name + " " + s.id)

    async def cmd_hello(self, **_):
        """Echo."""
        return "Hello boss! How's it going?"

    async def cmd_forcesave(self, **_):
        """Force configuration file save."""
        self.config.save(vb=1)
        return "Saved."

    async def cmd_forceload(self, **_):
        """Force configuration file reload."""
        self.config.load()
        return "Loaded config file."

    async def cmd_calias(self, args, **_):
        """Manipulate command aliases.

        If an alias overlaps with a "real" command, the real command will __always__ take priority.

        Syntax:
        `{p}calias add <command> <alias>...` - Add an alias so that when `{p}<alias>` is invoked, `{p}<command>` is executed instead.
        `{p}calias list <command>`
        `{p}calias clear <command>...`
        `{p}calias remove <alias>...`
        """
        if not args:
            return "This command requires a subcommand."

        # The first argument passed is a subcommand; What action should be taken.
        mode = args.pop(0).lower()
        if mode not in ("add", "list", "clear", "remove"):
            return "Invalid subcommand `{}`.".format(mode)

        # Ensure that enough arguments have been supplied.
        if not args or (mode == "add" and len(args) < 2):
            return "Subcommand `{}` requires more arguments.".format(mode)

        out = []
        aliases = self.config.get("aliases")

        # Now we can get down to business :D
        if mode == "add":
            cmd = args.pop(0)
            if not self.router.find_command(cmd, recursive=False)[1]:
                return "`{}{}` cannot be aliased because it is not a valid command.".format(
                    self.config.prefix, cmd
                )

            for alias in args:
                if self.router.find_command(alias, recursive=False)[1]:
                    out.append(
                        "`{}{}` cannot be an alias because it is already a command.".format(
                            self.config.prefix, alias
                        )
                    )
                elif alias in aliases:
                    out.append(
                        "`{}{}` is already an alias for `{}{}`.".format(
                            self.config.prefix,
                            alias,
                            self.config.prefix,
                            aliases[alias],
                        )
                    )
                else:
                    aliases[alias] = cmd
                    out.append(
                        "`{}{}` has been added as an alias for `{}{}`.".format(
                            self.config.prefix, alias, self.config.prefix, cmd
                        )
                    )
        elif mode == "list":
            pass
        elif mode == "clear":
            pass
        elif mode == "remove":
            pass

        self.config.save()
        return "\n".join(out)

    async def cmd_blacklist(self, args, src, **_):
        """Prevent user of given ID(s) from using Petal.

        The user will not be able to access any features of Petal, but will still be logged in the member database. Multiple IDs may be provided, space-separated.

        Syntax: `{p}blacklist <user_ID>...`
        """
        if not args:
            return "Provide at least one User ID."
        else:
            report = []
            for uid in args:
                mem = self.get_member(src, uid)
                if mem is None:
                    report.append("Couldnt find user with ID: " + uid)

                if mem.id in self.config.blacklist:
                    self.config.blacklist.remove(mem.id)
                    report.append(mem.name + " was removed from the blacklist.")
                else:
                    self.config.blacklist.append(mem.id)
                    report.append(mem.name + " was blacklisted.")
            self.config.save()
            return "\n".join(report)

    async def cmd_menu(self, src, **_):
        m = Menu(self.client, src.channel, "Choice", user=src.author)

        m.em.title = "Result: `{}`".format(
            await m.get_choice(["asdf", "qwert", "asdfqwert", "qwertyuiop"])
        )
        await m.close()

    async def cmd_menu2(self, src, **_):
        m = Menu(self.client, src.channel, "Choice", user=src.author)

        m.em.title = "Results: `{}`".format(
            await m.get_multi(["asdf", "qwert", "asdfqwert", "qwertyuiop"])
        )
        await m.close()

    async def cmd_poll(
        self, args, src, _question: str = "", _channel: str = "", _time: int = 0, **_
    ):
        if len(args) < 2:
            return "Must provide at least two options."

        duration = _time or 3600

        title = "Poll"
        if _question:
            title += ": " + _question

        if _channel:
            targ = self.client.get_channel(_channel)
        else:
            targ = src.channel
        if not targ:
            return "Invalid Channel"

        poll = Menu(self.client, targ, title=title)
        outcome = await poll.get_poll(args, duration)
        return str(outcome)


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMaintenance
