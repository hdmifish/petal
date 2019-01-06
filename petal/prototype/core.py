class Commands:
    def __init__(self, client, router, *a, **kw):
        self.client = client
        self.config = client.config
        self.router = router
        self.args = a  # Save for later
        self.kwargs = kw  # Just in case

    def get_command(self, kword):
        if "__" not in kword:
            # Refuse to fetch anything with a dunder
            return getattr(self, "cmd_" + kword, None)

    def get_all(self, *_):
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
        return True
