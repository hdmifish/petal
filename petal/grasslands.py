"""
Grasslands is a semi-public module for colored logging and misc APIs
"""

from datetime import datetime as dt
from random import randint
import requests

from colorama import init, Fore
from wiktionaryparser import WiktionaryParser as WP


version = "0.0.0"

Wikt = WP()
def_cache = {}


class Peacock(object):
    def __init__(self, painter=None):
        init()

    def timestamp(self):
        return "[{}]".format(str(dt.utcnow())[:-7])

    def log(self, message):
        print(
            Fore.WHITE
            + "[LOG] "
            + self.timestamp()
            + " "
            + message.encode("ascii", "ignore").decode("ascii")
            + Fore.RESET,
            flush=True,
        )
        return

    def warn(self, message):
        print(
            Fore.YELLOW
            + "[WARN] "
            + self.timestamp()
            + " "
            + message.encode("ascii", "ignore").decode("ascii")
            + Fore.RESET,
            flush=True,
        )
        return

    def err(self, message):
        print(
            Fore.RED
            + "[ERROR] "
            + self.timestamp()
            + " "
            + message.encode("ascii", "ignore").decode("ascii")
            + Fore.RESET,
            flush=True,
        )

    def info(self, message):
        print(
            Fore.CYAN
            + "[INFO] "
            + self.timestamp()
            + " "
            + message.encode("ascii", "ignore").decode("ascii")
            + Fore.RESET,
            flush=True,
        )

    def com(self, message):
        print(
            Fore.BLUE
            + "[COMMAND] "
            + self.timestamp()
            + " "
            + message.encode("ascii", "ignore").decode("ascii")
            + Fore.RESET,
            flush=True,
        )

    def member(self, message):
        print(
            Fore.CYAN
            + "[MEMBER] "
            + self.timestamp()
            + " "
            + message.encode("ascii", "ignore").decode("ascii")
            + Fore.RESET,
            flush=True,
        )

    def debug(self, message):
        print(
            Fore.MAGENTA
            + "[DEBUG] "
            + self.timestamp()
            + " "
            + message.encode("ascii", "ignore").decode("ascii")
            + Fore.RESET,
            flush=True,
        )

    def ready(self, message):
        print(
            Fore.GREEN
            + "[READY] "
            + self.timestamp()
            + " "
            + message.encode("ascii", "ignore").decode("ascii")
            + Fore.RESET,
            flush=True,
        )

    def f(self, func="basic", message=""):
        print(
            Fore.MAGENTA
            + "[FUNC/{}] ".format(func.upper())
            + self.timestamp()
            + " "
            + message.encode("ascii", "ignore").decode("ascii")
            + Fore.RESET,
            flush=True,
        )


class Octopus(object):
    class Tentacle_user:
        def __init__(self, response):
            try:
                self.id = response["user_id"]
                self.name = response["username"]
                self.count300 = response["count300"]
                self.count100 = response["count100"]
                self.count50 = response["count50"]
                self.playcount = response["playcount"]
                self.ranked_score = response["ranked_score"]
                self.total_score = response["total_score"]
                self.rank = response["pp_rank"]
                self.level = response["level"]
                self.pp_raw = response["pp_raw"]
                self.accuracy = response["accuracy"]
                self.rank_ss = response["count_rank_ss"]
                self.rank_s = response["count_rank_s"]
                self.rank_a = response["count_rank_a"]
                self.country = response["country"]
                self.country_rank = response["pp_country_rank"]
            except KeyError as e:
                Peacock().err("Missing Key: " + str(e))
                return None

    class Tentacle_beatmap:
        def __init__(self, response):
            return

    def __init__(self, API_KEY, log=Peacock()):
        self.log = log
        if API_KEY is None:
            self.log.err(
                "No API KEY Provided. Syntax is Octopus(API_KEY," + " Logger object)"
            )
            return None
        self.key = API_KEY
        response = requests.get(
            "https://osu.ppy.sh/api/get_beatmaps?k={}" + "&limit={}".format(self.key, 1)
        )
        if "error" in response:
            self.log.err("OSU Error: " + response["error"])
            return None
        else:
            self.log.ready("OSU support enabled")

    def get_user(self, userid, mode=0):
        response = requests.get(
            "https://osu.ppy.sh/api/get_user?k="
            + "{}&m={}&u={}".format(self.key, mode, userid.strip())
        )
        if response.json() == []:
            return None
        user = self.Tentacle_user(response.json()[0])
        return user

    def get_beatmap(self, beatid, sets="", mode=0):
        response = requests.get(
            "https://osu.ppy.sh/api/get_beatmaps?k="
            + "{}&s={}&b={}&m={}".format(self.key, sets, beatid, mode)
        )
        return response


