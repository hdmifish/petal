"""Command module for SUDO COMMAND
Access: Config Whitelist
ALLOWS ACCESS TO ANY OTHER COMMAND
***VERY VERY VERY VERY DANGEROUS***
"""

from petal.commands import core


class CommandSudo(core.Commands):
    auth_fail = "`{user} is not in the sudoers file.  This incident will be reported.`"
    whitelist = "sudoers"

    async def cmd_sudo(self, args: list, msg: str, src, **etc):
        """Execute a single command as the superuser."""
        if not args:
            return "`usage: sudo [command]`"
        kword = args.pop(0)
        msg = msg.split(maxsplit=1)[-1]
        engine, func, denied = self.router.find_command(kword)

        if denied:
            return "Authentication failure: " + denied
        elif not func:
            return "`sudo: {}: command not found`".format(kword)
        else:
            return await func(args=args, **etc, msg=msg, src=src)


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandSudo
