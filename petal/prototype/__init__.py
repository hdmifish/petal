import importlib
import sys

LoadModules = ["mod", "public", "util"]
# List of modules to load; All Command-providing modules should be included, except core

for module in LoadModules:
    # Import everything in the list above
    importlib.import_module(module)

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
            # TODO: Strip down "MODULE" to a single word to prevent any sort of injection
            # Get the module
            mod = sys.modules.get(MODULE, None)
            if mod:
                # Instantiate its command engine
                cmod = mod.CommandModule(client, *a, **kw)
                self.commands.append(cmod)
                setattr(self, MODULE, cmod)

    def find_command(self, kword):
        """
        Find and return a class method whose name matches kword
        """
        func = None
        for mod in self.commands:
            func = mod.get_command(kword)
            if not func:
                continue
            else:
                break
        return func

    def route(self, command: str, src=None):
        """
        Route a command (and the source message) to the correct method of the correct module.
        By this point, the prefix should have been stripped away already, leaving a plaintext command.
        """
        # 'ban badperson666 evilness'
        command_components = command.split(
            " ", 1
        )  # Separate the first word from the rest
        # ['ban', 'badperson666 evilness']
        command_word = command_components.pop(0)
        # 'ban'; ['badperson666 evilness']

        func = self.find_command(command_word)  # Find the method
        if not func:
            return "Command '{}' not found.".format(command_word)
        else:
            return func(command_components, src)  # Execute it

    def parse(self, string=None, src=None):
        """
        Given a message, determine whether it is a command;
        If it is, route it accordingly
        """
        if not string:
            # If a string is not provided, a source message MUST be;
            # Extract a new string from it
            if not src:
                # But if no source message is provided, fail
                raise ValueError("CommandRouter.parse() must take a string and/or a source Discord message")
            else:
                string = src.content

        prefix = self.config.prefix
        if string.startswith(prefix):
            # Message begins with the invocation prefix
            command = string[len(prefix):]
            return self.route(command, src)
            # Remove the prefix and route the command
