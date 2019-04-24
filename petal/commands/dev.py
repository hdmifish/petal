"""Commands module for BOT ADMINISTRATION.
Access: Config Whitelist"""

from petal.commands import core
from petal.menu import Menu
from petal.util.grammar import pluralize, sequence_words


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

        An Alias is an alternative invocation for a command. If a command is not
        found under the invocation given, the list of aliases is checked, and if
        the invocation is found to be an alias, the request is instead forwarded
        to the command word set under the alias.
        Due to this approach to resolution, if an alias overlaps with a "real"
        command, the real command will __always__ take priority.

        Syntax:
        `{p}calias add <command> <alias>...` - Add aliases so that when `{p}<alias>` is invoked, `{p}<command>` is executed instead.
        `{p}calias clear <command>...` - Remove ALL aliases that lead to specified commands.
        `{p}calias list [<command>]` - List aliases for command. If command is not supplied, list all aliases instead.
        `{p}calias remove <alias>...` - Unset specified aliases.
        `{p}calias trace <alias>...` - Display the command that would be executed if `{p}<alias>` were invoked.
        """
        if not args:
            return "This command requires a subcommand."

        # The first argument passed is a subcommand; What action should be taken.
        mode = args.pop(0).lower()
        if mode not in ("add", "clear", "list", "remove", "trace"):
            return "Invalid subcommand `{}`.".format(mode)

        # Ensure that enough arguments have been supplied.
        if (mode != "list" and not args) or (mode == "add" and len(args) < 2):
            return "Subcommand `{}` requires more arguments.".format(mode)

        out = []
        aliases = self.config.get("aliases")
        p = self.config.prefix

        args = [arg[len(p) :] if arg.startswith(p) else arg for arg in args]

        # Now we can get down to business :D
        if mode == "add":
            cmd = args.pop(0)
            if not self.router.find_command(cmd, recursive=False)[1]:
                return "`{}` cannot be aliased because it is not a valid command.".format(
                    p + cmd
                )
            out.append(
                "To command `{}`, add {} {}:".format(
                    cmd,
                    pluralize(len(args), "es", "", "alias"),
                    sequence_words(["`{}`".format(p + a) for a in args]),
                )
            )

            for alias in args:
                if self.router.find_command(alias, recursive=False)[1]:
                    out.append(
                        f"`{p + alias}` cannot be an alias because it is already a command."
                    )
                elif alias in aliases:
                    out.append(
                        "`{0}{1}` is already an alias for `{0}{2}`.".format(
                            p, alias, aliases[alias]
                        )
                    )
                else:
                    aliases[alias] = cmd
                    out.append(
                        "`{0}{1}` has been added as an alias for `{0}{2}`.".format(
                            p, alias, cmd
                        )
                    )
        elif mode == "clear":
            cmd = args.pop(0)
            if not self.router.find_command(cmd, recursive=False)[1]:
                return f"`{p + cmd}` cannot be cleared of aliases because it is not a valid command."
            out.append(f"From command `{p + cmd}`, remove all aliases:")
            for alias, target in aliases.copy().items():
                if target == cmd:
                    del aliases[alias]
                    out.append(f"Alias `{p + alias}` removed.")
        elif mode == "list":
            if args:
                cmd = args.pop(0)
                if not self.router.find_command(cmd, recursive=False)[1]:
                    return f"`{p + cmd}` cannot have aliases listed because it is not a valid command."
                out.append(f"List of aliases for command `{p + cmd}`:")
                for alias, target in aliases.items():
                    if target == cmd:
                        out.append(f"`{p + alias}`")
            else:
                out.append("List of aliases:")
                out += [
                    "`{}` -> `{}`".format(p + alias, p + cmd)
                    for alias, cmd in aliases.items()
                ]
        elif mode == "remove":
            out.append(
                "Remove {} {}:".format(
                    pluralize(len(args), "es", "", "alias"),
                    sequence_words(["`{}`".format(p + a) for a in args]),
                )
            )
            for alias in args:
                if alias in aliases:
                    del aliases[alias]
                    out.append("Alias `{}` removed.".format(p + alias))
                else:
                    out.append("`{}` is not a valid alias.".format(p + alias))
        elif mode == "trace":
            out.append(
                "Trace {} {}:".format(
                    pluralize(len(args), "es", "", "alias"),
                    sequence_words(["`{}`".format(p + a) for a in args]),
                )
            )
            for alias in args:
                if alias in aliases:
                    out.append("`{}` -> `{}`".format(p + alias, p + aliases[alias]))
                else:
                    out.append("`{}` is not a valid alias.".format(p + alias))

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

        # m.em.title = "Result: `{}`".format(
        #     await m.get_one(["asdf", "qwert", "asdfqwert", "qwertyuiop"])
        # )
        # await m.close()
        await m.add_result(
            await m.get_one(["asdf", "qwert", "asdfqwert", "qwertyuiop"])
        )
        await m.add_result(
            await m.get_one(["zxcv", "qazwsx", "yuiop", "poiuytrewq"]), overwrite=0
        )
        await m.add_result(
            await m.get_one(["aaaaaaaaa", "wysiwyg", "zzz"]), overwrite=0
        )

    async def cmd_menu2(self, src, **_):
        m = Menu(self.client, src.channel, "Choice", user=src.author)

        # m.em.title = "Results: `{}`".format(
        #     await m.get_multi(["asdf", "qwert", "asdfqwert", "qwertyuiop"])
        # )
        # await m.close()
        await m.add_result(
            "\n".join(await m.get_multi(["asdf", "qwert", "asdfqwert", "qwertyuiop"]))
        )

    async def cmd_bool(self, src, **_):
        m = Menu(self.client, src.channel, "Choice", user=src.author)
        m.add_result(str(await m.get_bool()))

    async def cmd_poll(
        self, args, src, _question: str = "", _channel: str = "", _time: int = 0, **_
    ):
        if len(args) < 2:
            return "Must provide at least two options."

        duration = _time if _time > 0 else 3600

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

    async def cmd_vote(
        self, src, _question: str = "", _channel: str = "", _time: int = 0, **_
    ):
        duration = _time if _time > 0 else 3600

        title = "Vote"
        if _question:
            title += ": " + _question

        if _channel:
            targ = self.client.get_channel(_channel)
        else:
            targ = src.channel
        if not targ:
            return "Invalid Channel"

        poll = Menu(self.client, targ, title=title)
        outcome = await poll.get_vote(duration)
        return str(outcome)

    async def cmd_bytes(self, src, **_):
        """Encode the message provided into a Bytes object. Then, print it.

        Debug utility to sanity check **__exactly__** what is received over Discord.

        Syntax: `{p}bytes <literally anything>...`
        """
        raw = src.content.encode("utf-8")
        return "`discord.Message.content`:```{}```Hexadecimal:```{}```".format(
            repr(raw)[2:-1], raw.hex()
        )


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMaintenance
