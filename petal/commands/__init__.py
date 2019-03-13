from datetime import datetime as dt
import importlib
import shlex
import sys

import facebook
import praw
import pytumblr
import twitter

from petal.grasslands import Giraffe, Octopus, Peacock


# List of modules to load; All Command-providing modules should be included (NOT "core").
# Order of this list is the order in which commands will be searched. First occurrence
#     the user is permitted to access will be run.
LoadModules = [
    "dev",
    "admin",
    "mod",
    "listener",
    "social",
    "event",
    "minecraft",
    "util",
    "public",
    "custom",
]

for module in LoadModules:
    # Import everything in the list above.
    importlib.import_module("." + module, package=__name__)


class CommandRouter:
    version = ""

    def __init__(self, client, *a, **kw):
        self.client = client
        self.config = client.config
        self.engines = []

        self.log = Peacock()
        self.log.info("Loading Command modules...")
        self.startup = dt.utcnow()

        # Load all command engines.
        for MODULE in LoadModules:
            # Get the module.
            self.log.info("Loading {} commands...".format(MODULE.capitalize()))
            mod = sys.modules.get(__name__ + "." + MODULE, None)
            if mod:
                # Instantiate its command engine.
                cmod = mod.CommandModule(client, self, *a, **kw)
                self.engines.append(cmod)
                setattr(self, MODULE, cmod)
                self.log.ready("{} commands loaded.".format(MODULE.capitalize()))
            else:
                self.log.warn("FAILED to load {} commands.".format(MODULE.capitalize()))

        # Execute legacy initialization.
        # TODO: Move this elsewhere

        key_osu = self.config.get("osu")
        if key_osu:
            self.osu = Octopus(key_osu)
        else:
            self.osu = None
            self.log.warn("No OSU! key found.")

        key_imgur = self.config.get("imgur")
        if key_imgur:
            self.imgur = Giraffe(key_imgur)
        else:
            self.imgur = None
            self.log.warn("No imgur key found.")

        reddit = self.config.get("reddit")
        if reddit:
            self.reddit = praw.Reddit(
                client_id=reddit["clientID"],
                client_secret=reddit["clientSecret"],
                user_agent=reddit["userAgent"],
                username=reddit["username"],
                password=reddit["password"],
            )
            if self.reddit.read_only:
                self.log.warn(
                    "This account is in read only mode. "
                    + "You may have done something wrong. "
                    + "This will disable reddit functionality."
                )
                self.reddit = None
                return
            else:
                self.log.ready("Reddit support enabled!")
        else:
            self.reddit = None
            self.log.warn("No Reddit keys found")

        tweet = self.config.get("twitter")
        if tweet:
            self.twit = twitter.Api(
                consumer_key=tweet["consumerKey"],
                consumer_secret=tweet["consumerSecret"],
                access_token_key=tweet["accessToken"],
                access_token_secret=tweet["accessTokenSecret"],
                tweet_mode="extended",
            )
            if "id" not in str(self.twit.VerifyCredentials()):
                self.log.warn(
                    "Your Twitter authentication is invalid, "
                    + " Twitter posting will not work"
                )
                self.twit = None
                return
        else:
            self.twit = None
            self.log.warn("No Twitter keys found.")

        fb = self.config.get("facebook")
        if fb:
            self.fb = facebook.GraphAPI(
                access_token=fb["graphAPIAccessToken"], version=fb["version"]
            )
        else:
            self.fb = None
            self.log.warn("No Facebook keys found.")

        tumblr = self.config.get("tumblr")
        if tumblr:
            self.tumblr = pytumblr.TumblrRestClient(
                tumblr["consumerKey"],
                tumblr["consumerSecret"],
                tumblr["oauthToken"],
                tumblr["oauthTokenSecret"],
            )
            self.log.ready("Tumblr support Enabled!")
        else:
            self.tumblr = None
            self.log.warn("No Tumblr keys found.")

        self.log.ready("Command Module Loaded!")

    def find_command(self, kword, src=None):
        """
        Find and return a class method whose name matches kword.
        """
        denied = ""
        for mod in self.engines:
            func = mod.get_command(kword)
            if not func:
                continue
            else:
                if not src or mod.authenticate(src):
                    return mod, func, False
                else:
                    denied = mod.auth_fail
        return None, None, denied

    def get_all(self):
        full = []
        for mod in self.engines:
            full += mod.get_all()
        return full

    def parse(self, cline: list) -> (list, dict):
        """$cline is a list of strings. Figure out which strings, if any, are
            meant to be options/flags. If an option has a related value, add it
            to the options dict with the value as its value. Otherwise, do the
            same but with True instead. Return what args remain with the options
            dict.
        """
        args = cline.copy()
        opts = {}

        # Loop through given arguments
        for i, arg in enumerate(args):
            # Find args that begin with a dash
            if arg.startswith("-"):
                # This arg is an option key
                key = arg.lstrip("-")
                args[i] = None

                if key in ("self", "args", "src"):
                    # Do not allow flags that mimic important values.
                    continue

                if "=" in key:
                    # A specific value was given.
                    key, val = key.split("=", 1)
                else:
                    # Unspecified value defaults to generic True.
                    val = True

                if arg.startswith("--"):
                    # This arg is a long opt; The whole word is one key.
                    opts[key] = val
                else:
                    # This is a short opt cluster; Each letter is a key.
                    for char in key:
                        opts[char] = True
                    opts[key[-1]] = val

        # Remove all placeholders now that position no longer matters.
        while None in args:
            args.remove(None)

        return args, opts

    async def route(self, command: str, src=None):
        """Route a command (and the source message) to the correct method of the
            correct module. By this point, the prefix should have been stripped
            away already, leaving a plaintext command.
        """
        # Split the full command line into a list of tokens, each its own arg.
        cline = list(shlex.shlex(command, posix=True, punctuation_chars=True))
        cword = cline.pop(0)

        # Find the method, if one exists.
        engine, func, denied = self.find_command(cword, src)
        if denied:
            return "Authentication failure: " + denied
        elif not func:
            return
        else:
            # Extract option flags from the argument list.
            args, opts = self.parse(cline)
            # Execute the method, passing the arguments as a list and the options
            #     as keyword arguments.
            return await func(args=args, **opts, src=src)

    async def run(self, src):
        """Given a message, determine whether it is a command;
        If it is, route it accordingly.
        """
        if src.author == self.client.user:
            return
        prefix = self.config.prefix
        if src.content.startswith(prefix):
            # Message begins with the invocation prefix
            command = src.content[len(prefix) :]
            return await self.route(command, src)
            # Remove the prefix and route the command

    @property
    def uptime(self):
        delta = dt.utcnow() - self.startup
        delta = delta.total_seconds()

        d = divmod(delta, 86400)  # days
        h = divmod(d[1], 3600)  # hours
        m = divmod(h[1], 60)  # minutes
        s = m[1]  # seconds

        return "%d days, %d hours, %d minutes, %d seconds" % (d[0], h[0], m[0], s)
