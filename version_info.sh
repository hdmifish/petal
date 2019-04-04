#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# MATCH THIS TO THE VERSION IN PETAL
VERSION=0.7.0

#(optional) what the webhook message should say.
UPDATE_TITLE="Preparing to Prepare"

# Separate bullet points with hyphens and use \n characters please.
CHANGELOG="A primarily administrative update, and maybe some features\n+ Filled out changelog.txt\n\* Changed !statsfornerds to !stats\n\* Changed !list_connected_servers to !servers\n+ Added !define command"

