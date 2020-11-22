# Guardian Discord bot

Bot functionalities include:
- Music playback
- Image storage and indexing

The problem which inspired image storage and indexing is quick identification and resending of an already sent meme; a short, humoristic expression of ideas and viewpoints of certain individuals/groups. 


In this simplified case it would be an image commonly consisting of text + some sort of image meme template.

## Discord.py module setup

[Official discord.py documentation.](https://discordpy.readthedocs.io/en/latest/index.html "Discordpy docs.")


Install the module:

`$ python3 -m pip install -U discord.py[voice]`


Install the following dependencies (Debian based systems):

`$ sudo apt install libffi-dev libnacl-dev python3-dev`

More info on the [discordpy install guide](https://discordpy.readthedocs.io/en/latest/intro.html "Module install guide.").

## Creating and inviting your bot

[Link to discordpy's guide.](https://discordpy.readthedocs.io/en/latest/discord.html "Discordpy docs - invite, create.")

## Token

Each bot has a token which acts as its "key".
Replace the file `token.txt` to contain only your bot token (without the quotation marks).
