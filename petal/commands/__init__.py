from asyncio import ensure_future as create_task, sleep
from datetime import datetime as dt
import getopt
import importlib
import sys
from typing import get_type_hints, List, Tuple

import discord

from petal.etc import check_types, get_output, split, unquote
from petal.exceptions import (
    CommandArgsError,
    CommandAuthError,
    CommandInputError,
    CommandOperationError,
)
from petal.social_integration import Integrated


# List of modules to load; All Command-providing modules should be included (NOT "core").
# Order of this list is the order in which commands will be searched. First occurrence
#     the user is permitted to access will be run.
LoadModules = [
    "sudo",
    "dev",
    "admin",
    "manager",
    "mod",
    "listener",
    "social",
    "event",
    "minecraft",
    "util",
    "public",
    "custom",
]

for module in LoadModules:
    # Import everything in the list above.
    importlib.import_module("." + module, package=__name__)

auth_fail_dict = {
    "bad user": "Could not find you on the main server.",
    "bad role": "Could not find the correct role on the main server.",
    "bad op": "Command wants MC Operator but is not integrated.",
    "private": "Command cannot be used in DM.",
}


class CommandPending:
    """Class for storing a Command while it is executed. If it cannot be
        executed, it will be saved for a set time limit. During that timeout
        period, if the message is edited, the Command will attempt to rerun.
    """

    def __init__(self, dict_, output, router, src):
        self.dict_ = dict_
        self.output = output
        self.router = router
        self.src: discord.Message = src

        self.active = False
        self.reply: discord.Message = None
        self.waiting = create_task(self.wait())

    async def run(self):
        """Try to execute this command. Return True if execution is carried out
            successfully, False otherwise. Potentially, remove self.
        """
        if not self.active:
            # Command is not valid for execution. Cease.
            return False

        if self.reply:
            await self.reply.delete()
            self.reply = None

        try:
            # Run the Command through the Router.
            response = await self.router.run(self.src)
        except CommandArgsError as e:
            # Arguments not valid. Cease, but do not necessarily desist.
            self.reply = await self.src.channel.send(e)
        except CommandAuthError as e:
            # Access denied. Cease and desist.
            self.unlink()
            await self.src.channel.send("Sorry, not permitted; {}".format(e))
        except CommandInputError as e:
            # Input not valid. Cease, but do not necessarily desist.
            self.reply = await self.src.channel.send("Bad input: {}".format(e))
        except CommandOperationError as e:
            # Command could not finish, but was accepted. Cease and desist.
            self.unlink()
            await self.src.channel.send("Command failed; {}".format(e))
        except Exception as e:
            # Command could not finish. We do not know why, so play it safe.
            self.unlink()
            await self.src.channel.send(
                "Sorry, something went wrong, but I do not know what"
                + (": `{}`".format(e) if str(e) else ".")
            )
        else:
            # Command routed without errors.
            if response is not None:
                # Command executed successfully. Desist and respond.
                self.unlink()
                self.router.config.get("stats")["comCount"] += 1
                await self.output(self.src, response)
                return True
            else:
                # Command was not executed. Cease.
                return False
        finally:
            return False

    async def wait(self):
        self.active = True
        self.dict_[self.src.id] = self
        await sleep(60)
        self.unlink()

    def unlink(self):
        """Prevent self from being executed."""
        self.active = False
        if self.src.id in self.dict_:
            del self.dict_[self.src.id]


