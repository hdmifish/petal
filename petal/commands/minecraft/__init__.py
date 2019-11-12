"""Commands module for MINECRAFT-RELATED UTILITIES.
Access: Server Operators"""

import importlib
import sys

from petal.commands import core
from petal.util.minecraft import Minecraft


LoadModules = [
    "mc_admin",
    "mc_mod",
    "mc_public",
]

for module in LoadModules:
    # Import everything in the list above.
    importlib.import_module("." + module, package=__name__)


class CommandsMinecraft(core.Commands):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.minecraft: Minecraft = Minecraft(self.client)
        self.engines = []

        # Load all command engines.
        for MODULE in LoadModules:
            # Get the module.
            self.log.info("Loading {} commands...".format(MODULE.title()))
            mod = sys.modules.get(__name__ + "." + MODULE, None)

            if mod:
                # Instantiate its command engine.
                cmod = mod.CommandModule(*a, **kw)
                self.engines.append(cmod)
                setattr(self, MODULE, cmod)
                self.log.ready("{} commands loaded.".format(MODULE.title()))

            else:
                self.log.warn("FAILED to load {} commands.".format(MODULE.title()))

    def get_command(self, kword: str):
        for mod in self.engines:
            func, submod = mod.get_command(kword)
            if not func:
                continue
            else:
                return func, (submod or mod)
        return None, None

    def get_all(self) -> list:
        full = []
        for mod in self.engines:
            full += mod.get_all()
        return full


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMinecraft
