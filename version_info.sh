#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# MATCH THIS TO THE VERSION IN PETAL
VERSION=0.7.2

#(optional) what the webhook message should say.
UPDATE_TITLE=""

# Separate bullet points with hyphens and use \n characters please.
CHANGELOG="+ Return a syntax hint if it looks like the user might have tried to separate arguments with a pipe"

