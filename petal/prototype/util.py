from . import core

import discord


class CommandsUtil(core.Commands):
    def authenticate(self, *_):
        return True

    async def cmd_help(self, string, src, **_):
        """
        Print information regarding command usage.

        Help text is drawn from the docstring of a command method, which should be formatted into three sections -- Summary, Details, and Syntax -- which are separated by double-newlines.
        The Summary section provides cursory information about a command, and is typically all one needs to understand it.
        The Details section contains more involved information about how the command works, possibly including technical information.
        The Syntax section describes exactly how the command is invoked.

        Syntax: `{p}help [<command>]`
        """

        mod, cmd = self.router.find_command(string)
        if not cmd:
            # TODO: Iso, put your defualt helptext here; Didnt copy it over in case you wanted it changed
            pass
        elif cmd.__doc__:
            # Grab the docstring and insert the correct prefix wherever needed
            doc0 = cmd.__doc__.format(p=self.config.prefix)
            # Split the docstring up by double-newlines
            doc = [doc1.strip() for doc1 in doc0.split("\n\n")]

            summary = doc.pop(0)
            em = discord.Embed(title=cmd.__name__[4:], description=summary, colour=0x0ACDFF)

            details = ""
            syntax = ""
            while doc:
                line = doc.pop(0)
                if line.lower().startswith("syntax"):
                    syntax = line.split(" ", 1)[1]
                else:
                    details += line + "\n"
            if details:
                em.add_field(name="Details", value=details.strip())
            if syntax:
                em.add_field(name="Syntax", value=syntax)

            em.set_author(name="Petal Help", icon_url=self.client.user.avatar_url)
            em.set_thumbnail(url=self.client.user.avatar_url)
            await self.client.embed(src.channel, em)
        else:
            return "No help for `{}` available".format(cmd.__name__)

# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsUtil
