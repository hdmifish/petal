LoadModules = ["mod", "public", "util"]
# List of modules to load; All Command-providing modules should be included, except core

for module in LoadModules:
    # Import everything in the list above
    exec("from . import " + module)

__all__ = ["CommandRouter"]


class CommandRouter:
    def __init__(self, client, *a, **kw):
        self.client = client
        self.config = client.config
        self.commands = []

        for MODULE in LoadModules:
            # TODO: Strip down "MODULE" to a single word to prevent any sort of injection
            try:
                mod = eval(MODULE).CommandModule(client, *a, **kw)
                self.commands.append(mod)
                exec(f"self.{MODULE} = mod")
            except:
                pass

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
