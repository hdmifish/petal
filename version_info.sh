#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# Petal reads this line.
VERSION="1.1.0"

#(optional) what the webhook message should say.
UPDATE_TITLE="Scholar of the First STDIN"

CHANGELOG=$(cat <<'EOF'
+ Added !souls command, for randomly generating Messages from the Dark Souls series.
EOF
)
