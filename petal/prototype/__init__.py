import importlib
import itertools
import re
import sys

LoadModules = ["mod", "public", "util"]
# List of modules to load; All Command-providing modules should be included, except core

for module in LoadModules:
    # Import everything in the list above
    importlib.import_module("." + module, package=__name__)

__all__ = ["CommandRouter"]

"""
A suggestion from a friend:

import functools
import importlib

@functools.lru_cache(maxsize=None)
def get_command(name, *args, **kwargs):
    mod = importlib.import(name)
    return mod.CommandModule(*args, **kwargs)


_commands = dict()
def get_command(name, *args, **kwargs):
    if name in _commands:
        return _commands[name]

    mod = importlib.import(name)
    c = mod.CommandModule(*args, **kwargs)
    _commands[name] = c
    return c
"""


class CommandRouter:
    def __init__(self, client, *a, **kw):
        self.client = client
        self.config = client.config
        self.commands = []

        for MODULE in LoadModules:
            # Get the module
            mod = sys.modules.get(__name__ + "." + MODULE, None)
            if mod:
                # Instantiate its command engine
                cmod = mod.CommandModule(client, *a, **kw)
                self.commands.append(cmod)
                setattr(self, MODULE, cmod)

    def find_command(self, kword):
        """
        Find and return a class method whose name matches kword
        """
        for mod in self.commands:
            func = mod.get_command(kword)
            if not func:
                continue
            else:
                return mod, func
        return None, None

    def parse(self, command):
        pattern = r"(?<!-)(-\w(?=[^\w])|--\w{2,})( [^\s-]+)?"
        # This regex works beautifully and I hate it deeply
        flags = {}

        # Get a list of strings where the --flags are separated out
        exp = list(
            [s.strip() if type(s) == str else s for s in re.split(pattern, command)]
        )
        # My IDE marks a bunch of fake errors if I dont re-encapsulate this; Ignore it

        # Clean out the list
        while "" in exp:
            # Of empties...
            exp.remove("")
        while None in exp:
            # ...and Nones
            exp.remove(None)

        # Make two iterables, one for the "current" position and one for the "next"
        base, ahead = itertools.tee(iter(exp))
        next(ahead)

        for i in range(len(exp)):
            # Get the next word
            possible_flag = next(base)
            try:
                # Get the **next** next word
                flag_arg = next(ahead)
            except StopIteration:
                # If there isnt one, then if this one is a flag, it is True
                flag_arg = True
            if exp[i] == possible_flag and str(possible_flag).startswith("-"):
                # This word is a flag; Eat it because we pass it separately
                exp[i] = None
                if str(flag_arg).startswith("-"):
                    # The next word is another flag; not an arg of this one
                    flag_arg = True
                else:
                    # The next word is an argument of this flag
                    try:
                        # Eat it so it isnt taken by anything else
                        exp[i + 1] = None
                    except IndexError:
                        # Oh it doesnt exist, nvm it doesnt matter
                        pass
                # Set the flag in the dict
                flags[str(possible_flag).lstrip("-")] = flag_arg

        # Now that all that is done, clean out the list again
        while None in exp:
            exp.remove(None)

        # Return a final string of all non-flags with a dict of flags
        return " ".join(exp), flags

    def route(self, command: str, src=None):
        """
        Route a command (and the source message) to the correct method of the correct module.
        By this point, the prefix should have been stripped away already, leaving a plaintext command.
        """
        # 'ban badperson666 evilness'
        # Separate the first word from the rest
        command_word, command_components = command.split(" ", 1)
        # 'ban'; 'badperson666 evilness'

        # Find the method
        engine, func = self.find_command(command_word)
        if not func:
            return "Command '{}' not found.".format(command_word)
        elif not engine.authenticate(src):
            return "Authentication failure."
        else:
            # Parse it
            text, flags = self.parse(command_components)
            # And execute it
            return func(text, **flags, src=src)

    def run(self, string=None, src=None):
        """
        Given a message, determine whether it is a command;
        If it is, route it accordingly
        """
        if not string:
            # If a string is not provided, a source message MUST be;
            # Extract a new string from it
            if not src:
                # But if no source message is provided, fail
                raise ValueError(
                    "CommandRouter.run() must take a string and/or a source Discord message"
                )
            else:
                string = src.content

        prefix = self.config.prefix
        if string.startswith(prefix):
            # Message begins with the invocation prefix
            command = string[len(prefix) :]
            return self.route(command, src)
            # Remove the prefix and route the command


"""
"""
