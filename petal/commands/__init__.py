import importlib
import itertools
import re
import shlex
import sys

import facebook
import praw
import pytumblr
import twitter

from petal.grasslands import Giraffe, Octopus, Peacock


# List of modules to load; All Command-providing modules should be included (NOT "core").
# Order of this list is the order in which commands will be searched. First occurrence runs.
LoadModules = ["admin", "dev", "mod", "listener", "minecraft", "public", "util"]

for module in LoadModules:
    # Import everything in the list above
    importlib.import_module("." + module, package=__name__)

__all__ = ["CommandRouter"]


class CommandRouter:
    def __init__(self, client, *a, **kw):
        self.client = client
        self.config = client.config
        self.engines = []

        self.log = Peacock()
        self.log.info("Loading Command modules...")

        # Load all command engines
        for MODULE in LoadModules:
            # Get the module
            self.log.info("Loading {}...".format(MODULE))
            mod = sys.modules.get(__name__ + "." + MODULE, None)
            if mod:
                # Instantiate its command engine
                cmod = mod.CommandModule(client, self, *a, **kw)
                self.engines.append(cmod)
                setattr(self, MODULE, cmod)
                self.log.info("{} commands loaded.".format(MODULE))
            else:
                self.log.warn("FAILED to load {} commands.".format(MODULE))

        # Execute legacy initialization
        # TODO: Move this elsewhere

        self.osuKey = self.config.get("osu")
        if self.osuKey is not None:
            self.o = Octopus(self.osuKey)

        else:
            self.log.warn("No OSU! key found.")

        self.imgurKey = self.config.get("imgur")
        if self.imgurKey is not None:
            self.i = Giraffe(self.imgurKey)
        else:
            self.log.warn("No imgur key found.")
        if self.config.get("reddit") is not None:
            reddit = self.config.get("reddit")
            self.r = praw.Reddit(
                client_id=reddit["clientID"],
                client_secret=reddit["clientSecret"],
                user_agent=reddit["userAgent"],
                username=reddit["username"],
                password=reddit["password"],
            )
            if self.r.read_only:
                self.log.warn(
                    "This account is in read only mode. "
                    + "You may have done something wrong. "
                    + "This will disable reddit functionality."
                )
                self.r = None
                return
            else:
                self.log.ready("Reddit support enabled!")
        else:
            self.log.warn("No Reddit keys found")

        if self.config.get("twitter") is not None:
            tweet = self.config.get("twitter")
            self.t = twitter.Api(
                consumer_key=tweet["consumerKey"],
                consumer_secret=tweet["consumerSecret"],
                access_token_key=tweet["accessToken"],
                access_token_secret=tweet["accessTokenSecret"],
                tweet_mode="extended",
            )
            # tweet te
            if "id" not in str(self.t.VerifyCredentials()):
                self.log.warn(
                    "Your Twitter authentication is invalid, "
                    + " Twitter posting will not work"
                )
                self.t = None
                return
        else:
            self.log.warn("No Twitter keys found.")

        if self.config.get("facebook") is not None:
            fb = self.config.get("facebook")
            self.fb = facebook.GraphAPI(
                access_token=fb["graphAPIAccessToken"], version=fb["version"]
            )

        if self.config.get("tumblr") is not None:
            tumble = self.config.get("tumblr")
            self.tb = pytumblr.TumblrRestClient(
                tumble["consumerKey"],
                tumble["consumerSecret"],
                tumble["oauthToken"],
                tumble["oauthTokenSecret"],
            )
            self.log.ready("Tumblr support Enabled!")
        else:
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

    def parse(self, command):
        # TODO: Note to self: Remake this with getopt instead. Idiot.
        pattern = r"(?<!-)(-\w(?=[^\w])|--\w{2,})( [^\s-]+)?"
        # This regex works beautifully and I hate it deeply
        flags = {}

        # Get a list of strings where the --flags are separated out
        exp = list(
            [s.strip() if type(s) == str else s for s in re.split(pattern, command)]
        )
        # My IDE marks a bunch of fake errors if I dont re-encapsulate this; Ignore it

        # Clean out the list
        while "" in exp:
            # Of empties...
            exp.remove("")
        while None in exp:
            # ...and Nones
            exp.remove(None)

        # Make two iterables, one for the "current" position and one for the "next"
        base, ahead = itertools.tee(iter(exp))
        next(ahead)

        for i in range(len(exp)):
            # Get the next word
            possible_flag = next(base)
            try:
                # Get the **next** next word
                flag_arg = next(ahead)
            except StopIteration:
                # If there isnt one, then if this one is a flag, it is True
                flag_arg = True
            if exp[i] == possible_flag and str(possible_flag).startswith("-"):
                # This word is a flag; Eat it because we pass it separately
                exp[i] = None
                if str(flag_arg).startswith("-"):
                    # The next word is another flag; not an arg of this one
                    flag_arg = True
                else:
                    # The next word is an argument of this flag
                    try:
                        # Eat it so it isnt taken by anything else
                        exp[i + 1] = None
                    except IndexError:
                        # Oh it doesnt exist, nvm it doesnt matter
                        pass
                # Set the flag in the dict
                flags[str(possible_flag).lstrip("-")] = flag_arg

        # Now that all that is done, clean out the list again
        while None in exp:
            exp.remove(None)

        # Return a final string of all non-flags with a dict of flags
        return " ".join(exp), flags

    def parse2(self, cline: list) -> (list, dict):
        """Replacement of parse() above.
        $cline is a list of strings. Figure out which strings, if any, are meant
            to be options/flags. If an option has a related value, add it to the
            options dict with the value as its value. Otherwise, do the same but
            with True instead. Return what args remain with the options dict.
        """
        args = cline.copy()
        opts = {}

        # Loop through given arguments
        for i, arg in enumerate(args):
            # Find args that begin with a dash
            if arg.startswith("-"):
                # This arg is an option key
                key = arg.lstrip("-")

                if "=" in key:
                    # A specific value was given
                    key, val = key.split("=", 1)
                else:
                    # Unspecified value defaults to generic True
                    val = True

                if arg.startswith("--"):
                    # This arg is a long opt; The whole word is one key
                    opts[key] = val
                else:
                    # This is a short opt cluster; Each letter is a key
                    for char in key:
                        opts[char] = True
                    opts[key[-1]] = val

                # Replace processed options with a placeholder
                args[i] = None

        # Remove all placeholders now that position no longer matters
        while None in args:
            args.remove(None)

        return args, opts

    async def route(self, command: str, src=None):
        """
        Route a command (and the source message) to the correct method of the correct module.
        By this point, the prefix should have been stripped away already, leaving a plaintext command.
        """
        # Split the full command line into a list of tokens; Each is its own arg
        cline = list(shlex.shlex(command, posix=True, punctuation_chars=True))
        # Extract the first word, the command itself
        cword = cline.pop(0)

        # Find the method
        engine, func, denied = self.find_command(cword, src)
        if denied:
            return "Authentication failure: " + denied
        elif not func:
            # return "Command '{}' not found.".format(cword)
            return
        else:
            # Parse it
            args, opts = self.parse2(cline)
            # And execute it
            return await func(args=args, **opts, src=src)

    async def run(self, src):
        """
        Given a message, determine whether it is a command;
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
