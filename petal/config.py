from typing import Union

from ruamel import yaml

from .exceptions import ConfigError
from .grasslands import Peacock

log = Peacock()


class Config(object):
    def __init__(self):
        try:
            with open("config.yml", "r") as fp:
                self.doc = yaml.load(fp, Loader=yaml.RoundTripLoader)
        except IOError as e:
            log.err("Could not open config.yml: " + str(e))
            exit()
        except Exception as e:
            # log.err(
            #     "An unexpected exception of type: "
            #     + type(e).__name__
            #     + " has occurred:\n"
            #     + str(e)
            # )
            # exit()
            # Meh, if youre exiting anyway why not just raise it?
            raise e
        else:
            if "token" in self.doc:
                self.token = self.doc["token"]
                self.useToken = not self.doc["selfbot"]
            else:
                log.err("Token missing in config.yml")
                exit(404)
        # Defining constants below
        try:
            self.prefix = self.doc["prefix"]
            log.f("config", "Using prefix: " + self.prefix)
            self.owner = self.doc["owner"]
            log.f("config", "Loaded ownerID")
            self.pm = self.doc["acceptPMs"]
            log.f("config", "AcceptPMs: " + str(self.pm))
            self.l1 = self.doc["level"]["l1"]
            self.l2 = self.doc["level"]["l2"]
            self.l3 = self.doc["level"]["l3"]
            self.l4 = self.doc["level"]["l4"]
            log.f("config", "Loaded Local Permissions")
            self.aliases = self.doc["aliases"]
            log.f("config", "Loaded Aliases")
            self.permitNSFW = self.doc["permitNSFW"]
            log.f("config", "Permiting NSFW Images: " + str(self.permitNSFW))
            self.blacklist = self.doc["blacklist"]
            log.f("config", "Loaded blacklist")
            self.commands = self.doc["commands"]
            log.f("config", "Loaded commands")
            self.useLog = "logChannel" in self.doc

            if self.useLog:
                log.ready("Using Action Log Features")
                self.logChannel = self.get("logChannel")
                self.modChannel = self.get("modChannel")
            self.wordFilter = self.get("wordFilter")
            log.f("config", "Loaded word filter")
            self.tc = self.get("trackChannel")
            if self.tc is None:
                log.warn(
                    "trackChannel object not found in config.yml. "
                    + "That functionality is disabled"
                )

            # self.lockLog = False  //deprecated
            # self.imageIndex = self.doc["imageIndex"]
            self.hugDonors = self.doc["hugDonors"]
            log.f("config", "Loaded hug donors")
            self.stats = self.doc["stats"]
            log.f("config", "Loaded stats")
        except KeyError as e:
            log.err("Missing config item: " + str(e))
            exit(404)
        return

    # def flip(self):
    #    self.lockLog = not self.lockLog

    def get(self, field, default=None, err: Union[BaseException, bool] = None):
        """Retrieve a Configuration Value.

        Splits the given "field" apart into a kind of Path by slashes ("/"), and
            walks the Config file, following the Path. If the Path cannot be
            complete, the Default is returned instead.

        If the "err" Parameter is passed, an Exception will be raised instead of
            returning the Default.
        """
        here = self.doc

        for step in field.split("/"):
            if step in here:
                here = here[step]
            else:
                log.err(f"'{field}' is not found in config.")

                if err is True:
                    raise ConfigError(field)
                elif err and isinstance(err, BaseException):
                    raise err
                else:
                    return default

        return here

    def __getitem__(self, key: Union[slice, str, tuple]):
        """Retrieve a Configuration Value by way of Object Indexing.

        Allows a more succinct, if somewhat more opaque, way of writing Config
            queries.
        """
        if isinstance(key, slice):
            # config["field" : "default" : "err"]
            return self.get(str(key.start), key.stop, key.step)

        elif isinstance(key, tuple):
            # config["field", "default", "err"]
            return self.get(*key[:3])

        else:
            # config["field"]
            return self.get(key)

    def save(self, vb=False):
        if vb:
            log.info("Saving...")
        try:
            with open("config.yml", "w") as fp:
                yaml.dump(self.doc, fp, Dumper=yaml.RoundTripDumper)
        except PermissionError:
            log.err("No write access to config.yml")
        except IOError as e:
            log.err("Could not open config.yml: " + str(e))
        except Exception as e:
            log.err(
                "An unexpected exception of type: "
                + type(e).__name__
                + " has occurred:\n"
                + str(e)
            )
        else:
            if vb:
                log.info("Save complete")
        return

    def load(self, vb=False):
        try:
            with open("config.yml", "r") as fp:
                self.doc = yaml.load(fp, Loader=yaml.RoundTripLoader)
        except IOError as e:
            log.err("Could not open config.yml: " + str(e))
        except Exception as e:
            log.err(
                "An unexpected exception of type: "
                + type(e).__name__
                + " has occurred:\n"
                + str(e)
            )
        else:
            return self


cfg: Config = Config()
