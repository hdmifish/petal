#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# MATCH THIS TO THE VERSION IN PETAL
VERSION=0.5.7 

#(optional) what the webhook message should say. 
UPDATE_TITLE="THE META UPDATE"

# Separate bullet points with hyphens and use \n characters please. 
CHANGELOG="-Enabled webhook support for deployments\n-Added indentation"

