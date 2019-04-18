from datetime import datetime as dt
import getopt
import importlib
import shlex
import sys
from typing import get_type_hints, List, Tuple, Optional as Opt

import discord

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


def split(line: str) -> Tuple[list, str]:
    """Break an input line into a list of tokens, and a "regular" message."""
    # Split the full command line into a list of tokens, each its own arg.
    tokens = shlex.shlex(line, posix=False)
    tokens.quotes += "`"
    # Split the string only on whitespace.
    tokens.whitespace_split = True
    # However, consider a comma to be whitespace so it splits on them too.
    tokens.whitespace += ","
    # Consider a semicolon to denote a comment; Everything after a semicolon
    #   will then be ignored.
    tokens.commenters = ";"

    # Now, find the original string, but only up until the point of a semicolon.
    # Therefore, the following message:
    #   !help -s commands; @person, this is where to see the list
    # will yield a list:   ["help", "-s", "commands"]
    # and a string:         "help -s commands"
    # This will allow commands to consider "the rest of the line" without going
    #   beyond a semicolon, and without having to reconstruct the line from the
    #   list of arguments, which may or may not have been separated by spaces.
    original = shlex.shlex(line, posix=False)
    original.quotes += "`"
    original.whitespace_split = True
    original.whitespace = ""
    original.commenters = ";"

    # Return a list of all the tokens, and the first part of the "original".
    return list(tokens), original.read_token()


def unquote(string: str) -> str:
    for q in "'\"`":
        if string.startswith(q) and string.endswith(q):
            return string[1:-1]
    return string


def check_types(opts: dict, hints: dict) -> dict:
    output = {}
    for opt_name, val in opts.items():
        # opt name back into kwarg name
        kwarg = "_" + opt_name.strip("-").replace("-", "_")
        want = hints[kwarg]
        err = TypeError("{} wants {}, got {}".format(opt_name, want, repr(val)))

        if want == bool:
            print(repr(val))
            val = True

        elif want == Opt[int]:
            if val.lstrip("-").isdigit() and val.count("-") <= 1:
                val = int(val)
            else:
                raise err

        elif want == Opt[float]:
            if val.replace(".", "", 1).lstrip("-").isdigit() and val.count("-") <= 1:
                val = float(val)
            else:
                raise err

        elif want != Opt[type(val)]:
            raise err

        output[kwarg] = val
    return output


auth_fail_dict = {
    "bad user": "Could not find you on the main server.",
    "bad role": "Could not find the correct role on the main server.",
    "bad op": "Command wants MC Operator but is not integrated.",
    "private": "Command cannot be used in DM.",
}


class CommandRouter(Integrated):
    version = ""

    def __init__(self, client, *a, **kw):
        self.startup = dt.utcnow()
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
                else:
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

    async def route(self, command: str, src: discord.Message) -> str:
        """Route a command (and the source message) to the correct method of the
            correct module. By this point, the prefix should have been stripped
            away already, leaving a plaintext command.
        """
        try:
            cline, msg = split(command)
        except ValueError as e:
            return "Could not parse arguments: {}".format(e)
        cword = cline.pop(0)

        # Find the method, if one exists.
        engine, func, denied = self.find_command(cword, src)
        if denied:
            # User is not permitted to use this.
            return "Authentication failure: " + denied

        elif not func and src.id not in self.client.potential_typoed_commands:
            # This is not a command. However, might it have been a typo? Add the
            #   message ID to a deque.
            self.client.potential_typoed_commands.append(src.id)
            return ""

        elif func:
            if src.id in self.client.potential_typoed_commands:
                self.client.potential_typoed_commands.remove(src.id)

            try:
                args, opts = self.parse_from_hinting(cline, func)
            except getopt.GetoptError as e:
                return "Invalid Option: {}".format(e)
            except TypeError as e:
                return "Invalid Type: {}".format(e)

            # Execute the method, passing the arguments as a list and the options
            #     as keyword arguments.
            try:
                if cword != "argtest" and "|" in args:
                    await self.client.send_message(
                        channel=src.channel,
                        message="It looks like you might have tried to separate arguments with a pipe (`|`). I will still try to run that command, but just so you know, arguments are now *space-separated*, and grouped by quotes. Check out the `argtest` command for more info.",
                    )
                return (await func(args=args, **opts, msg=msg, src=src)) or ""
            except Exception as e:
                raise e
                return "Sorry, an exception was raised: `{}` (`{}`)".format(
                    type(e).__name__, e
                )

    async def run(self, src: discord.Message):
        """Given a message, determine whether it is a command;
        If it is, route it accordingly.
        """
        if src.author == self.client.user:
            return
        prefix = self.config.prefix
        if src.content.startswith(prefix):
            # Message begins with the invocation prefix
            command = src.content[len(prefix) :]
            return await self.route(command, src)
            # Remove the prefix and route the command

    @property
    def uptime(self):
        delta = dt.utcnow() - self.startup
        delta = delta.total_seconds()

        d = divmod(delta, 86400)  # days
        h = divmod(d[1], 3600)  # hours
        m = divmod(h[1], 60)  # minutes
        s = m[1]  # seconds

        return "%d days, %d hours, %d minutes, %d seconds" % (d[0], h[0], m[0], s)
