[![Python 3.7](https://img.shields.io/badge/python-3.6%20|%203.7-blue.svg?logoColor=white&logo=python&style=popout)](https://www.python.org/)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![GitHub commit activity the past week, 4 weeks, year](https://img.shields.io/github/commit-activity/y/hdmifish/petal.svg?logoColor=white&logo=github)](https://github.com/hdmifish/petal/graphs/commit-activity)
[![GitHub last commit](https://img.shields.io/github/last-commit/hdmifish/petal.svg?logoColor=white&logo=github)](https://github.com/hdmifish/petal/commit/master)

# Petal
[![Discord invite](https://img.shields.io/badge/Built%20for-Patch%20Gaming-1db2bf.svg?logoColor=white&logo=discord&style=popout-square)](https://discord.gg/patchgaming)

A friendly, practical, discord bot.

## Returning Users
I keep an expanded changelog with every commit. If you need more than the short commit message to see what was changed, that would be a good place to look.

**Warning:** includes stream of consciousness content that may confuse or annoy the reader

## Getting Started
This bot is designed for hosting on Ubuntu and has not been tested on other platforms. It is possible to get it working on Windows but some features may produce unexpected results or not work at all

##### Requirements:
- 64-bit Ubuntu/Debian
- `pip3.5 install --upgrade -r requirements.txt`
- A discord application token (register [here](https://discordapp.com/developers/applications/me))


##### If you are new to Ubuntu/Debian, but have it ready to go already:
(we are going to assume you are using ubuntu 14.04 (or Debian 7) or higher)

##### Step 1: Get everything up to date
This prevents problems later on
`sudo apt-get update && sudo apt-get upgrade -y`
##### Step 2: Install python3.5 and pip
`sudo apt-get install python3.5 python3.5-dev -y`
**Note:** To ensure python3.5 is installed, run the following:
`python3.5 --version`


##### Step 3: Download and Install pip for python 3.5+
**Note:** You may skip this if you already have pip installed. You can verify this in the usual way of just typing `pip` or `pip3.5` and seeing if the command is recognized


In your home directory `cd ~` run the following:
`sudo wget https://bootstrap.pypa.io/get-pip.py`
then run:
`sudo python3.5 get-pip.py`
finally, verify the install:
`python3.5 -m pip --version`



**Note**: If for some reason you get a __command not found__ error, replace `pip3.5` with `python3.5 -m pip`

If you still get an error after that, make sure you built pip with python3.5 or higher. Sometimes it will even run as `pip` instead of `pip3.5`


<br>



##### Step 4: Install Git and Petal:
To get this updated project and future updates, we need to link it with GitHub (which is probably where you are reading this)


Some versions of Ubuntu/Debian come with Git preinstalled. However, if yours did not, try running the following:
`sudo apt-get install git -y`

To download petal without creating a new directory:
`sudo git clone https://github.com/hdmifish/petal.git`

If you want to customize where petal will go:
1. `mkdir your_directory_name`
2. `cd your_directory_name`
3. `git clone https://github.com/hdmifish/petal.git .` (the dot is important)
4. `ls`

When you run `ls` you should see something like this:
![What it "should" look like](https://i.imgur.com/Y9wICtz.png)

##### Step 5: Install requirements

Now we need to install the other "stuff" that makes Petal work.
That can be done via:

`pip3.5 install --upgrade -r requirements.txt`

##### Step 6 (optional): Install GNU Screen:
If you dont want to have to deal with terminal windows to keep your bot open, you can run a "Screen session" to run it in the background. This is a really good way to cleanly run your bot and doesnt require you to stay logged in to your current regular session. You can even lose connection to your terminal (e.g. your SSH session gets disconnected, times out) and your screen session will still be running

To install this:
`sudo apt-get install screen`

I'll show you how to use it with this bot in a later step :)

##### Step 7: Create a discord bot application and account:
Your bot has to have an account just like you do to access discord. In order to give your bot a proper token, you need to create a bot account using [discord's handy webpage](https://discordapp.com/developers/applications/me)

1. Click *New Application*
2. Give your bot a name(this is what it will show up as in discord)
3. (You don't need a redirect URI. So if you don't know what it is, dont worry.)
4. Write a description for your bot to personalize it and give it an icon (shows up in discord as the avatar
  - **Note:** This can be changed later, but is not exactly straightforward.
6. Click *Create Application*
7. Click *Create Bot Account*

~~Add this bot to your server by following [these steps](https://github.com/jagrosh/MusicBot/wiki/Adding-Your-Bot-To-Your-Server)
(I don't know who jagrosh is, but his steps work well. So shoutout to them)~~

Discord now provides and OAuth2 URL generator built-in to the bot page.
Make sure `bot` is checked in the "scope" section and that the appropriate permissions are selected. You can always change these later with roles.


After inviting our new bot account to the server, we need to add the token to the config.yaml page (which we haven't made yet) so that Petal can run as the bot account.

**Note:** Do not share your token with others, they can control your bot and you will be responsible for anything they do with it.

##### Step 8: Edit _exampleconfig.yml
If you are on a GUI version of linux, pop open your favorite text editor and edit the _exampleconfig.yml file there.
(Otherwise, vim/nano works fine)

The config file is documented to show what information goes where. It changes often to reflect new features, but these features are optional and errors regarding missing config entries should show up pretty obviously in the bot logs.

First, copy your token in (make sure it's in single quotes).

Then, obtain your discord ID and copy it into the "Owner" block.

Finally, The rest is optional. You may add API keys to enable features and customize certain settings. More info on those will come later.

When you are finished filling out the config file to your liking perform the following:

1. `cp _exampleconfig.yml config.yml`

Congratulations, you have created a config file!

##### Step 9: Run the bot

###### If using Screen:
1. Navigate to the petal directory where *run.py* resides.
2. run `screen -dmSL petal python3.5 run.py`
3. To see your bot running, do `screen -r petal`
4. All output from the bot, including errors is logged in `screenlog.0` in the directory in which you ran step 2
5. To exit a screen session and leave the bot running do `CTRL + A` then press `d`

###### If not using Screen:
1. Navigate to the petal directory where run.py resides.
2. run python3.5 run.py
3. To stop the bot from executing, do `CTRL+C`
    **Note:** Only press CTRL+C once, as it does take a second for the bot to shutdown. If you repeatedly press it, it can wipe your config file.

To ensure the bot is working in discord. Do the ping command.
(by default this command is `>ping` but you may change the prefix)

Let me know if this installation method worked out for you alright. If not, let me know by opening up an "Issue" ticket in GitHub.

The development environment (as well as the production environment) I use is [discord.gg/patchgaming](http://discord.gg/patchgaming) for whom this bot was developed originally. This means that I will not fix errors that do not appear there without someone letting me know about the error. You can contact me on that discord (username: `isometricramen`) or via the aformentioned "issues" tab.

 **I am very open to helping people interested in Petal. Please do not hesitate to message me on discord if you need help. There are no stupid questions (usually)**
