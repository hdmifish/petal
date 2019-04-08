#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# MATCH THIS TO THE VERSION IN PETAL
VERSION=0.7.1

#(optional) what the webhook message should say.
UPDATE_TITLE="Preparing to Prepare"

# Separate bullet points with hyphens and use \n characters please.
CHANGELOG="* Fixed a mistake where !wlme would look for a config option as an attribute of Config, rather than going through Config.get()\n* Fixed an oversight wherein a failure to send a notification DM would not be correctly reported\n+ Added flag --nosend to !wlaccept to prevent sending DM notification"

