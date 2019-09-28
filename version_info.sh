#!/bin/bash
# Used in  post-merge hook for deployment on patchgaming. You can use this for your own server if you want.
# Not necessarily the prettiest but easy to work with.

# Petal reads this line.
VERSION="1.0.0-rc0"

#(optional) what the webhook message should say.
UPDATE_TITLE="The Great Migration"


# Separate bullet points with hyphens and use \n characters please.
# ESCAPE QUOTES, THIS IS BASH
CHANGELOG='* Migrated to version 1.x of Discord Library.\n* All IDs now Integers.\n* Config.get() now allows \"pathed\" option fetching.\n* Servers are now called \"Guilds\".\n+ Added several Petal Exceptions for various situations, allowing Commands to fail explicitly.\n+ Implemented \"saved\" commands, allowing much greater flexibility in re-running using Exceptions.\n+ Implemented module standardizing the process of waiting for user responses.\n+ Implemented module standardizing creation of check predicates for passing to Discord Library.\n+ Additional Command returns: Dict, unpacked directly into send(); Embed, posted directly; Yield, iterated and sequentially appended to output before final return.\n+ Added `--set` option to !osu, replacing functionality of !setosu.\n+ Implemented !plane command, for forcing your problems and worries onto anyone environmentally conscious and unfortunate enough to pick up the wrong piece of abandoned paper.\n+ Implemented !send command, for posting embeds to other channels.\n+ Implemented Channel Tunneling with !tunnel, allowing Petal to act as a bridge between Messageables; Potential for use in future remake of !anon.\n+ Implemented !when command, for time zone conversions.\n+ Implemented utility functions for generating Ordinals and wording numbers.\n- Removed !setosu.\n- Trimmed many imports.\n= Fixed \"issue\" with !time reversing offsets relative to GMT because of the PyTZ developer not understanding how standards are meant to work.'
