"""Commands module for BOT ADMINISTRATION.
Access: Config Whitelist
"""

from petal.checks import all_checks, Messages
from petal.commands import core
from petal.exceptions import CommandArgsError, CommandInputError
from petal.menu import Menu
from petal.util import fmt, questions
from petal.util.grammar import pluralize, sequence_words


class CommandsMaintenance(core.Commands):
    auth_fail = "This command is whitelisted."
    whitelist = "bot_maintainers"

    async def cmd_guilds(self, **_):
        """Return a list of all guilds Petal is in."""
        for g in self.client.guilds:
            yield f"{g.name} :: `{g.id}`"

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
            raise CommandInputError("This command requires a subcommand.")

        # The first argument passed is a subcommand; What action should be taken.
        mode = args.pop(0).lower()
        if mode not in ("add", "clear", "list", "remove", "trace"):
            raise CommandInputError(f"Invalid subcommand `{mode}`.")

        # Ensure that enough arguments have been supplied.
        if (mode != "list" and not args) or (mode == "add" and len(args) < 2):
            raise CommandInputError(f"Subcommand `{mode}` requires more arguments.")

        aliases = self.config.get("aliases")
        p = self.config.prefix

        args = [arg[len(p) :] if arg.startswith(p) else arg for arg in args]

        # Now we can get down to business :D
        if mode == "add":
            cmd = args.pop(0)
            if not self.router.find_command(cmd, recursive=False)[1]:
                raise CommandInputError(
                    f"`{p + cmd}` cannot be aliased because it is not a valid"
                    f" command."
                )
            yield "To command `{}`, add {} {}:".format(
                cmd,
                pluralize(len(args), "alias", "es"),
                sequence_words(["`{}`".format(p + a) for a in args]),
            )

            for alias in args:
                if self.router.find_command(alias, recursive=False)[1]:
                    yield (
                        f"`{p + alias}` cannot be an alias because it is"
                        f" already a command."
                    )
                elif alias in aliases:
                    yield "`{0}{1}` is already an alias for `{0}{2}`.".format(
                        p, alias, aliases[alias]
                    )
                else:
                    aliases[alias] = cmd
                    yield "`{0}{1}` has been added as an alias for `{0}{2}`.".format(
                        p, alias, cmd
                    )

        elif mode == "clear":
            cmd = args.pop(0)
            if not self.router.find_command(cmd, recursive=False)[1]:
                raise CommandInputError(
                    f"`{p + cmd}` cannot be cleared of aliases because it is"
                    f" not a valid command."
                )
            yield f"From command `{p + cmd}`, remove all aliases:"
            for alias, target in aliases.copy().items():
                if target == cmd:
                    del aliases[alias]
                    yield f"Alias `{p + alias}` removed."

        elif mode == "list":
            if args:
                cmd = args.pop(0)
                if not self.router.find_command(cmd, recursive=False)[1]:
                    raise CommandInputError(
                        f"`{p + cmd}` cannot have aliases listed because it is"
                        f" not a valid command."
                    )
                yield f"List of aliases for command `{p + cmd}`:"
                for alias, target in aliases.items():
                    if target == cmd:
                        yield f"`{p + alias}`"
            else:
                yield "List of aliases:"
                for alias, cmd in aliases.items():
                    yield f"`{p + alias}` -> `{p + cmd}`"

        elif mode == "remove":
            yield "Remove {} {}:".format(
                pluralize(len(args), "alias", "es"),
                sequence_words([f"`{p + a}`" for a in args]),
            )
            for alias in args:
                if alias in aliases:
                    del aliases[alias]
                    yield f"Alias `{p + alias}` removed."
                else:
                    yield f"`{p + alias}` is not a valid alias."

        elif mode == "trace":
            yield "Trace {} {}:".format(
                pluralize(len(args), "alias", "es"),
                sequence_words([f"`{p + a}`" for a in args]),
            )
            for alias in args:
                if alias in aliases:
                    yield f"`{p + alias}` -> `{p + aliases[alias]}`"
                else:
                    yield f"`{p + alias}` is not a valid alias."

        self.config.save()

    async def cmd_blacklist(self, args, src, **_):
        """Prevent user of given ID(s) from using Petal.

        The user will not be able to access any features of Petal, but will still be logged in the member database. Multiple IDs may be provided, space-separated.

        Syntax: `{p}blacklist <user_ID>...`
        """
        if not args:
            raise CommandArgsError("Provide at least one User ID.")
        else:
            for uid in args:
                if not uid.isdigit():
                    yield f"`{uid}` is not a valid ID."

                mem = self.get_member(src, int(uid))

                if mem is None:
                    yield f"Couldnt find user with ID `{uid}`"
                elif str(mem.id) in self.config.blacklist:
                    self.config.blacklist.remove(str(mem.id))
                    yield f"`{fmt.userline(mem.name)}` was removed from the blacklist."
                else:
                    self.config.blacklist.append(str(mem.id))
                    yield f"`{fmt.userline(mem.name)}` was blacklisted."

            self.config.save()

    async def cmd_menu(self, src, **_):
        m = Menu(self.client, src.channel, "Choice", "Test Function", user=src.author)

        m.add_section(
            await m.get_one(["asdf", "qwert", "asdfqwert", "qwertyuiop"]) or "(None)"
        )
        await m.post()
        m.add_section(
            await m.get_one(["zxcv", "qazwsx", "yuiop", "poiuytrewq"]) or "(None)",
            # overwrite=0,
        )
        await m.post()
        m.add_section(
            await m.get_one(["aaaaaaaaa", "wysiwyg", "zzz"])
            or "(None)"  # , overwrite=0,
        )
        await m.post()

    async def cmd_menu2(self, src, **_):
        m = Menu(self.client, src.channel, "Choice", "Test Function", user=src.author)

        m.add_section(
            "\n".join(await m.get_multi(["asdf", "qwert", "asdfqwert", "qwertyuiop"]))
            or "(None)"
        )
        await m.post()

    async def cmd_bool(self, src, **_):
        m = Menu(self.client, src.channel, "Choice", "Test Function", user=src.author)
        m.add_section(repr(await m.get_bool()))
        await m.post()

    async def cmd_repeat(self, src, **_):
        return "You said:```{}```".format(
            (
                await Messages.waitfor(
                    self.client,
                    all_checks(
                        Messages.by_user(src.author), Messages.in_channel(src.channel)
                    ),
                    channel=src.channel,
                    prompt="say thing",
                )
            ).content
        )

    async def cmd_bool2(self, **_):
        title = yield questions.ChatReply("Enter text for boolean:")
        conf = yield questions.ConfirmMenu("Boolean", title)
        yield str(conf)


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMaintenance
