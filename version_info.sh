#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# MATCH THIS TO THE VERSION IN PETAL
VERSION=0.8.0

#(optional) what the webhook message should say.
UPDATE_TITLE="Mod Tools Revamp: Chapter 1"

# Separate bullet points with hyphens and use \n characters please.
CHANGELOG="+ Return a syntax hint if it looks like the user might have tried to separate arguments with a pipe\n+ Allow most role restricted commands to be used in DM by falling back to mainserver roles\n+ Integrate command options with moderation commands\n+ Reimplement mod report URIs\n* Dashed numbers are no longer interpreted as command options; Apparently negative numbers exist\n* Correct CommandsMod to CommandsMgr in manager command module\n* Improve type printing"
