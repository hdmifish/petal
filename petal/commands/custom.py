"""SPECIALIZED commands module for USER-DEFINED COMMANDS.
Access: Public"""

from petal.commands import core


class CommandsCustom(core.Commands):
    auth_fail = "This command is public. If you are reading this, something went wrong."

    def get_command(self, kword: str):
        """
        Build and return a method returning the configured response to this keyword.
        """
        # Step Zero is to make sure that the name does not belong to a REAL command.
        zero = super().get_command(kword)
        if zero:
            return zero

        # Otherwise, first, ensure that the keyword does in fact exist in the custom list.
        command = self.config.commands.get(kword, None)
        if not command:
            return None
        response = command["com"]

        # Build the function to return the response. Note that "self" exists already.
        async def cmd_custom(args, src, **_):
            if args:
                member = self.get_member(src, args[0].strip())
                tag = member.mention if member else None
            else:
                tag = None

            nsfw = command.get("nsfw", False)
            if nsfw and src.channel.id not in self.config.get("nsfwChannels"):
                return None

            # Replace tags where needed.
            try:
                output = response.format(
                    self=src.author.name,
                    myID=src.author.id,
                    tag=tag or src.author.mention,
                )
            except KeyError:
                return None
            else:
                return output

        # Specify the docstring and name so that !help will work on this.
        cmd_custom.__doc__ = (
            "__Custom command__: Return a static string.\n\n".format(response)
            # "__Custom command__: Return the following text: ```{}```\n\n".format(response.replace("{", "\{").replace("}", "\}"))  # TODO: Find a way to make a literal {tag} that resists format()
            + command.get(
                "desc",
                "This is a custom command, so available help text is limited, but at the same time, the command is very simple. All it does is return a string, although the string may include formatting tags for invoker name, invoker ID, and a targeted mention.",
            )
            + "\n\nSyntax: `{p}"
            + kword.lower()
            + (" <user_ID>" if "{tag}" in response else "")
            + "`"
        )
        cmd_custom.__name__ = "cmd_" + kword.lower()

        return cmd_custom

    def authenticate(self, *_):
        return True

    async def cmd_new(self, args, src, nsfw=False, **_):
        """
        That awesome custom command command.

        Create a custom Petal command that will print a specific text when run. This text can be anything, from a link to a copypasta to your own poetry. Just try not to be obnoxious with it, yeah?

        Syntax: `{p}new [OPTIONS] <name of command> "<output of command>"`

        Options: `--nsfw` :: Pass this flag to restrict the command to specific channels.
        """
        if len(args) != 2:
            return "This command needs to be given 2 arguments."
        if nsfw not in (True, False):
            return "`--nsfw` flag cannot be supplied with a value."

        invoker = args[0].strip()
        command = args[1].strip()

        if invoker in self.config.commands:
            await self.client.send_message(
                src.author,
                src.channel,
                "This command already exists, type `yes` to overwrite it.",
            )
            response = await self.client.wait_for_message(
                timeout=15, author=src.author, channel=src.channel
            )

            if str(response.content).lower() != "yes":
                return "Command `" + self.config.prefix + invoker + "` was not changed."
            else:
                self.config.commands[invoker] = {"com": command, "nsfw": nsfw}
                self.config.save()
                return "Command `" + self.config.prefix + invoker + "` was redefined."
        else:
            self.config.commands[invoker] = {"com": command, "nsfw": nsfw}
            self.config.save()
            return "New Command `{}` Created!".format(self.config.prefix + invoker)


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsCustom
