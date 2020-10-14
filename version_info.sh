#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# Petal reads this line.
VERSION="1.1.3"

#(optional) what the webhook message should say.
UPDATE_TITLE="Shove this Data into your Base"

CHANGELOG=$(cat <<'EOF'
* DSMSG Command now supports Options.
= Fixed problems with OSU Command.
= Fixed some potential issues with Minecraft names.
= Revised Animal Crossing Mode to better handle Codeblocks.
EOF
)
