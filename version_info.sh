#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# Petal reads this line.
VERSION=0.11.4

#(optional) what the webhook message should say.
UPDATE_TITLE="The Ephemeral Status"

# Separate bullet points with hyphens and use \n characters please.
CHANGELOG="= Fixed an issue with a command not accepting conversational numbers."
