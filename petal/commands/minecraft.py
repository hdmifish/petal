"""Commands module for MINECRAFT-RELATED UTILITIES.
Access: Server Operators"""

import discord

from . import core
from petal.mcutil import Minecraft


class CommandsMinecraft(core.Commands):
    auth_fail = "This command requires Operator status on the Minecraft server."

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.minecraft = Minecraft(self.client)

    def authenticate(self, src):
        # For now, commands in this module authenticate individually.
        return True

    def check(self, src, level):
        """
        Check that the MC config is valid, and that the user has clearance.
        """
        mclists = (
            self.config.get("minecraftDB"),
            self.config.get("minecraftWL"),
            self.config.get("minecraftOP"),
        )
        if None in mclists:
            return (
                "Looks like the bot owner doesn't have the whitelist configured. Sorry."
            )
        mcchan = self.config.get("mc_channel")
        if mcchan is None:
            return (
                "Looks like the bot owner doesn't have an mc_channel configured. Sorry."
            )
        mcchan = self.client.get_channel(mcchan)
        if mcchan is None:
            return (
                "Looks like the bot owner doesn't have an mc_channel configured. Sorry."
            )
        if level != -1 and not self.minecraft.WLAuthenticate(src, level):
            return "Authentication failure: This command requires Minecraft Operator level {}.".format(
                level
            )

    # TODO: Rewrite all MC commands fully

    async def cmd_wlme(self, args, src, **_):
        """Submit your Minecraft username to be whitelisted on the community server.

        The whitelist is curated and managed by Petal for convenience, security, and consistency.

        Syntax: `{p}wlme <minecraft_username>`
        """
        failure = self.check(src, -1)
        if failure:
            return failure

        if not args:
            return "You need to include your Minecraft username, or I will not be able to find you! Like this: `{}wlme Notch` :D".format(
                self.config.prefix
            )

        submission = args[0]
        reply, uuid = self.minecraft.WLRequest(
            submission, src.author.id
        )  # Send the submission through the new function

        if reply == 0:

            try:  # For now, just gonna do this just in case
                self.log.f(
                    "wl+",
                    f"{src.author.name}#{src.author.discriminator} ({src.author.id}) creates NEW ENTRY for '{src.content[len(self.config.prefix) + 4:]}'",
                )
            except:
                pass

            wlreq = await self.client.send_message(
                channel=self.config.mc_channel, message="`<request loading...>`"
            )

            await self.client.edit_message(
                message=wlreq,
                new_content="Whitelist Request from: `"
                + src.author.name
                + "#"
                + src.author.discriminator
                + "` with request: "
                + src.content[len(self.config.prefix) + 4 :]
                + "\nTaggable: <@"
                + src.author.id
                + ">\nDiscord ID:  "
                + src.author.id
                + "\nMojang UID:  "
                + uuid,
            )

            return "Your whitelist request has been successfully submitted :D"
        elif reply == -1:
            return "No need, you are already whitelisted :D"
        elif reply == -2:
            return "That username has already been submitted for whitelisting :o"
        # elif reply == -:
        #     return "Error (No Description Provided)"
        elif reply == -7:
            return "Could not access the database file D:"
        elif reply == -8:
            return (
                "That does not seem to be a valid Minecraft username D: "
                + "DEBUG: "
                + submission
            )
        elif reply == -9:
            return "Sorry, iso and/or dav left in an unfinished function >:l"
        else:
            return "Nondescript Error ({})".format(reply)

    async def cmd_wlaccept(self, args, src, **_):
        """Mark a PlayerDB entry as "approved", to be added to the whitelist.

        Same methods of specification as {p}WLQuery; See `{p}help wlquery` for more information.

        Syntax: `{p}wlaccept <profile_identifier>`
        """
        failure = self.check(src, 3)
        if failure:
            return failure

        # separated this for simplicity
        submission = args[0]
        # Send the submission through the function
        reply, doSend, recipientid, mcname, wlwrite = self.minecraft.WLAdd(
            submission, src.author.id
        )

        if reply == 0:
            try:  # For now, just gonna do this just in case
                self.log.f(
                    "wl+",
                    f"{src.author.name}#{src.author.discriminator} ({src.author.id}) sets APPROVED on '{mcname}'",
                )
            except:
                pass
            if doSend:
                recipientobj = self.client.get_server(
                    self.config.get("mainServer")
                ).get_member(recipientid)
                try:
                    wlpm = "You have been whitelisted on the Patch Minecraft server :D Remember that the IP is `minecraft.patchgaming.org`, and note that it may take up to 60 seconds to take effect"
                    await self.client.send_message(channel=recipientobj, message=wlpm)
                except discord.DiscordException as e:
                    self.log.err("Error on WLAdd PM: " + str(e))
                    return "You have approved `{}` for <@{}>...But a PM could not be sent D:".format(
                        mcname, recipientid
                    )
                else:
                    return "You have successfully approved `{}` for <@{}> and a notification PM has been sent :D".format(
                        mcname, recipientid
                    )
            else:
                return "You have successfully reapproved `{}` for <@{}> :D".format(
                    mcname, recipientid
                )
            # return "You have successfully approved `{}` for <@{}> :D".format(mcname, recipientid)
        elif reply == -2:
            return "You have already approved `{}` :o".format(mcname)
        # elif reply == -:
        #     return "Error (No Description Provided)"
        elif reply == -7:
            return "Could not access the database file D:"
        elif reply == -8:
            return "Cannot find a whitelist request matching `{}` D:".format(submission)
        elif reply == -9:
            return "Sorry, iso and/or dav left in an unfinished function >:l"

    async def cmd_wlquery(self, args, src, verbose=False, v=False, **_):
        """Take a string and finds any database entry that references it.

        Search terms can be Discord UUID, Minecraft UUID, or Minecraft username. Multiple (non-special) terms (space-separated) can be queried at once.
        Special search terms: `pending`, `suspended`

        Syntax: `{p}wlquery [OPTIONS] <profile_identifier> [<profile_identifier> [...]]`

        Options: `--verbose`, `-v` :: Provide more detailed information about the user.
        """
        failure = self.check(src, 2)
        if failure:
            return failure

        submission = [arg.lower() for arg in args]
        verbose = True in [verbose, v]

        if "pending" in submission:
            searchres = []
            noresult = "No requests are currently pending."
            pList = self.minecraft.etc.WLDump()
            for entry in pList:
                if not entry["approved"]:
                    searchres.append(entry)
        elif "suspended" in submission or "restricted" in submission:
            searchres = []
            noresult = "No users are currently suspended."
            pList = self.minecraft.etc.WLDump()
            for entry in pList:
                if entry["suspended"]:
                    searchres.append(entry)
        else:
            searchres = self.minecraft.WLQuery(" ".join(submission))
            noresult = "No database entries matching `{}` found."

        if not searchres:
            return noresult.format(submission)
        else:
            qout = await self.client.send_message(
                channel=src.channel, message="<query loading...>"
            )
            oput = "Results for {} ({}):\n".format(submission, len(searchres))
            for entry in searchres:
                oput += "**Minecraft Name: `" + entry["name"] + "`**\n"
                if entry.get("suspended"):
                    oput += "Status: **`#!# SUSPENDED #!#`**\n"
                    oput += "Reason: {}\n".format(
                        self.minecraft.suspend_table.get(
                            entry.get("suspended", True), "<ERROR>"
                        )
                    )
                elif len(entry["approved"]) == 0:
                    oput += "Status: *`-#- PENDING -#-`*\n"
                else:
                    oput += "Status: __`--- APPROVED ---`__\n"
                duser = self.client.get_server(
                    self.config.get("mainServer")
                ).get_member(entry.get("discord", 0))
                oput += "- On Discord: "
                if duser:
                    oput += "**__`YES`__**\n"
                else:
                    oput += "**__`! NO !`__**\n"
                oput += (
                    "- Operator level: `"
                    + str(entry.get("operator", "<ERROR>"))
                    + "`\n"
                )
                oput += "- Minecraft UUID: `" + entry.get("uuid", "<ERROR>") + "`\n"
                oput += "- Discord UUID: `" + entry.get("discord", "<ERROR>") + "`\n"
                if verbose:
                    oput += (
                        "- Discord Tag: <@" + entry.get("discord", "<ERROR>") + ">\n"
                    )
                    oput += (
                        "- Submitted at: `" + entry.get("submitted", "<ERROR>") + "`\n"
                    )
                    oput += "- Alternate Usernames:\n"
                    for pname in entry["altname"]:
                        oput += "  - `" + pname + "`\n"
                    oput += "- Notes:\n"
                    for note in entry.get("notes", []):
                        oput += "  - `" + note + "`\n"
                else:
                    oput += "- Notes: `{}`\n".format(len(entry.get("notes", [])))
            oput += "--------"
            await self.client.edit_message(message=qout, new_content=oput)
            # return oput

    async def cmd_wlrefresh(self, src, **_):
        """Force an immediate rebuild of both the PlayerDB and the whitelist itself.

        Syntax: `{p}wlrefresh`
        """
        failure = self.check(src, 2)
        if failure:
            return failure

        await self.client.send_typing(src.channel)
        refreshReturn = self.minecraft.etc.EXPORT_WHITELIST(True, True)
        refstat = ["Whitelist failed to refresh.", "Whitelist Fully Refreshed."]

        return refstat[refreshReturn]

    async def cmd_wlgone(self, src, **_):
        """Check the WL database for any users whose Discord ID is that of someone who has left the server.

        Syntax: `{p}wlgone`
        """
        failure = self.check(src, 2)
        if failure:
            return failure

        uList = self.minecraft.etc.WLDump()
        idList = []
        for entry in uList:
            idList.append(entry["discord"])
        oput = "Registered users who have left the server:\n"
        leftnum = 0
        for userid in idList:
            try:
                user = self.client.get_server(self.config.get("mainServer")).get_member(
                    userid
                )
                if user is None:
                    oput = oput + userid + "\n"
                    leftnum += 1
            except:  # Dont log an error here; An error here means a success
                oput = oput + userid + "\n"
                leftnum += 1
        oput = oput + "----({})----".format(leftnum)
        return oput

    async def cmd_wlsuspend(self, src, **_):
        """Flag a person to be removed from the whitelist.

        Syntax: `{p}wlsuspend help`
        `{p}wlsuspend <profile_identifier> <code>`
        """
        failure = self.check(src, 3)
        if failure:
            return failure

        wordPos = ["true", "on", "yes", "active", "enable"]
        wordNeg = ["false", "off", "no", "inactive", "disable"]
        submission = src.content[
            len(self.config.prefix) + 9 :
        ].strip()  # separated this for simplicity

        sub0 = submission.lower().split()
        # ["username", "rest", "of", "the", "message"]
        sub1 = sub0[0]  # "username"
        if len(sub0) > 1:
            sub2 = sub0[1]  # "rest"
        else:
            sub2 = ""

        if sub1.lower() == "help":
            return "Suspension codes:\n" + "\n".join(
                ["{}: {}".format(k, v) for k, v in self.minecraft.suspend_table.items()]
            )

        victim = self.minecraft.WLQuery(sub1)
        if victim == -7:
            return "Could not access database file"
        if not victim:
            return "No results"

        # A far more reasonable argument processor
        if sub2.isnumeric():
            interp = int(sub2)
        elif sub2 in wordPos:
            interp = True
        elif sub2 in wordNeg:
            interp = 0
        else:
            return "As the great Eddie Izzard once said, 'I'm not sure what you're trying to do...'"

        rep, wlwin = self.minecraft.WLSuspend(victim, interp)
        codes = {
            0: "Suspension successfully enabled",
            -1: "Suspension successfully lifted",
            -2: "No Change: Already suspended",
            -3: "No Change: Not suspended",
            -7: "No Change: Failed to write database",
            -8: "No Change: Indexing failure",
            -9: "Maybe no change? Something went horribly wrong D:",
        }
        wcode = {0: "Failed to update whitelist", 1: "Successfully updated whitelist"}

        oput = "WLSuspend Results:\n"
        for ln in rep:
            oput = oput + "-- `" + ln["name"] + "`: " + codes[ln["change"]] + "\n"
            try:  # For now, just gonna do this just in case
                self.log.f(
                    "wl+",
                    f"{src.author.name}#{src.author.discriminator} ({src.author.id}) sets SUSPENSION on {ln['name']}: {codes[ln['change']]}",
                )
            except:
                pass
        oput = oput + wcode[wlwin]

        return oput

    async def cmd_wlmod(self, src, **_):
        """Flag a person to be given a level of operator status.

        Level 1 can: Bypass spawn protection.
        Level 2 can: Use `/clear`, `/difficulty`, `/effect`, `/gamemode`, `/gamerule`, `/give`, `/summon`, `/setblock `and `/tp`, and can edit command blocks.
        Level 3 can: Use `/ban`, `/deop`, `/whitelist`, `/kick`, and `/op`.
        Level 4 can: Use `/stop`.
        (<https://gaming.stackexchange.com/questions/138602/what-does-op-permission-level-do>)

        Syntax: `{p}wlmod <profile_identifier> (0|1|2|3|4)`
        """
        failure = self.check(src, 4)
        if failure:
            return failure

        # separated this for simplicity
        submission = src.content[len(self.config.prefix) + 5 :].strip()

        sub0 = submission.lower().split(" ")
        # ["username", "rest", "of", "the", "message"]
        sub1 = sub0[0]  # "username"
        try:
            level = int(sub0[1])  # "rest"
        except:
            level = -1
        if not 0 <= level <= 4:
            return "You need to specify an op level for {} between `0` and `4` D:".format(
                sub1
            )

        victim = self.minecraft.WLQuery(sub1)
        if victim == -7:
            return "Could not access database file."
        elif not victim:
            return "No valid target found."
        elif len(victim) > 1:
            return "Ambiguous command: {} possible targets found.".format(
                str(len(victim))
            )
        elif src.author.id == victim[0]["discord"]:
            return "You cannot change your own Operator status."

        # rep, doSend, targetid, targetname, wlwin = self.minecraft.WLMod(victim[0], level)
        rep = self.minecraft.WLMod(victim[0]["discord"], level)

        return "{} has been granted __Level {} Operator__ status. Return values: `{}`".format(
            victim[0]["name"], level, "`, `".join([str(term) for term in rep])
        )

    async def cmd_wlnote(self, src, **_):
        """Add a note to a user DB profile.

        Syntax: `{p}wlnote`
        """
        failure = self.check(src, 3)
        if failure:
            return failure

        # separated this for simplicity
        submission = src.content[len(self.config.prefix) + 6 :].strip()

        sub0 = submission.lower().split(" ", 1)
        # ["username", "rest of the message"]
        sub1 = sub0[0]  # "username"
        try:
            note = int(sub0[1])  # "rest of the message"
        except:
            note = ""
        if not note:
            return

        victim = self.minecraft.WLQuery(sub1)
        if victim == -7:
            return "Could not access database file."
        elif not victim:
            return "No valid target found."
        elif len(victim) > 1:
            return "Ambiguous command: {} possible targets found.".format(
                str(len(victim))
            )

        rep = self.minecraft.WLNote(victim[0]["discord"], note)

        errors = {
            0: "Success",
            -6: "Failed to write database",
            -7: "Failed to read database",
            -8: "Target not found in database",
        }

        if not rep:
            return "{} has been noted: `{}`".format(victim[0]["name"], note)
        else:
            return errors.get(rep, "Unknown Error ('{}')".format(rep))


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMinecraft
