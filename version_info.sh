#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# MATCH THIS TO THE VERSION IN PETAL
VERSION=0.10.0

#(optional) what the webhook message should say.
UPDATE_TITLE="Dont Quote Me On This"

# Separate bullet points with hyphens and use \n characters please.
CHANGELOG="+ Filled in default return for !info.\n+ Implemented !quote command; Mods only for right now. May go public in a future patch."
