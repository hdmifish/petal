import discord

from petal.dbhandler import m2id


class Commands:
    auth_fail = "This command is implemented incorrectly."

    def __init__(self, client, router, *a, **kw):
        self.client = client
        self.config = client.config
        self.db = client.db

        self.router = router
        self.log = self.router.log

        self.args = a  # Save for later
        self.kwargs = kw  # Just in case

    def get_command(self, kword: str):
        if "__" not in kword:
            # Refuse to fetch anything with a dunder
            return getattr(self, "cmd_" + kword, None)

    def get_all(self) -> list:
        full = [
            getattr(self, attr)
            for attr in dir(self)
            if "__" not in attr and attr.startswith("cmd_")
        ]
        return full

    def authenticate(self, *_):
        """
        Take a Discord message and return True if:
          1. The author of the message is allowed to access this package
          2. This command can be run in this channel
        Should be overwritten by modules providing secure functions
        (For example, moderation tools)
        """
        return False

    # # # UTILS IMPORTED FROM LEGACY COMMANDS # # #

    def check_user_has_role(self, user, role):
        target = discord.utils.get(user.server.roles, name=role)
        if target is None:
            self.log.err("Role '" + role + "' does not exist.")
            return False
        else:
            if target in user.roles:
                return True
            else:
                return False

    def get_member(self, message, member):
        if isinstance(message, discord.Server):
            return message.get_member(m2id(member))
        else:
            return discord.utils.get(
                message.server.members, id=member.lstrip("<@!").rstrip(">")
            )
