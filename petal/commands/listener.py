"""Commands module for LISTENER-RELATED UTILITIES.
Access: Role-based"""

from datetime import datetime as dt, timedelta

import discord

from petal.commands import core


class CommandsListener(core.Commands):
    auth_fail = "This command requires the `{role}` role."
    role = "RoleListener"

    async def cmd_lpromote(self, src, _user=None, **_):

        if _user is None:
            await self.client.send_message(
                src.author, src.channel, "Who would you like to promote?"
            )
            response = await self.client.wait_for_message(
                channel=src.channel, author=src.author, timeout=60
            )
            response = response.content
            _user = self.get_member(src, response.strip())
            if response is None:
                return "Timed out after 1 minute..."

            if _user is None:
                return "No user found for that name, try again"

        cb = self.config.get("choppingBlock")

        if _user.id in cb:
            if (cb[_user.id]["timeout"] - dt.utcnow()).total_seconds() >= 0:
                if src.author.id not in cb[_user.id]["votes"]:
                    cb[_user.id]["votes"][src.author.id] = 1
                    return "You have voted to promote, " + _user.name
                else:
                    return "You already voted..."
            else:
                return (
                    "The time to vote on this user has expired. Please run "
                    + self.config.prefix
                    + "lvalidate to add them to the roster"
                )
        else:
            if self.check_user_has_role(_user, "Helping Hands"):
                return "This user is already a Helping Hands..."
            now = dt.utcnow() + timedelta(days=2)
            cb[_user.id] = {
                "votes": {src.author.id: 1},
                "started_by": src.author.id,
                "timeout": now,
                "server_id": _user.server.id,
            }
            return (
                "A vote to promote {0}#{1} has been started, it will end in 48 hours.".format(
                    _user.name, _user.discriminator
                )
                + "\nYou man cancel this vote by running "
                + self.config.prefix
                + "lcancel (not to be confused with smash bros)"
            )

    async def cmd_ldemote(self, src, _user=None, **_):
        if _user is None:
            await self.client.send_message(
                src.author, src.channel, "Who would you like to demote?"
            )
            response = await self.client.wait_for_message(
                channel=src.channel, author=src.author, timeout=60
            )
            response = response.content
            _user = self.get_member(src, response.strip())
            if response is None:
                return "Timed out after 1 minute..."

            if _user is None:
                return "No user found for that name, try again"

        cb = self.config.get("choppingBlock")
        if _user.id in cb:
            if (cb[_user.id]["timeout"] - dt.utcnow()).total_seconds() >= 0:
                if src.author.id not in cb[_user.id]["votes"]:
                    cb[_user.id]["votes"][src.author.id] = -1
                    return "You have voted to demote, " + _user.name
                else:
                    return "You already voted..."
            else:
                return (
                    "The time to vote on this user has expired. Please run "
                    + self.config.prefix
                    + "lvalidate to add them to the roster"
                )
        else:
            if not self.check_user_has_role(_user, "Helping Hands"):
                return (
                    "This user is not a member of Helping Hands. I cannot demote them"
                )
            now = dt.utcnow() + timedelta(days=2)
            cb[_user.id] = {
                "votes": {src.author.id: -1},
                "started_by": src.author.id,
                "timeout": now,
                "server_id": _user.server.id,
            }
            return (
                "A vote to demote {0}#{1} has been started, it will end in 48 hours.".format(
                    _user.name, _user.discriminator
                )
                + "\nYou may cancel this vote by running "
                + self.config.prefix
                + "lcancel (not to be confused with smash bros)"
            )

    async def cmd_lcancel(self, src, **_):
        """
        Cancels all lvotes you started. Does not validate them.
        !lcancel
        """
        cb = self.config.get("choppingBlock")
        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."

        if cb is None:
            return "lvotes are disabled in config."

        temp = {}
        for entry in cb:
            try:
                if cb["started_by"] == src.author.id:
                    temp[entry] = cb[entry]
            except KeyError:
                temp[entry] = cb[entry]

        for e in temp:
            print("Deleted: " + str(self.config.doc["choppingBlock"][e]))
            del self.config.doc["choppingBlock"][e]

        self.config.save()
        return "Deleted all lvotes if you had started any"

    async def cmd_lvalidate(self, src, _user=None, **_):
        """
        Ends a vote and promotes/demotes user. Can be used prematurely
        !lvalidate <optional: tagged user>
        """

        cb = self.config.get("choppingBlock")

        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."
        if _user is None:
            await self.client.send_message(
                src.author, src.channel, "Which user would you like to validate?"
            )
            response = await self.client.wait_for_message(
                channel=src.channel, author=src.author, timeout=60
            )
            response = response.content
            _user = self.get_member(src, response.strip())
            if response is None:
                return "Timed out after 1 minute..."

            if _user is None:
                return "No user found for that name, try again"

        if _user.id not in cb:

            return "That user is not in the list, therefore I can't do anything."

        else:
            votelist = cb[_user.id]["votes"]
            if len(votelist) < 2:
                return (
                    "Not enough votes to pass, cancel the poll or wait longer. You may cancel with "
                    + self.config.prefix
                    + "lcancel"
                )

            score = 0
            for entry in votelist:
                score += votelist[entry]

            if len(votelist) == 2 and score not in [-2, 2]:
                return (
                    "Not enough votes to promote/demote. Sorry, maybe discuss more. Or if this is an error,"
                    " let a manager/admin know"
                )

            elif len(votelist) == 2 and score in [-2, 2]:
                if score == -2:
                    await self.client.remove_roles(
                        _user, discord.utils.get(src.server.roles, name="Helping Hands")
                    )
                    try:
                        await self.client.send_message(
                            src.author,
                            _user,
                            "Following a vote by the listeners: "
                            "you have been removed from helping hands for now",
                        )
                        del self.config.doc["choppingBlock"][_user.id]
                        self.config.save()
                    except:
                        return "User could not be PM'd but they are a member of Helping Hands no more"
                    else:
                        return _user.name + " has been removed from Helping Hands"
                else:
                    cb[_user.id]["pending"] = True
                    cb[_user.id]["server_id"] = src.server.id
                    cb[_user.id]["channel_id"] = src.channel.id

                    try:
                        await self.client.send_message(
                            src.author,
                            _user,
                            "Following a vote by the listeners: you have been chosen "
                            "to be a Helping Hands! Reply !Laccept or !Lreject",
                        )

                    except:
                        return (
                            "User could not be PM'd but they are a now able to become a member of Helping Hands."
                            "\nLet them know to type !Laccept or !Lreject in PMs in leaf"
                        )
                    else:
                        return (
                                _user.name + " has been made a member of Helping Hands."
                            "\nThey must accept the invite by following the instruction I just sent them"
                        )

            else:
                avg = float(score / len(votelist))
                if -0.85 < avg < 0.85:
                    return "You need 85% of votes to pass current score:" + str(
                        abs(avg * 100.00)
                    )

                elif avg < -0.85:
                    await self.client.remove_roles(
                        _user, discord.utils.get(src.server.roles, name="Helping Hands")
                    )
                    try:
                        await self.client.send_message(
                            src.author,
                            _user,
                            "Following a vote by your fellow Helping Handss,"
                            " you have been demoted for the time being.",
                        )

                        del self.config.doc["choppingBlock"][_user.id]
                        self.config.save()

                    except:
                        return "User could not be PM'd but they are a Helping Hands no more"
                    else:
                        return _user.name + " has been removed from Helping Hands"

                elif avg > 0.85:
                    cb[_user.id]["pending"] = True
                    try:
                        await self.client.send_message(
                            src.author,
                            _user,
                            "Following a vote by your fellow members you have been chosen "
                            "to be a Helping Hands! Type !Laccept in any channel. "
                            "Or !Lreject if you wanna not become a Helping Hands",
                        )
                    except:
                        return (
                            "User could not be PM'd but they are a now able to become a Helping Hands."
                            "\nLet them know to type !Laccept in a channel"
                        )
                    else:
                        return (
                                _user.name
                                + " has been made a Helping Hands!\nThey must accept"
                            " the invite by following the instruction I just sent them"
                        )

    async def cmd_laccept(self, src, **_):
        """
        If you were voted to be a Helping Hands, running this command will accept the offer. Otherwise, run !Lreject
        !laccept
        """
        cb = self.config.get("choppingBlock")

        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."
        if not src.channel.is_private:
            return "You must reply only in PMs with petal. Not in a channel"
        if src.author.id in cb:
            if "pending" in cb[src.author.id]:
                svr = self.client.get_server(cb[src.author.id]["server_id"])
                if svr is None:
                    return (
                        "Error fetching server with ID: "
                        + cb[src.author.id]["server_id"]
                        + " ask who promoted you to do it manually"
                    )
                member = svr.get_member(src.author.id)
                await self.client.add_roles(
                    member, discord.utils.get(svr.roles, name="Helping Hands")
                )

                chan = svr.get_channel(cb[src.author.id]["channel_id"])
                del self.config.doc["choppingBlock"][src.author.id]
                self.config.save()
                if chan is None:
                    return "You will need to tell them you have accepted as I could not notify them"
                else:
                    await self.client.send_message(
                        src.author,
                        chan,
                        "Just letting y'all know that "
                        + member.name
                        + " has accepted their role",
                    )

                return "Welcome!"
            else:
                return "You don't have a pending invite to join the Helping Hands at this time"

    async def cmd_lreject(self, src, **_):
        """
        If you were voted to be a Helping Hands, running this command will reject the offer.
        !lreject
        """
        cb = self.config.get("choppingBlock")

        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."

        if src.author.id in cb:
            if "pending" in cb[src.author.id]:

                svr = self.client.get_server(cb[src.author.id]["server_id"])
                if svr is not None:
                    chan = svr.get_channel(cb[src.author.id]["channel_id"])
                else:
                    chan = None
                if chan is None:
                    return "You will need to tell them you have accepted as I could not notify them"
                else:
                    await self.client.send_message(
                        src.author,
                        chan,
                        "Just letting y'all know that "
                        + src.author.name
                        + " has rejected their role",
                    )
                del self.config.doc["choppingBlock"][src.author.id]
                self.config.save()
                return "You have rejected to join the helping hands. If this was on accident, let a listener know"
            else:
                return "You don't have a pending invite to join the Helping Handss at this time"

    async def cmd_lshow(self, src, **_):
        """
       If you were voted to be a Helping Hands, running this command will reject the offer.
       !lreject
       """
        cb = self.config.get("choppingBlock")

        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."

        msg = ""
        for entry in cb:
            mem = self.get_member(src, entry)
            if mem is None:
                continue
            starter = self.get_member(src, cb[entry]["started_by"])
            if starter is None:
                continue
            msg += (
                "\n------\nVote started for: "
                + mem.name
                + "\#"
                + mem.discriminator
                + "\nstarted by: "
                + starter.name
                + "#"
                + starter.discriminator
                + "\n------\n"
            )

        return "Heres what votes are goin on: \n" + msg


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsListener
