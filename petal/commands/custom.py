"""SPECIALIZED commands module for USER-DEFINED COMMANDS.
Access: Public"""

import asyncio

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
        async def cmd_custom(args, src, **_):
            if args:
                member = self.get_member(src, args[0].strip())
                tag = member.mention if member else None
            else:
                tag = None

            nsfw = cmd_dict.get("nsfw", False)
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
        short = response.replace("{", "{{").replace("}", "}}")
        if len(short) > 80:
            short = short[:77] + "..."
        cmd_custom.__doc__ = (
            "__Custom command__: Return the following text: ```{}```\n\n".format(short)
            + cmd_dict.get("desc")
            or "This is a custom command, so available help text is limited, "
            "but at the same time, the command is very simple. All it does is "
            "return a string, although the string may include formatting tags "
            "for invoker name, invoker ID, and a targeted mention."
            + "\n\nSyntax: `{p}"
            + kword.lower()
            + (" <user_ID>" if "{tag}" in response else "")
            + "`"
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
        **_
    ):
        """That awesome custom command command.

        Create a custom Petal command that will print a specific text when run. This text can be anything, from a link to a copypasta to your own poetry. Just try not to be obnoxious with it, yeah?

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
                return "New Command `{}` Created!".format(self.config.prefix + invoker)
        return saved


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsCustom
