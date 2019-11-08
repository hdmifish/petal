"""SPECIALIZED commands module for USER-DEFINED COMMANDS.
Access: Public"""

import asyncio
from string import Template

import discord

from petal.commands import core


same_author = lambda m0: lambda m1: m0.author == m1.author and m0.channel == m1.channel


class CommandsCustom(core.Commands):
    auth_fail = "This command is public. If you are reading this, something went wrong."

    def get_command(self, kword: str):
        """Build and return a method returning the configured response to this keyword."""
        # Step Zero is to make sure that the name does not belong to a REAL command.
        zero, mod = super().get_command(kword)
        if zero:
            return zero, mod

        # Otherwise, first, ensure that the keyword does in fact exist in the custom list.
        cmd_dict = self.config.commands.get(kword, None)
        if not cmd_dict:
            return None, None
        response = cmd_dict["com"]

        # Build the function to return the response. Note that "self" exists already.
        def cmd_custom(args, src, **_):
            if args:
                member = self.get_member(src, args[0].strip())
                tag = member.mention if member else None
            else:
                tag = None

            if cmd_dict.get("nsfw", False) and src.channel.id not in self.config.get(
                "nsfwChannels"
            ):
                # Fail silently, the same as if there were no command found.
                return
            else:
                # Replace tags where needed.
                return Template(response).safe_substitute(
                    SELF=src.author.name,
                    MYID=src.author.id,
                    TAG=tag or src.author.mention,
                )

        # Specify the docstring and name so that !help will work on this.
        if len(response) > 80:
            short = response[:77] + "..."
        else:
            short = response

        cmd_custom.__doc__ = "{0}{1}\n\nSyntax: `{{p}}{2}{3}`".format(
            "__Custom command__: Return the following text: ```{}```\n\n".format(short),
            (
                cmd_dict.get("desc")
                or "This is a custom command, so available help text is "
                "limited, but at the same time, the command is very simple. "
                "All it does is return a string, although the string may "
                "include formatting tags for invoker name, invoker ID, and a "
                "targeted mention."
            ),
            kword.lower(),
            (" [<user_ID>]" if "$TAG" in response else ""),
        )
        cmd_custom.__name__ = "cmd_" + kword.lower()

        return cmd_custom, None

    async def cmd_new(
        self,
        args: list,
        src: discord.Message,
        _description: str = None,
        _image: str = None,
        _i: str = None,
        _nsfw: bool = False,
        **_,
    ):
        """That awesome custom command command.

        Create a custom Petal command that will print a specific text when run. This text can be anything, from a link to a copypasta to your own poetry. Just try not to be obnoxious with it, yeah?

        A number of Substitution Tags are available, which will be replaced when the Command is run:
            `$SELF` :: The Display Name of the User running the Command.
            `$ID` :: The Discord ID of the User running the Command.
            `$TAG` :: A Mention/Tag of the User running the Command.

        Syntax: `{p}new [OPTIONS] <name of command> "<output of command>"`

        Options: `--nsfw` :: Pass this flag to restrict the command to specific channels.
        """
        if len(args) != 2:
            return "This command needs to be given 2 arguments."

        invoker = args[0].strip()
        command = args[1].strip()

        if invoker in self.config.aliases:
            return "Cannot define this command because it would shadow an alias."

        img = ""  # Base64 data, to save in Mongo.
        url = _image or _i  # URL of image.

        if src.attachments:
            pass

        def save():
            if img:
                written = self.client.db.write_cmd_image(invoker, img)
                if written is not True:
                    return "Failed to write image into Database."
            # TODO: Validate the URL as well, and return str if bad.
            self.config.commands[invoker] = {
                "com": command,
                "db": bool(img),
                "desc": _description,
                "link": url,
                "nsfw": _nsfw,
            }
            self.config.save()
            return True

        if invoker in self.config.commands:
            await self.client.send_message(
                src.author,
                src.channel,
                "This command already exists, type `yes` to overwrite it.",
            )
            try:
                response = await self.client.wait_for(
                    "message", check=same_author(src), timeout=30
                )
            except asyncio.TimeoutError:
                return "Timed out while waiting for confirmation."

            if str(response.content).lower() != "yes":
                return "Command `" + self.config.prefix + invoker + "` was not changed."
            else:
                saved = save()
                if saved is True:
                    return (
                        "Command `" + self.config.prefix + invoker + "` was redefined."
                    )
        else:
            saved = save()
            if saved is True:
                return f"New Command `{self.config.prefix}{invoker}` Created!"
        return saved


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsCustom
