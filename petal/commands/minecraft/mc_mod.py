"""Commands module for MINECRAFT-RELATED UTILITIES.
Access: Server Operators"""

from collections import defaultdict

import discord

from petal.commands.minecraft import auth
from petal.exceptions import CommandArgsError, CommandInputError, CommandOperationError
from petal.types import Src
from petal.util.fmt import escape, userline
from petal.util.grammar import sequence_words


wlpm = "You have been whitelisted on the Patch Minecraft server :D Remember that the Server Address is `minecraft.patchgaming.org`, and note that it may take up to 60 seconds to take effect."


class CommandsMCMod(auth.CommandsMCAuth):
    op = 3

    async def cmd_wlaccept(self, args, src: Src, _nosend=False, **_):
        """Mark a PlayerDB entry as "approved", to be added to the whitelist.

        If this is the first time the user is being approved, unless `--nosend` is passed, a DM will be sent to the user, if possible, to notify them that their application has been accepted.

        Same methods of specification as `{p}wlquery`; See `{p}help wlquery` for more information.

        Syntax: `{p}wlaccept <profile_identifier>`

        Options: `--nosend` :: Do not send a message to the user telling them they have been whitelisted.
        """
        if not args:
            raise CommandInputError("Provide at least one User to be accepted.")

        send = defaultdict(list)

        with self.minecraft.db():
            # Open the DB File. We do not use it directly, so it does not need
            #   to be assigned a Name; This is just to avoid excessive reads.
            for ident in args:
                with self.minecraft.db(ident) as db:
                    for entry in db:
                        if str(src.author.id) not in entry["approved"]:
                            if not entry["approved"]:
                                # This is the first Approval of this Whitelist
                                #   Application. Indicate that the user should
                                #   be sent a DM.
                                send[entry["discord"]].append(entry["name"])

                            entry["approved"].append(str(src.author.id))
                            yield self.minecraft.card(entry, title="Application Approved")
                        else:
                            yield f"You have already approved {escape(entry['name'])!r}."
            self.minecraft.export()

        if send and not _nosend:
            # Send the Users DMs to inform them of their acceptance.
            for uuid, names in send.items():
                member: discord.Member = self.client.main_guild.get_member(int(uuid))
                if member:
                    request, has = (
                        ("request", "has") if len(names) == 1 else ("requests", "have")
                    )
                    try:
                        await member.send(
                            f"Your Minecraft whitelist {request} for "
                            f"{sequence_words([repr(escape(name)) for name in names])}"
                            f" {has} been accepted. Remember that the Server"
                            f" Address is `mc.patchgaming.org`, and that it may"
                            f" take up to 60 seconds to go into effect."
                        )
                    except:
                        yield f"Failed to notify `{userline(member)}` via DM."
                    else:
                        yield f"Notified user `{userline(member)}` via DM."
                else:
                    yield f"User `{uuid}` not found."

        # yield (True, "Rebuilding Database...", True)
        # # await src.channel.trigger_typing()
        # self.mc2.rebuild()
        # yield "Rebuild complete."

        # submission = args[0]
        # # Send the submission through the function
        # reply, doSend, recipientid, mcname, wlwrite = self.minecraft.WLAdd(
        #     submission, str(src.author.id)
        # )
        #
        # if reply == 0:
        #     self.log.f(
        #         "wl+",
        #         f"{src.author.name}#{src.author.discriminator} ({src.author.id}) sets APPROVED on '{mcname}'",
        #     )
        #     if doSend and not _nosend:
        #         recipientobj = self.client.main_guild.get_member(recipientid)
        #         try:
        #             msg = await self.client.send_message(
        #                 channel=recipientobj, message=wlpm
        #             )
        #         except discord.DiscordException as e:
        #             self.log.err("Error on WLAdd PM: " + str(e))
        #             msg = None
        #         if msg:
        #             return "You have successfully approved `{}` for <@{}> and a notification PM has been sent :D".format(
        #                 mcname, recipientid
        #             )
        #         else:
        #             return "You have approved `{}` for <@{}>...But a PM could not be sent D:".format(
        #                 mcname, recipientid
        #             )
        #     else:
        #         return "You have successfully reapproved `{}` for <@{}> :D".format(
        #             mcname, recipientid
        #         )
        #     # return "You have successfully approved `{}` for <@{}> :D".format(mcname, recipientid)
        # elif reply == -2:
        #     return "You have already approved `{}` :o".format(mcname)
        # # elif reply == -:
        # #     return "Error (No Description Provided)"
        # elif reply == -7:
        #     return "Could not access the database file D:"
        # elif reply == -8:
        #     return "Cannot find a whitelist request matching `{}` D:".format(submission)
        # elif reply == -9:
        #     return "Sorry, iso and/or dav left in an unfinished function >:l"

    def cmd_wlquery(self, args, _verbose: bool = False, _v: bool = False, **_):
        """Take a string and finds any database entry that references it.

        Search terms can be Discord UUID, Minecraft UUID, or Minecraft username. Multiple (non-special) terms (space-separated) can be queried at once.
        Special search terms: `pending`, `suspended`

        Syntax: `{p}wlquery [OPTIONS] <profile_identifier> [<profile_identifier> [...]]`

        Options: `--verbose`, `-v` :: Provide more detailed information about the user.
        """
        submission = [arg.lower() for arg in args]
        _verbose = _verbose or _v

        if not submission:
            raise CommandInputError("Provide at least one Query Parameter.")

        limit = False
        show = []

        with self.minecraft.db(
            *(p for p in args if p != "pending" and p != "suspended")
        ) as db:
            if "pending" in submission:
                limit = True
                subs = [entry for entry in db if not entry.get("approved")]
                if subs:
                    for sub in subs:
                        if sub not in show:
                            show.append(sub)
                else:
                    yield "No Pending Applications found."

            if "suspended" in submission:
                limit = True
                subs = [entry for entry in db if entry.get("suspended")]
                if subs:
                    for sub in subs:
                        if sub not in show:
                            show.append(sub)
                else:
                    yield "No Suspended Users found."

            if submission and not limit:
                show.extend(db)

            if show:
                yield from (self.minecraft.card(x, _verbose) for x in show)
            else:
                raise CommandOperationError("No Users found.")

        # if "pending" in submission:
        #     searchres = []
        #     noresult = "No requests are currently pending."
        #     pList = self.minecraft.etc.WLDump()
        #     for entry in pList:
        #         if not entry["approved"]:
        #             searchres.append(entry)
        # elif "suspended" in submission or "restricted" in submission:
        #     searchres = []
        #     noresult = "No users are currently suspended."
        #     pList = self.minecraft.etc.WLDump()
        #     for entry in pList:
        #         if entry["suspended"]:
        #             searchres.append(entry)
        # else:
        #     searchres = self.minecraft.WLQuery(" ".join(submission))
        #     noresult = "No database entries matching `{}` found."
        #
        # if not searchres:
        #     return noresult.format(submission)
        # else:
        #     qout = await src.channel.send("<query loading...>")
        #     oput = "Results for {} ({}):\n".format(submission, len(searchres))
        #     for entry in searchres:
        #         oput += "**Minecraft Name: `" + entry["name"] + "`**\n"
        #         if entry.get("suspended"):
        #             oput += "Status: **`#!# SUSPENDED #!#`**\n"
        #             oput += "Reason: {}\n".format(
        #                 self.minecraft.suspend_table.get(
        #                     entry.get("suspended", True), "<ERROR>"
        #                 )
        #             )
        #         elif len(entry["approved"]) == 0:
        #             oput += "Status: *`-#- PENDING -#-`*\n"
        #         else:
        #             oput += "Status: __`--- APPROVED ---`__\n"
        #         duser = self.client.main_guild.get_member(entry.get("discord", 0))
        #         oput += "- On Discord: "
        #         if duser:
        #             oput += "**__`YES`__**\n"
        #         else:
        #             oput += "**__`! NO !`__**\n"
        #         oput += (
        #             "- Operator level: `"
        #             + str(entry.get("operator", "<ERROR>"))
        #             + "`\n"
        #         )
        #         oput += "- Minecraft UUID: `" + entry.get("uuid", "<ERROR>") + "`\n"
        #         oput += "- Discord UUID: `" + entry.get("discord", "<ERROR>") + "`\n"
        #         if _verbose:
        #             oput += (
        #                 "- Discord Tag: <@" + entry.get("discord", "<ERROR>") + ">\n"
        #             )
        #             oput += (
        #                 "- Submitted at: `" + entry.get("submitted", "<ERROR>") + "`\n"
        #             )
        #             oput += "- Alternate Usernames:\n"
        #             for pname in entry["altname"]:
        #                 oput += "  - `" + pname + "`\n"
        #             oput += "- Notes:\n"
        #             for note in entry.get("notes", []):
        #                 oput += "  - `" + note + "`\n"
        #         else:
        #             oput += "- Notes: `{}`\n".format(len(entry.get("notes", [])))
        #     oput += "--------"
        #     await qout.edit(content=oput)
        #     # return oput

    async def cmd_wlrefresh(self, **_):
        """Force an immediate rebuild of both the PlayerDB and the whitelist itself.

        Syntax: `{p}wlrefresh`
        """
        yield ("Rebuilding Database...", True)

        with self.minecraft.db() as db:
            self.minecraft.rebuild()
            for entry in db:
                if self.client.main_guild.get_member(int(entry["discord"])):
                    if entry["suspended"] == 104:
                        # User is in the Guild, but is Suspended for not being
                        #   in the Guild. Unset Suspension.
                        entry["suspended"] = 0
                        yield f"Unsuspending {entry['name']!r}."

                elif not entry["suspended"]:
                    # User is not Suspended, but is also not in the Guild. Set
                    #   Suspension.
                    entry["suspended"] = 104

            self.minecraft.export()

        yield "Rebuild complete."

        #     if self.minecraft.etc.EXPORT_WHITELIST(True, True):
        #         return "Whitelist fully refreshed."
        #     else:
        #         return "Whitelist failed to refresh."

    async def cmd_wlgone(self, _page: int = 0, **_):
        """Check the WL database for any users whose Discord ID is that of someone who has left the server.

        Syntax: `{p}wlgone`
        """

        with self.minecraft.db() as db:
            gone_users = [
                (entry["discord"], entry["name"])
                for entry in db
                if self.client.main_guild.get_member(int(entry.get("discord"))) is None
            ]

        start = 20 * _page
        stop = 20 * (_page + 1)

        yield f"Registered users who have left the Guild (Page {_page}):"
        for entry in gone_users[start:stop]:
            yield "`{}` - {}".format(*map(escape, entry))

        yield "----({}-{} of __{}__)----".format(start + 1, stop, len(gone_users))

    async def cmd_wlsuspend(self, args, _help: bool = False, _h: bool = False, **_):
        """Flag a person to be removed from the whitelist.

        Syntax: `{p}wlsuspend [OPTIONS] <code> <profile_identifier...>`

        Options: `--help`, `-h` :: Return the list of Suspension Codes and stop.
        """
        if _help or _h:
            # Command was invoked with --help or -h
            yield "Suspension codes:\n" + "\n".join(
                f"{k}: {v}"
                for k, v in self.minecraft.suspend_table.items()
                if isinstance(k, int)
            )
            return
        elif len(args) < 2:
            raise CommandInputError(
                "Provide at least one Profile Identifier with a Suspension Code."
            )
        elif not args[0].isdigit():
            raise CommandInputError("Suspension Code must be an Integer.")

        code, *targets = args
        code = int(code)

        with self.minecraft.db(*targets) as db:
            for entry in db:
                yield "Changing Suspension of {name!r} from {suspended} to {after}.".format(
                    **entry, after=code
                )
                entry["suspended"] = code

            self.minecraft.export()

        # victim = self.minecraft.WLQuery(target)
        # if victim == -7:
        #     return "No Change: Could not access database file"
        # if not victim:
        #     return "No Change: Target not found in database"
        #
        # if code.isnumeric():
        #     interp = int(code)
        # else:
        #     return "No Change: Suspension code must be numeric"
        #
        # rep, wlwin = self.minecraft.WLSuspend(victim, interp)
        # codes = {
        #     0: "Suspension successfully enabled",
        #     -1: "Suspension successfully lifted",
        #     -2: "No Change: Already suspended",
        #     -3: "No Change: Not suspended",
        #     -7: "No Change: Failed to write database",
        #     -8: "No Change: Indexing failure",
        #     -9: "Maybe no change? Something went horribly wrong D:",
        # }
        # wcode = {0: "Failed to update whitelist", 1: "Successfully updated whitelist"}
        #
        # oput = "WLSuspend Results:\n"
        # for ln in rep:
        #     oput += "-- `" + ln["name"] + "`: " + codes[ln["change"]] + "\n"
        #     self.log.f(
        #         "wl+",
        #         f"{src.author.name}#{src.author.discriminator} ({src.author.id}) sets SUSPENSION on {ln['name']}: {codes[ln['change']]}",
        #     )
        # oput += wcode[wlwin]
        #
        # return oput

    async def cmd_wlnote(self, args, **_):
        """Add a note to a user DB profile.

        Notes can be viewed with `{p}wlquery --verbose`.
        A note **must** be provided in __quotes__. Quotes may be single, double, triple-single, or triple-double.
        Quote characters may be escaped with a backslash (`\\`), or nested within quotes of a different type ("like 'this'", or 'like "this"').

        Syntax: `{p}wlnote <profile_identifier> "<note>"`
        """
        if len(args) > 2:
            raise CommandArgsError("Only one note can be added to a profile at a time.")
        elif len(args) < 2:
            raise CommandArgsError("Provide one profile identifier and one (quoted) note.")

        target, note = args

        if not note:
            raise CommandArgsError("Note cannot be empty.")

        with self.minecraft.db(target) as db:
            for entry in db:
                entry["notes"].append(note)
                yield f"Note added to {entry['name']!r}."

        # victim = self.minecraft.WLQuery(target)
        # if victim == -7:
        #     return "Could not access database file."
        # elif not victim:
        #     return "No valid target found."
        # elif len(victim) > 1:
        #     return "Ambiguous command: {} possible targets found.".format(len(victim))
        #
        # rep = self.minecraft.WLNote(victim[0]["discord"], note)
        #
        # errors = {
        #     0: "Success",
        #     -6: "Failed to write database",
        #     -7: "Failed to read database",
        #     -8: "Target not found in database",
        # }
        #
        # if not rep:
        #     return "{} has been noted: `{}`".format(victim[0]["name"], note)
        # else:
        #     return errors.get(rep, "Unknown Error ('{}')".format(rep))


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMCMod
