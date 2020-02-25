#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# Petal reads this line.
VERSION="1.0.0-rc5"

#(optional) what the webhook message should say.
UPDATE_TITLE="The Great Migration"

CHANGELOG=$(cat <<'EOF'
* Migrated to version 1.x of Discord Library.
* All IDs now Integers.
* Config.get() now allows "pathed" option fetching, and can be called by Subscripting.
* Servers are now called "Guilds".
* Revised Join/Part Messages.
* Wrapped periodic Coroutines in a Task that reports when they fail.
+ Added several Petal Exceptions for various situations, allowing Commands to fail explicitly.
+ Implemented Color Enumeration to facilitate standard colors in Embeds.
+ Implemented "saved" commands, allowing much greater flexibility in re-running using Exceptions.
+ Implemented module standardizing the process of waiting for user responses.
+ Implemented module standardizing creation of check predicates for passing to Discord Library.
+ Implemented new and far superior Minecraft Interface.
+ Additional Command returns: Dict, unpacked directly into send(); Embed, posted directly; Yield, iterated and sequentially appended to output before final return.
+ Added `--set` option to !osu, replacing functionality of !setosu.
+ Implemented !bytes command, for debugging the EXACT contents of a String.
+ Implemented !plane command, for forcing your problems and worries onto anyone environmentally conscious and unfortunate enough to pick up the wrong piece of abandoned paper.
+ Implemented !send command, for posting embeds to other channels.
+ Implemented Channel Tunneling with !tunnel, allowing Petal to act as a bridge between Messageables; Potential for use in future remake of !anon.
+ Implemented !userinfo command, for displaying.....user info.
+ Implemented !when command, for time zone conversions.
+ Implemented utility functions for generating Ordinals and wording numbers.
- Removed !setosu.
- Trimmed many imports.
= Fixed "issue" with !time reversing offsets relative to GMT because of the PyTZ developer not understanding how standards are meant to work.
EOF
)
