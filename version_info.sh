#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# MATCH THIS TO THE VERSION IN PETAL
VERSION=0.9.0

#(optional) what the webhook message should say.
UPDATE_TITLE="The Optional Update"

# Separate bullet points with hyphens and use \n characters please.
CHANGELOG="+ If you misspell a command, you can now edit your message and it will run.\n+- Replaced low quality homemade option parser. Again. For the third time. We use GetOpt now.\n+ More options for define, help, xkcd, and mod commands.\n+ Finally finished !calias.\n* Contents of petal/petal.py moved into previously-empty petal/__init__.py\n* Greatly improved quote support.\n= Various fixes."
