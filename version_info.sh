#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# Petal reads this line.
VERSION=0.11.0

#(optional) what the webhook message should say.
UPDATE_TITLE="The Ephemeral Status"

# Separate bullet points with hyphens and use \n characters please.
CHANGELOG="+ Added !bytes.\n+ Readded !bugger.\n+ Technical data now cycles through Presence field.\n* Allow embeds in messages and messages in embeds.\n* Significantly optimized !quote hashing."
