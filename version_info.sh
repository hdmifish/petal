#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# Petal reads this line.
VERSION="1.0.1"

#(optional) what the webhook message should say.
UPDATE_TITLE="The Great Migration"

CHANGELOG=$(cat <<'EOF'
= Minor stability/usability fixes.
EOF
)
