import asyncio
import discord
import youtube_dl

from discord.ext import commands

msg_id = None

youtube_dl.utils.bug_reports_message = lambda: ''

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
    'source_address': '0.0.0.0' # ipv4, ipv6 can have issues
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

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
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.songs = asyncio.Queue()
        self.play_next = asyncio.Event()

        self.bot.loop.create_task(self.mp_task())

    async def mp_task(self):
        while True:
            self.play_next.clear()

            self.current = await self.songs.get()
            ctx, player = self.current
            ctx.voice_client.play(player, after = lambda _: self.toggle_next())
            await ctx.send(f'Now playing: {player.title}')

            await self.play_next.wait()
            
    
    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next.set)

    @commands.command()
    async def play(self, ctx, url):
        vc = ctx.voice_client

        if vc is None:
            return

        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        if vc.is_playing():
            await ctx.send(f'Queued: {player.title}')
        await self.songs.put((ctx, player))

    @commands.command()
    async def join(self, ctx):
        channel = ctx.author.voice.channel

        vc = ctx.voice_client
        if vc is not None:
            return await vc.move_to(channel)

        await channel.connect()
        
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

    @commands.command()
    async def emoji(self, ctx):
        await ctx.send('ide')

            
'''
@bot.command()
async def eggeater(ctx, msgID):
    msg = await ctx.fetch_message(msgID)
    await msg.add_reaction('<a:eggeater:780741073491722240>')
'''

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