class CommandRouter(Integrated):
    version = ""

    def __init__(self, client, *a, **kw):
        super().__init__(client)

        self.log.info("Loading Command modules...")
        self.engines = []

        # Load all command engines.
        for MODULE in LoadModules:
            # Get the module.
            self.log.info("Loading {} commands...".format(MODULE.capitalize()))
            mod = sys.modules.get(__name__ + "." + MODULE, None)
            if mod:
                # Instantiate its command engine.
                cmod = mod.CommandModule(client, self, *a, **kw)
                self.engines.append(cmod)
                setattr(self, MODULE, cmod)
                self.log.ready("{} commands loaded.".format(MODULE.capitalize()))
            else:
                self.log.warn("FAILED to load {} commands.".format(MODULE.capitalize()))

        self.log.ready("Command modules loaded.")

    def find_command(self, kword, src=None, recursive=True):
        """
        Find and return a class method whose name matches kword.
        """
        denied = ""
        for mod in self.engines:
            func, submod = mod.get_command(kword)
            if not func:
                continue
            else:
                mod_src = submod or mod
                permitted, reason = mod_src.authenticate(src)
                if not src or permitted:
                    return mod_src, func, False
                else:  # src and not permitted
                    if reason in auth_fail_dict:
                        denied = auth_fail_dict[reason]
                    elif reason == "denied":
                        denied = mod_src.auth_fail.format(
                            op=mod_src.op,
                            role=(
                                self.config.get(mod_src.role)
                                if mod_src.role
                                else "!! ERROR !!"
                            ),
                            user=src.author.name,
                        )
                    else:
                        denied = "`{}`.".format(reason)
                    raise CommandAuthError(denied)

        # This command is not "real". Check whether it is an alias.
        alias = dict(self.config.get("aliases")) or {}
        if recursive and kword in alias:
            return self.find_command(alias[kword], src, False)

        return None, None, denied

    def get_all(self, src=None):
        full = []
        for mod in self.engines:
            if not src or mod.authenticate(src):
                full += mod.get_all()
        return full

    def parse(
        self, args: List[str], shorts: str = "", longs: list = None
    ) -> Tuple[list, dict]:
        """Just a hinted proxy for GetOpt. Allows commands to more easily use it.
        Also reverses the output because I dislike the normal order, but dont
            tell anyone.
        """
        longs = longs or []
        o, a = getopt.getopt(args, shorts, longs)
        return a, {k: v for k, v in o}

    def parse_from_hinting(
        self, cline: List[str], func: classmethod
    ) -> Tuple[list, dict]:
        """cline is a List of Strings, and func is a Command Method. Generate a
            Dict of Types that can be accepted by the various kwargs of func.
            With that information, use Getopt to break cline down into
            Arguments, Options, and Values that can be passed to func.

        Using this system, a Command Method can specify the types acceptable for
            its Options, and Users can pass data as part of a String that gets
            automatically converted into the correct Type.
        """
        hints = get_type_hints(func)
        shorts = ""
        longs = []

        # First, convert the method typing hints into something Getopt knows.
        for opt_name, opt_type in hints.items():
            if not opt_name.startswith("_"):
                continue
            # "_option_name" -> "option-name"
            opt_name = opt_name[1:].replace("_", "-")
            if len(opt_name) == 1:
                if opt_type != bool:
                    opt_name += ":"
                shorts += opt_name
            else:
                if opt_type != bool:
                    opt_name += "="
                longs.append(opt_name)

        # Run the line through Getopt using the option expectations we just generated.
        args, opts = self.parse(cline, shorts, longs)

        # Args: Remove any outermost quotes.
        args = [unquote(arg) for arg in args]
        # Opts: Enforce the typing, and if it all passes, send our results back up.
        opts = check_types(opts, hints)

        return args, opts

    async def route(self, command: str, src: discord.Message):
        """Route a command (and the source message) to the correct method of the
            correct module. By this point, the prefix should have been stripped
            away already, leaving a plaintext command.
        """
        try:
            cline, msg = split(command)
        except ValueError as e:
            raise CommandArgsError("Could not parse arguments: {}".format(e))
        cword = cline.pop(0)

        # Find the method, if one exists.
        engine, func, denied = self.find_command(cword, src)
        if denied:
            # User is not permitted to use this.
            # TODO: This is redundant. Remove all references to `denied` outside of `find_command`.
            raise CommandAuthError(denied)
        elif func:
            try:
                args, opts = self.parse_from_hinting(cline, func)
            except getopt.GetoptError as e:
                bad_opt = ("-{}" if len(e.opt) == 1 else "--{}").format(e.opt)
                raise CommandArgsError(
                    "Sorry, {}.".format(
                        e.msg.replace(bad_opt, "`{} {}`".format(cword, bad_opt))
                    )
                )
            except TypeError as e:
                raise CommandArgsError("Sorry, an option is mistyped: {}".format(e))

            # Execute the method, passing the arguments as a list and the options
            #     as keyword arguments.
            if cword != "argtest" and "|" in args:
                await self.client.send_message(
                    channel=src.channel,
                    message="It looks like you might have tried to separate arguments with a pipe (`|`). I will still try to run that command, but just so you know, arguments are now *space-separated*, and grouped by quotes. Check out the `argtest` command for more info.",
                )
            return await get_output(func(args=args, **opts, msg=msg, src=src))

    async def run(self, src: discord.Message):
        """Given a message, determine whether it is a command;
        If it is, route it accordingly.
        """
        if src.author == self.client.user:
            return
        prefix = self.config.prefix
        if src.content.startswith(prefix):
            # Message begins with the invocation prefix.
            command = src.content[len(prefix) :]
            # Remove the prefix and route the command.
            return await self.route(command, src)

    @property
    def uptime(self):
        delta = dt.utcnow() - self.client.startup
        delta = delta.total_seconds()

        d = divmod(delta, 86400)  # days
        h = divmod(d[1], 3600)  # hours
        m = divmod(h[1], 60)  # minutes
        s = m[1]  # seconds

        return "%d days, %d hours, %d minutes, %d seconds" % (d[0], h[0], m[0], s)
