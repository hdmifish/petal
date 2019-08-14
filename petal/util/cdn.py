"""Module dedicated to accessing the Avatar CDN."""

from typing import NewType, Union
from urllib.parse import ParseResult, urlparse

import discord
import requests

from ..config import cfg
from ..exceptions import ConfigError

__all__ = ["get_asset", "get_avatar"]


# Typing to keep the domains separate.
URL: type = NewType("URL String", str)
DiscordURL: type = NewType("Discord URL", URL)
PetalURL: type = NewType("Petal URL", URL)


def cdn_save(url: DiscordURL, dest: PetalURL = None) -> PetalURL:
    """Given a Discord Asset URL, send a PUT Request to save the Asset on the CDN.

    Raise an Exception if unsuccessful.
    """
    dest: PetalURL = convert(url) if dest is None else dest

    response: requests.Response = requests.get(url)
    if response:
        data = response.content
        saved: requests.Response = requests.put(dest, data)
        if saved:
            return dest
        else:
            saved.raise_for_status()
    else:
        response.raise_for_status()


def convert(url: DiscordURL) -> PetalURL:
    """Given a URL to the Discord CDN, convert it into the Petal Mirror.

    https://images-ext-2.discordapp.net/external/EYKxsyQBGXDjUBnfgqdaGqzT0kov7_rxRSe53PGqrNU/%3Fsize%3D1024/https/cdn.discordapp.com/avatars/106605138893889536/8fc0478f11a6f5adf6a1e970c658cded.webp
    ->
    https://{Address of CDN}/avatars/106605138893889536/8fc0478f11a6f5adf6a1e970c658cded.webp
    """
    endpoint = cfg.get("api/cdn")
    if endpoint is None:
        raise ConfigError("CDN API URL")
    else:
        parts: ParseResult = urlparse(str(url))
        # noinspection PyProtectedMember
        return PetalURL(parts._replace(netloc=endpoint).geturl())


def get_asset(url_discord: DiscordURL) -> URL:
    """Given the URL of a Discord Asset, find it in the Mirror CDN. If it is not
        there, upload it and return the Mirror URL. If it cannot be uploaded,
        return the Discord URL.
    """
    url_cdn: PetalURL = convert(url_discord)

    req: requests.Response = requests.get(url_cdn)
    if req:
        # File exists on CDN. Return.
        return url_cdn
    else:
        # File does NOT exist on CDN. Add it.
        return cdn_save(url_discord, url_cdn)


def get_avatar(user: Union[discord.Member, discord.User]) -> URL:
    """Given a Discord Member/User, check their Avatar URL, and then, if
        possible, get a Mirror of it from the Bot CDN.
    """
    url_discord: DiscordURL = user.avatar_url
    try:
        return get_asset(url_discord)
    except:
        # If anything goes wrong, return Discord URL.
        return url_discord
