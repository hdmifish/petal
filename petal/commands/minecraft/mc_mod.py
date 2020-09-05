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

    async def cmd_wlrefresh(self, _full: bool = False, **_):
        """Force an immediate rebuild of both the PlayerDB and the whitelist itself.

        Syntax: `{p}wlrefresh [OPTIONS]`

        Options:
            `--full` :: Do a complete rebuild, instead of simply checking for auto-suspensions.
        """
        yield "Rebuilding Database...", True

        with self.minecraft.db() as db:
            if _full:
                await self.minecraft.rebuild()

            for entry in db:
                id_discord: int = int(entry["discord"])

                if self.client.main_guild.get_member(id_discord):
                    if entry["suspended"] == 104:
                        # User is in the Guild, but is Suspended for not being
                        #   in the Guild. Unset Suspension.
                        entry["suspended"] = 0
                        yield f"Unsuspending {entry['name']!r}."

                elif not entry["suspended"]:
                    # User is not Suspended, but is also not in the Guild. Set
                    #   Suspension.
                    entry["suspended"] = 104
                    yield f"Suspending {entry['name']!r}."

            self.minecraft.export()

        yield "Rebuild complete."

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
                for k, v in self.minecraft.suspensions.items()
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


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsMCMod
