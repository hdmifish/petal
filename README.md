<< UPDATE 12/09. Added the welcome/role gate command. If you don't understand regex, just type in a phrase. Just note your members will have to type the message exactly>>

# Petal
A friendly, practical, discord bot.

## Getting Started
This bot is designed for hosting on Ubuntu and has not been tested on other platforms. It is possible to get it working on windows but some features may produce unexpected results

##### Requirements:
`pip3.5 install --upgrade -r requirements.txt`
- A discord application key (register [here](https://discordapp.com/developers/applications/me))

##### If you are new to linux, but have it ready to go:
(we are going to assume you are using ubuntu 14.04 or higher)

##### Step 1: Get everything up to date
This prevents problems later on
`sudo apt-get update && sudo apt-get upgrade -y`
##### Step 2: Install python3.5 and pip
`sudo apt-get install python3.5 python3.5-dev -y`
**Note:** To ensure python3.5 is installed, run the following:
`python3.5 --version`

**Note:** Some versions of python do not come with pip. To find out if yours did, run the following:
`python3.5 -m pip --version`

**If a version number is displayed, skip the next step**

##### Step 3: Download and Install pip for python 3.5+
In your home directory `cd ~` run the following:
`sudo wget https://bootstrap.pypa.io/get-pip.py`
then run:
`sudo python3.5 get-pip.py`
finally, verify the install:
`python3.5 -m pip --version`

**Note**: If for some reason you get a __command not found__ error, replace `pip3.5` with `python3.5 -m pip`
If you still get an error after that, make sure you built pip with python3.5 or higher. Sometimes it will even run as `pip` instead of `pip3.5`

##### Step 4: Install git and Petal:
To get this updated project and future updates, we need to link it with github.

Recent versions of ubuntu come shipped with git. However, if yours did not, try running the following:
`sudo apt-get install git -y`

To download petal without creating a new directory:
`sudo git clone https://github.com/hdmifish/petal.git`

If you want to customize where petal will go:
1. `mkdir <your directory name (without the <>)>`
2. `cd <your directory name(again without the <>)>`
2. `git clone https://github.com/hdmifish/petal.git .` (the dot is important)

`pip3.5 install --upgrade -r requirements.txt`
##### Step 6 (optional): Install GNU Screen:
If you dont want to have to deal with terminal windows to keep your bot open, you can run a "Screen session" to run it in the background.

To do this:
`sudo apt-get install screen`

##### Step 7: Create a discord bot application and account:
Your bot has to have an account just like you do. In order to do this, you need to create a bot account using [discord's handy webpage](https://discordapp.com/developers/applications/me)

1. Click *New Application*
2. Give your bot a name(this is what it will show up as in discord)
3. (You don't need a redirect URI if you don't know what it is)
4. Write a description for your bot to personalize it and give it an icon(shows up in discord as well)
5. (You don't need a RPC origin if you don't know what it is)
6. Click *Create Application*
7. Click *Create Bot Account*

Add this bot to your server by following [these steps](https://github.com/jagrosh/MusicBot/wiki/Adding-Your-Bot-To-Your-Server)
(I don't know who jagrosh is, but his steps work well. So shoutout to them)

After this we need to add the token to the config.yaml page in petal

**Note:** Do not share your token with others, they can control your bot and you will be responsible for anything they do with it.

##### Step 8: Edit example_config.yaml
If you are on a GUI version of linux, pop open your favorite text editor and edit the example_config.yaml file there.
(Otherwise, vim/nano works fine)
The config file is documented to show what information goes where.

First, copy your token in (make sure it's in single quotes).

Then, obtain your discord ID and copy it into the "Owner" block.

Finally, The rest is optional. You may add API keys to enable features and customize certain settings. More info on those will come later.

##### Step 9: Run the bot

###### If using Screen:
1. Navigate to the petal directory where *run.py* resides.
2. run `screen -dmSL petal python3.5 run.py`
3. To see your bot running, do `screen -r petal`
4. All output from the bot, including errors is logged in `screenlog.0`
5. To exit a screen session and leave the bot running do `CTRL+ A` then press `d`

###### If not using Screen:
1. Navigate to the petal directory where run.py resides.
2. run python3.5 run.py
3. To stop the bot from executing, do `CTRL+C`
    **Note:** Only press CTRL+C once, as it does take a second for the bot to shutdown. If you repeatedly press it, it can wipe your config file.

To ensure the bot is working in discord. Do the ping command.
(by default this command is `>ping` but you may change the prefix)

Let me know if this installation method worked out for you alright. If not, let me know by opening up an "Issue" ticket in github.
