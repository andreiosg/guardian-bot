import youtube_dl

import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!')

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # ipv4, ipv6 causes issues
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel
    if channel is not None:
        return await channel.connect()

    
@bot.command()
async def leave(ctx):
    vc = ctx.voice_client
    if vc is not None:
        await ctx.voice_client.disconnect()


with open('token.txt') as f:
    token = f.read()

bot.run(token)
