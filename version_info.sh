#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# MATCH THIS TO THE VERSION IN PETAL
VERSION=0.9.1

#(optional) what the webhook message should say.
UPDATE_TITLE="The Optional Update"

# Separate bullet points with hyphens and use \n characters please.
CHANGELOG="* Minor bug fixes, optimizations"
