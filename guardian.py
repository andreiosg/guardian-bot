import asyncio
import discord
import youtube_dl
import re
import pandas 

from discord.ext import commands

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'media/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'nooverwrites': False,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # ipv4, ipv6 can have issues
}

# Based on the streaming option (True, False)
# True ffmpeg options meant to fix streaming read error invalidation
# False is for a downloaded audio file
ffmpeg_options = {
    True: {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'},
    False: {
        'options': '-vn'}
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# download/streamable audio source
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist (youtube), not to confuse with queue_task
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options[stream]), data=data)


class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.songs = asyncio.Queue()
        self.play_next = asyncio.Event()

        self.bot.loop.create_task(self.queue_task())

    async def queue_task(self):
        while True:
            self.play_next.clear()

            ctx, player = await self.songs.get()
            ctx.voice_client.play(player, after = lambda _: self.toggle_next())
            await ctx.send(f'Playing: {player.title}')
            
            await self.play_next.wait()
            
    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next.set)

    @commands.command()
    async def stream(self, ctx, *, url):
        vc = ctx.voice_client

        if vc is None:
            return

        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        if vc.is_playing():
            await ctx.send(f'Queued: {player.title}')
        await self.songs.put((ctx, player))

    @commands.command()
    async def ytd(self, ctx, *, url):
        vc = ctx.voice_client

        if vc is None:
            return

        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=False)
        if vc.is_playing():
            await ctx.send(f'Queued: {player.title}')
        await self.songs.put((ctx, player))
        
    @commands.command()
    async def volume(self, ctx, volume: int):
        vc = ctx.voice_client
        if vc is None:
            return await ctx.send('Not in a voice channel.')

        vc.source.volume = volume / 100
        await ctx.send(f'Set volume to {volume}')

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None: 
            return await ctx.send('User not in a voice channel.')

        vc = ctx.voice_client
        if vc is not None:
            return await vc.move_to(ctx.author.voice.channel)

        await ctx.author.voice.channel.connect()
        
    @commands.command()
    async def leave(self, ctx):
        vc = ctx.voice_client
        if vc is not None:
            await vc.disconnect()

    @commands.command()
    async def skip(self, ctx):
        vc = ctx.voice_client
        if vc is not None and vc.is_playing():
            vc.stop()

    @commands.command()
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc is not None and vc.is_playing():
            vc.pause()

    @commands.command()
    async def resume(self, ctx):
        vc = ctx.voice_client
        if vc is not None and vc.is_paused():
            vc.resume()


class BotEmojiHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.animojis = pandas.read_csv('data/animated-emojis.csv')

    def build_emoji(self, emoji_name):
        idx = self.animojis[self.animojis['name']==emoji_name].index.item() 
        emojiID = self.animojis.at[idx, 'emojiID']
        return f'<a:{emoji_name}:{emojiID}>'

    @commands.command()
    async def areact(self, ctx, emoji_name, msg_id):
        msg = await ctx.fetch_message(msg_id)
        emoji = self.build_emoji(emoji_name)
        await msg.add_reaction(emoji)

    @commands.command()
    async def atag(self, ctx, emoji_name, user: discord.Member = None):
        # author name without id
        author = re.search('^(.*)#[0-9]{4}', str(ctx.message.author)).group(1)
        emoji = self.build_emoji(emoji_name)
        await ctx.send(f'{author}: {user.mention} {emoji}')

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(r'------')

with open('token.txt') as f:
    token = f.read()

bot.add_cog(MusicPlayer(bot))
bot.add_cog(BotEmojiHandler(bot))
bot.run(token)


