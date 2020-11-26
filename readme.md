# Discord bot 'Guardian'

Bot functionalities include:
- Music playback
- Image storage and indexing

The problem which inspired image storage and indexing is quick identification and resending of an already sent meme; a short, humoristic expression of ideas and viewpoints of certain individuals/groups. 


In this simplified case it would be an image commonly consisting of text + some sort of image meme template.

## Modules

[Official discord.py documentation.](https://discordpy.readthedocs.io/en/latest/index.html "Discordpy docs.")


Install the modules:

`$ python3 -m pip install -U discord.py[voice] youtube_dl pandas`


Install the following dependencies for discord.py[voice] (Debian based systems):

`$ sudo apt install libffi-dev libnacl-dev python3-dev`

Install the following dependency for the YTDLSource class:

`$ sudo apt install ffmpeg`

More info on the [discordpy install guide](https://discordpy.readthedocs.io/en/latest/intro.html "Module install guide.").

## Creating and inviting your bot

[Link to discordpy's guide.](https://discordpy.readthedocs.io/en/latest/discord.html "Discordpy docs - invite, create.")

## Token

Each bot has a token which acts as its "key".
Replace the file `token.txt` to contain only your bot token (without the quotation marks).


## Music playback

The following music playback commands are at the users disposal:
- `!stream url/search_query` - plays a youtube url/search query result from a stream
- `!ytd url/search_query` - plays a youtube url/search query result from a downloaded audio file, the audio file is permanently downloaded to the `media/` folder
- `!join` - makes the bot join the users voice channel
- `!leave` - makes the bot leave the users voice channel
- `!skip` - skips current song
- `!pause` - pauses current song
- `!resume` - resumes current song

