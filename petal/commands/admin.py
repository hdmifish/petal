"""Commands module for GUILD ADMINISTRATION.
Access: Config Whitelist"""

from petal.commands import core, shared


class CommandsAdmin(core.Commands):
    auth_fail = "This command is whitelisted."
    whitelist = "guild_admins"

    cmd_send = shared.factory_send(
        {
            "admins": {"colour": 0xA2E46D, "title": "Administrative Alert"},
            "events": {"colour": 0x1B6649, "title": "Event Announcement"},
            "mods": {"colour": 0xE67E22, "title": "Moderation Message"},
            "staff": {"colour": 0x4CCDDF, "title": "Staff Signal"},
        },
        "staff",
    )


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsAdmin
