from datetime import datetime as dt
import getopt
import importlib
from re import compile
import sys
from typing import Dict, get_type_hints, List, Optional, Tuple

from petal.etc import check_types, split, unquote
from petal.exceptions import CommandArgsError, CommandAuthError
from petal.social_integration import Integrated
from petal.types import Args, Src


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


_uquote_1 = compile(r"[‹›‘’]")
_uquote_2 = compile(r"[«»“”„]")

_unquote = lambda s: _uquote_1.sub("'", _uquote_2.sub('"', s))


class CommandRouter(Integrated):
    version = ""

    def __init__(self, client, *a, **kw):
        super().__init__(client)
        self.startup = client.startup

        self.log.info("Loading Command modules...")
        self.engines = []

        # Load all command engines.
        for MODULE in LoadModules:
            # Get the module.
            self.log.info(f"Loading {MODULE.title()} commands...")
            mod = sys.modules.get(__name__ + "." + MODULE, None)
            if mod:
                # Instantiate its command engine.
                cmod = mod.CommandModule(client, self, *a, **kw)
                self.engines.append(cmod)
                setattr(self, MODULE, cmod)
                self.log.ready(f"{MODULE.title()} commands loaded.")
            else:
                self.log.warn(f"FAILED to load {MODULE.title()} commands.")

        self.log.ready("Command modules loaded.")

    def find_command(self, kword, src=None, recursive=True):
        """Find and return a Class Method whose name matches kword."""
        reason = ""
        func = mod_src = None

        for mod in self.engines:
            _func, _submod = mod.get_command(kword)
            if _func:
                func = _func
                mod_src = _submod or mod
                permitted, reason = mod_src.authenticate(src)
                if not src or permitted:
                    # Allow if no Source Message was provided. That would
                    #   indicate that this is not a check meant to be enforced.
                    return mod_src, _func

        if func:
            # The Loop above successfully found a Method for this Command, but
            #   did NOT find that its use was permitted.
            # (If it were found permitted, it would have returned and we would
            #   not be here.)
            if reason in auth_fail_dict:
                raise CommandAuthError(auth_fail_dict[reason])

            elif reason == "denied":
                raise CommandAuthError(
                    mod_src.auth_fail.format(
                        op=mod_src.op,
                        role=(
                            self.config.get(mod_src.role)
                            if mod_src.role
                            else "!! ERROR !!"
                        ),
                        user=src.author.name,
                    )
                )
            else:
                raise CommandAuthError(f"`{reason}`.")
        else:
            # This command is not "real". Check whether it is an alias.
            if recursive:
                alias = self.config.get("aliases", {})
                if kword in alias:
                    return self.find_command(alias[kword], src, False)

            return None, None

    def get_all(self, src: Src = None):
        full = []
        for mod in self.engines:
            if not src or mod.authenticate(src):
                full += mod.get_all()
        return full

    @staticmethod
    def parse(
        args: List[str], shorts: str = "", longs: list = None
    ) -> Tuple[List[str], Dict[str, Optional[str]]]:
        """Just a hinted proxy for GetOpt. Allows commands to more easily use it.
        Also reverses the output because I dislike the normal order, but dont
            tell anyone.
        """
        longs = longs or []
        o, a = getopt.getopt(args, shorts, longs)
        return a, {k: v for k, v in o}

    def parse_from_hinting(
        self, cline: List[str], func: classmethod
    ) -> Tuple[Args, Dict[str, Optional[str]]]:
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
        args: Args = Args([unquote(arg) for arg in args])
        # Opts: Enforce the typing, and if it all passes, send our results back up.
        opts = check_types(opts, hints)

        return args, opts

    async def route(self, command: str, src: Src):
        """Route a command (and the source message) to the correct method of the
            correct module. By this point, the prefix should have been stripped
            away already, leaving a plaintext command.
        """
        command = _unquote(command)
        try:
            cline, msg = split(command)
        except ValueError as e:
            raise CommandArgsError(f"Could not parse arguments: {e}")
        cword = cline.pop(0)

        # Find the method, if one exists.
        engine, func = self.find_command(cword, src)
        print("found")
        if func:
            print("func")
            try:
                args, opts = self.parse_from_hinting(cline, func)
            except getopt.GetoptError as e:
                bad_opt = f"-{e.opt}" if len(e.opt) == 1 else f"--{e.opt}"
                raise CommandArgsError(
                    f"Sorry, {e.msg.replace(bad_opt, f'`{cword} {bad_opt}`')}."
                )
            except TypeError as e:
                raise CommandArgsError(f"Sorry, an option is mistyped: {e}")

            # Execute the method, passing the arguments as a list and the options
            #   as keyword arguments.
            if cword != "argtest" and "|" in args:
                await self.client.send_message(
                    channel=src.channel,
                    message="It looks like you might have tried to separate"
                    " arguments with a pipe (`|`). I will still try to run that"
                    " command, but just so you know, arguments are now"
                    " *space-separated*, and grouped by quotes. Check out the"
                    " `argtest` command for more info.",
                )
            return func(args=args, **opts, msg=msg, src=src)
        print("no func")

    async def run(self, src: Src):
        """Given a message, determine whether it is a command;
        If it is, route it accordingly.
        """
        if src.author != self.client.user and src.content.startswith(
            self.config.prefix
        ):
            # Message begins with the invocation prefix.
            command = src.content[len(self.config.prefix) :]
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

        return f"{d[0]:d} days, {h[0]:d} hours, {m[0]:d} minutes, {s:d} seconds"
