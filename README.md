<< UPDATE 12/09. Added the welcome/role gate command. If you don't understand regex, just type in a phrase. Just note your members will have to type the message exactly>>

# Petal
A simple, customizable, discord bot written in python.

## Getting Started
Small note, I am working on an installer for both windows and ubuntu as well as raspbian.

##### Windows Installer:
Go ahead and download [petal installer](https://raw.githubusercontent.com/hdmifish/petal/master/petal-installer.ps1) 
Just do CTRL+S and save it in your user directory i.e. `C:\Users\(your username)`
Now launch Powershell as Administrator
Note: By Default, windows locks down running powershell scripts. However, for one time use, run the following command:
`Set-ExecutionPolicy RemoteSigned` 
Then press `Y`
Finally, do ./petal-installer.ps1 in powershell and follow the instructions. 

For the Git install: 
Follow the windows options, use CMD not MinTTY and add git to command line. 



If you would like to offer suggestions or have questions, feel free to make an issue.
##### Scroll down if you are new to linux
(read this section if you know what you're doing)
##### Requirements:
- [discord.py (no voice support required)](https://github.com/Rapptz/discord.py)
- git (sudo git clone https://github.com/hdmifish/petal.git)
- [colorama](https://pypi.python.org/pypi/colorama)
- [requests](https://pypi.python.org/pypi/requests/)
- [cleverbot](https://pypi.python.org/pypi/cleverbot)
- [PRAW(for reddit)](https://pypi.python.org/pypi/praw)
- [ruamel.yaml](https://pypi.python.org/pypi/ruamel.yaml)
- [python-magic(not to be confused with the apt-get version)](https://pypi.python.org/pypi/python-magic)
- A discord application key (register [here](https://discordapp.com/developers/applications/me))

##### If you are new to linux, but have it ready to go:
(we are going to assume you are using ubuntu 14.04+ Further support coming later)

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

##### Step 3: Download and Install pip3.5
In your home directory `cd ~` run the following:
`sudo wget https://bootstrap.pypa.io/get-pip.py`
then run:
`sudo python3.5 get-pip.py`
finally, verify the install:
`python3.5 -m pip --version`

##### Step 4: Install discord.py and Petal requirements:

Petal needs to be able to communicate with discord. Therefore, we need the API wrapper from [Rapptz](https://github.com/Rapptz/discord.py).

Copy and run this long command:
`sudo -H pip3.5 install -U discord.py cleverbot colorama requests python-magic ruamel.yaml praw`

**Note**: If for some reason you get a __command not found__ error, replace `pip3.5` with `python3.5 -m pip`

##### Step 5: Install git and Petal:
To get this updated project and future updates, we need to link it with github.

Recent versions of ubuntu come shipped with git. However, if yours did not, try running the following:
`sudo apt-get install git -y`

To download petal without creating a new directory:
`sudo git clone https://github.com/hdmifish/petal.git`

If you want to customize where petal will go:
1. `mkdir <your directory name (without the <>)>`
2. `cd <your directory name(again without the <>)>`
2. `git clone https://github.com/hdmifish/petal.git .` (the dot is important)

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

After this we need to add the token to the config.yaml page in petal

**Note:** Do not share your token with others, they can controll your bot and you will be responsible for anything they do with it.

##### Step 8: Edit config.yaml
If you are on a GUI version of linux, pop open your favorite text editor and edit the config.yaml file there.
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
