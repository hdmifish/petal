LoadModules = ["mod", "public", "util"]
# List of modules to load; All Command-providing modules should be included, except core

for module in LoadModules:
    # Import everything in the list above
    exec("from . import " + module)

__all__ = ["CommandRouter"]


class CommandRouter:
    def __init__(self, config, *a, **kw):
        self.commands = []
        self.config = config

        for MODULE in LoadModules:
            # TODO: Strip down "MODULE" to a single word to prevent any sort of injection
            try:
                exec(f"self.{MODULE} = {MODULE}.CommandModule(config, *a, **kw)")
                exec(f"self.commands.append(self.{MODULE})")
            except:
                pass

    def route(self, command: str, src=None):
        """
        Route a command (and the source message) to the correct method of the correct module.
        By this point, the prefix should have been stripped away already, leaving a plaintext command.
        """
        command_components = command.split(
            " ", 1
        )  # Separate the first word from the rest
        command_word = command_components.pop(0)
        func = None
        for mod in self.commands:
            func = mod.get_command(command_word)
            if not func:
                continue
            else:
                break
        if not func:
            return "Command '{}' not found.".format(command_word)
        else:
            return func(command_components, src)
