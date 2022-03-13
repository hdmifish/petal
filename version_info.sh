#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# Petal reads this line.
VERSION="1.1.4"

#(optional) what the webhook message should say.
UPDATE_TITLE="Shove this Data into your Base"

CHANGELOG=$(cat <<'EOF'
More fun changes and bug fixes
EOF
)
