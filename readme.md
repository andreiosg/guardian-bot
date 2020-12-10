# Discord bot 'Guardian'

Bot functionalities include:
- Music playback
- Animated bot emoji handling
- Image storage and text optical character recognition (OCR)

The problem which inspired image storage and text OCR is quick identification and resending of an already sent meme; a short, humoristic expression of ideas and viewpoints of certain individuals/groups. 


In this simplified case it would be an image commonly consisting of text + some sort of image meme template.


Animated bot emoji handling was intended as a poor man's alternative to using Discord Nitro.

## Dependencies

[Official discord.py documentation.](https://discordpy.readthedocs.io/en/latest/index.html "Discordpy docs.")


Install the modules:

`$ python3 -m pip install -U discord.py[voice] youtube_dl pandas aiosqlite pytesseract`


Install the following dependencies for discord.py[voice] (Debian based systems):

`$ sudo apt install libffi-dev libnacl-dev python3-dev`

Install the following dependency for the YTDLSource class:

`$ sudo apt install ffmpeg`

Install the following dependency for the pytesseract module:

`$ sudo apt install tesseract-ocr`

More about discord.py[voice] can be found on the [discordpy install guide](https://discordpy.readthedocs.io/en/latest/intro.html "Module install guide.").

## Creating and inviting your bot

[Link to discordpy's guide.](https://discordpy.readthedocs.io/en/latest/discord.html "Discordpy docs - invite, create.")

## Token

Each bot has a token which acts as its "key".
The file `token.txt` should consist of a single line; the bot token.


## Music playback

The following music playback commands are at the users disposal:
- `!stream url/search_query` - plays a youtube url/search query result from a stream
- `!ytd url/search_query` - plays a youtube url/search query result from a downloaded audio file, the audio file is permanently downloaded to the `media/` folder
- `!volume new_volum_integer` - sets new audio volume, valid range is 0-100
- `!join` - makes the bot join the users voice channel
- `!leave` - makes the bot leave the users voice channel
- `!skip` - skips current song
- `!pause` - pauses current song
- `!resume` - resumes current song

Music queueing was implemented through the usage of the `asyncio.Queue` and `asyncio.Event` classes.

Event loop blocking is avoided by running the blocking functions in a default loop executor. Example: `awaitable loop.run_in_executor(...)`

## Bot emoji handler

The following animated bot emoji handler commands are at the users disposal:
- `!areact emoji_name message_id` - a(nimated)react reacts with an animated emoji to the specified message id
- `!atag emoji_name user` - a(nimated)tag sends a message in the form of `author: @user animated_emoji`

## Image storage and text OCR
The following image storage and text OCR command is at the users disposal:
- `!search_meme substring` - returns all the memes containing the given substring (case insensitive)

All the images sent by the users are saved locally by the bot. Each image has its text OCRd. 

The image id (which corresponds to the filename, converted to .jpg), as well as its text are then inserted as a single row into a database table for future fetching.
