class Commands:
    def __init__(self, client, *a, **kw):
        self.client = client
        self.config = client.config
        self.args = a  # Save for later
        self.kwargs = kw  # Just in case

    def get_command(self, kword):
        try:
            x = eval(f"self.{kword}")
        except:
            x = None
        if not "method" in str(type(x)) or x == Commands.get_command:
            x = None
        return x
