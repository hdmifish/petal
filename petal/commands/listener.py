"""Commands module for LISTENER-RELATED UTILITIES.
Access: Role-based"""

import asyncio
from datetime import datetime as dt, timedelta

import discord

from . import core


class CommandsListener(core.Commands):
    auth_fail = "This command requires the Listener role."

    def authenticate(self, src):
        return self.check_user_has_role(src.author, "Listener")

    async def lpromote(self, message, user=None):

        if user is None:
            await self.client.send_message(
                message.author, message.channel, "Who would you like to promote?"
            )
            response = await self.client.wait_for_message(
                channel=message.channel, author=message.author, timeout=60
            )
            response = response.content
            user = self.get_member(message, response.strip())
            if response is None:
                return "Timed out after 1 minute..."

            if user is None:
                return "No user found for that name, try again"

        cb = self.config.get("choppingBlock")

        if user.id in cb:
            if (cb[user.id]["timeout"] - dt.utcnow()).total_seconds() >= 0:
                if message.author.id not in cb[user.id]["votes"]:
                    cb[user.id]["votes"][message.author.id] = 1
                    return "You have voted to promote, " + user.name
                else:
                    return "You already voted..."
            else:
                return (
                    "The time to vote on this user has expired. Please run "
                    + self.config.prefix
                    + "lvalidate to add them to the roster"
                )
        else:
            if self.check_user_has_role(user, "Helping Hands"):
                return "This user is already a Helping Hands..."
            now = dt.utcnow() + timedelta(days=2)
            cb[user.id] = {
                "votes": {message.author.id: 1},
                "started_by": message.author.id,
                "timeout": now,
                "server_id": user.server.id,
            }
            return (
                "A vote to promote {0}#{1} has been started, it will end in 48 hours.".format(
                    user.name, user.discriminator
                )
                + "\nYou man cancel this vote by running "
                + self.config.prefix
                + "lcancel (not to be confused with smash bros)"
            )

    async def ldemote(self, message, user=None):
        if user is None:
            await self.client.send_message(
                message.author, message.channel, "Who would you like to demote?"
            )
            response = await self.client.wait_for_message(
                channel=message.channel, author=message.author, timeout=60
            )
            response = response.content
            user = self.get_member(message, response.strip())
            if response is None:
                return "Timed out after 1 minute..."

            if user is None:
                return "No user found for that name, try again"

        cb = self.config.get("choppingBlock")
        if user.id in cb:
            if (cb[user.id]["timeout"] - dt.utcnow()).total_seconds() >= 0:
                if message.author.id not in cb[user.id]["votes"]:
                    cb[user.id]["votes"][message.author.id] = -1
                    return "You have voted to demote, " + user.name
                else:
                    return "You already voted..."
            else:
                return (
                    "The time to vote on this user has expired. Please run "
                    + self.config.prefix
                    + "lvalidate to add them to the roster"
                )
        else:
            if not self.check_user_has_role(user, "Helping Hands"):
                return (
                    "This user is not a member of Helping Hands. I cannot demote them"
                )
            now = dt.utcnow() + timedelta(days=2)
            cb[user.id] = {
                "votes": {message.author.id: -1},
                "started_by": message.author.id,
                "timeout": now,
                "server_id": user.server.id,
            }
            return (
                "A vote to demote {0}#{1} has been started, it will end in 48 hours.".format(
                    user.name, user.discriminator
                )
                + "\nYou may cancel this vote by running "
                + self.config.prefix
                + "lcancel (not to be confused with smash bros)"
            )

    async def lvote(self, message):
        """
        ITs back boooyyyysssss!!!!
        !lvote
        """
        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."

        if not self.check_user_has_role(message.author, "Listener"):
            return "You must be a Listener to vote on Helping Hands"
        args = self.clean_input(message.content)
        user = None
        if args[0] != "":
            user = self.get_member(message, args[0])
            if user is None:
                return "No member with that id..."

        while 1:
            await self.client.send_message(
                message.author, message.channel, "Are we calling to promote or demote?"
            )
            response = await self.client.wait_for_message(
                channel=message.channel, author=message.author, timeout=20
            )

            if response is None:
                return "You didn't reply so I timed out..."
            response = response.content
            if response.lower() in ["promote", "p"]:
                response = await self.lpromote(message, user)
                self.config.save()
                return response
            elif response.lower() in ["demote", "d"]:
                response = await self.ldemote(message, user)
                self.config.save()
                return response
            else:
                await self.client.send_message(
                    message.author, message.channel, "Type promote or type demote [pd]"
                )
                await asyncio.sleep(1)

    async def lcancel(self, message):
        """
        Cancels all lvotes you started. Does not validate them.
        !lcancel
        """
        cb = self.config.get("choppingBlock")
        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."

        if not self.check_user_has_role(message.author, "Listener"):
            return "You are not a Listener You cannot use this feature"
        if cb is None:
            return "lvotes are disabled in config, why are you even running this command...?"

        temp = {}
        for entry in cb:
            try:
                if cb["started_by"] == message.author.id:
                    temp[entry] = cb[entry]
            except KeyError as e:
                temp[entry] = cb[entry]

        for e in temp:
            print("Deleted: " + str(self.config.doc["choppingBlock"][e]))
            del self.config.doc["choppingBlock"][e]

        self.config.save()
        return "Deleted all lvotes if you had started any"

    async def lvalidate(self, message, user=None):
        """
        Ends a vote and promotes/demotes user. Can be used prematurely
        !lvalidate <optional: tagged user>
        """

        cb = self.config.get("choppingBlock")

        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."
        if not self.check_user_has_role(message.author, "Listener"):
            return "You are not a Listener You cannot use this feature"
        if user is None:
            await self.client.send_message(
                message.author,
                message.channel,
                "Which user would you like to validate?",
            )
            response = await self.client.wait_for_message(
                channel=message.channel, author=message.author, timeout=60
            )
            response = response.content
            user = self.get_member(message, response.strip())
            if response is None:
                return "Timed out after 1 minute..."

            if user is None:
                return "No user found for that name, try again"

        if user.id not in cb:

            return (
                "That user is not in the list, therefore I can't do anything. Here's a cat though.\n"
                + await self.cat(message)
            )

        else:
            votelist = cb[user.id]["votes"]
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
                        user,
                        discord.utils.get(message.server.roles, name="Helping Hands"),
                    )
                    try:
                        await self.client.send_message(
                            message.author,
                            user,
                            "Following a vote by the listeners: "
                            "you have been removed from helping hands for now",
                        )
                        del self.config.doc["choppingBlock"][user.id]
                        self.config.save()
                    except:
                        return "User could not be PM'd but they are a member of Helping Hands no more"
                    else:
                        return user.name + " has been removed from Helping Hands"
                else:
                    cb[user.id]["pending"] = True
                    cb[user.id]["server_id"] = message.server.id
                    cb[user.id]["channel_id"] = message.channel.id

                    try:
                        mop = await self.client.send_message(
                            message.author,
                            user,
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
                            user.name + " has been made a member of Helping Hands."
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
                        user,
                        discord.utils.get(message.server.roles, name="Helping Hands"),
                    )
                    try:
                        await self.client.send_message(
                            message.author,
                            user,
                            "Following a vote by your fellow Helping Handss,"
                            " you have been demoted for the time being.",
                        )

                        del self.config.doc["choppingBlock"][user.id]
                        self.config.save()

                    except:
                        return "User could not be PM'd but they are a Helping Hands no more"
                    else:
                        return user.name + " has been removed from Helping Hands"

                elif avg > 0.85:
                    cb[user.id]["pending"] = True
                    try:
                        await self.client.send_message(
                            message.author,
                            user,
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
                            user.name
                            + " has been made a Helping Hands!\nThey must accept"
                            " the invite by following the instruction I just sent them"
                        )

    async def laccept(self, message):
        """
        If you were voted to be a Helping Hands, running this command will accept the offer. Otherwise, run !Lreject
        !laccept
        """
        cb = self.config.get("choppingBlock")

        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."
        if not message.channel.is_private:
            return "You must reply only in PMs with petal. Not in a channel"
        if message.author.id in cb:
            if "pending" in cb[message.author.id]:
                svr = self.client.get_server(cb[message.author.id]["server_id"])
                if svr is None:
                    return (
                        "Error fetching server with ID: "
                        + cb[message.author.id]["server_id"]
                        + " ask who promoted you to do it manually"
                    )
                member = svr.get_member(message.author.id)
                await self.client.add_roles(
                    member, discord.utils.get(svr.roles, name="Helping Hands")
                )

                chan = svr.get_channel(cb[message.author.id]["channel_id"])
                del self.config.doc["choppingBlock"][message.author.id]
                self.config.save()
                if chan is None:
                    return "You will need to tell them you have accepted as I could not notify them"
                else:
                    await self.client.send_message(
                        message.author,
                        chan,
                        "Just letting y'all know that "
                        + member.name
                        + " has accepted their role",
                    )

                return "Welcome!"
            else:
                return "You don't have a pending invite to join the Helping Hands at this time"

    async def lreject(self, message):
        """
        If you were voted to be a Helping Hands, running this command will reject the offer.
        !lreject
        """
        cb = self.config.get("choppingBlock")

        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."

        if message.author.id in cb:
            if "pending" in cb[message.author.id]:

                svr = self.client.get_server(cb[message.author.id]["server_id"])
                if svr is not None:
                    chan = svr.get_channel(cb[message.author.id]["channel_id"])
                else:
                    chan = None
                if chan is None:
                    return "You will need to tell them you have accepted as I could not notify them"
                else:
                    await self.client.send_message(
                        message.author,
                        chan,
                        "Just letting y'all know that "
                        + message.author.name
                        + " has rejected their role",
                    )
                del self.config.doc["choppingBlock"][message.author.id]
                self.config.save()
                return "You have rejected to join the helping hands. If this was on accident, let a listener know"
            else:
                return "You don't have a pending invite to join the Helping Handss at this time"

    async def lshow(self, message):
        """
       If you were voted to be a Helping Hands, running this command will reject the offer.
       !lreject
       """
        cb = self.config.get("choppingBlock")

        if "choppingBlock" not in self.config.doc:
            return "Unable to find the config object associated. You need to add choppingBlock: {} to your config..."

        if not self.check_user_has_role(message.author, "Listener"):
            return "You are not a Listener. You cannot use this feature"

        msg = ""
        for entry in cb:
            mem = self.get_member(message, entry)
            if mem is None:
                continue
            starter = self.get_member(message, cb[entry]["started_by"])
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