class Giraffe(object):
    def __init__(self, API_KEY, log=Peacock()):
        self.log = log
        if API_KEY is None:
            self.log.err(
                "No API KEY Provided. "
                + "Syntax is Giraffe(API_KEY, Logger object)\n "
                + "The API KEY is the same as your Client ID from"
                + " imgur"
            )

            return None
        else:
            self.log.ready("imgur support enabled")
        self.key = API_KEY

    def get_image(self, imageID):
        headers = {"Authorization": "Client-Id {}".format(self.key)}
        req = requests.get(
            "https://api.imgur.com/3/image/{}".format(imageID), headers=headers
        )
        response = req.json()

        if not response["success"]:
            return None

        return self.Imgur_Image(response["data"])

    def get_random(self, albumID):
        headers = {"Authorization": "Client-Id {}".format(self.key)}
        req = requests.get(
            "https://api.imgur.com/3/album/{}".format(albumID), headers=headers
        )
        response = req.json()
        print(response)
        if not response["success"]:
            return None

        return self.Imgur_Image(response["data"][randint(0, len(response["data"]) - 1)])

    def get_subreddit(self, subID):

        headers = {"Authorization": "Client-Id {}".format(self.key)}
        req = requests.get(
            "https://api.imgur.com/3/gallery/r/{}".format(subID), headers=headers
        )
        response = req.json()

        if not response["success"]:
            return None
        if len(response["data"]) == 0:
            return None

        return self.Imgur_Image(response["data"][randint(0, len(response["data"]) - 1)])

    class Imgur_Image:
        def __init__(self, data):
            self.id = data["id"]
            self.title = data["title"]
            self.description = data["description"]
            self.datetime = dt.fromtimestamp(data["datetime"])
            self.nsfw = data["nsfw"]
            self.link = data["link"]


class Pidgeon:
    def __init__(self, query):
        self.query = query
        api_url = "https://en.wikipedia.org/w/api.php?action=query&titles={q}&format=json&prop=extracts&exintro&explaintext"
        url = api_url.format(q=query)
        headers = {
            "User-Agent": "Petalbot/"
            + version
            + " (http://leaf.drunkencode.net/; nullexistence180@gmail.com) Python 3.6"
        }
        # Peacock().f("wiki", str(headers))
        req = requests.get(url, headers=headers)
        self.response = req.json()

    def get_summary(self):
        if self.response is None:
            return 0, "No data returned for: " + self.query
        try:
            page = self.response["query"]["pages"][
                list(self.response["query"]["pages"].keys())[0]
            ]
            Peacock().f("wiki", "Query: " + str(page))
            p = page["extract"][:360] + "..."

        except KeyError as e:

            Peacock().f("wiki", "Response: " + str(self.response))
            Peacock().f("wiki", "Error: " + str(e))
            return 0, "Wikipedia didn't return any entries"

        else:

            return 1, {"title": page["title"], "content": p, "id": page["pageid"]}


class Define:
    def __init__(self, query: str, lang=None, which=0):
        cachename = "{}/{}".format(query, lang)
        if cachename in def_cache:
            result = def_cache[cachename]
        else:
            result = Wikt.fetch(query, lang)
            def_cache[cachename] = result
        self.alts = len(result)
        result = result[which]
        self.etymology = result["etymology"]
        self.definitions = result["definitions"]
        self.valid = bool(self.definitions)
