import asyncio
import discord
import youtube_dl
import re
import pandas 
import aiosqlite
import pytesseract

from discord.ext import commands
from PIL import Image

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'media/audio/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'nooverwrites': False, 'default_search': 'auto',
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
    
# acts as a namespace for the embed methods needed for the MusicPlayer
class EmbedBuilder():
    @staticmethod
    def embed_queue(bot, head, values):
        em = discord.Embed(title=head, color=0x149cdf)
        em.set_thumbnail(url=bot.user.avatar_url)

        for i, value in enumerate(values):
            em.add_field(name=str(i+1)+'.', value=value, inline=False)

        return em
        
    @staticmethod
    def embed_one(bot, head, name, value):
        em = discord.Embed(title=head, color=0x149cdf)
        em.set_thumbnail(url=bot.user.avatar_url)

        em.add_field(name=name, value=value, inline=False)

        return em


class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.songs = {}
        self.play_next = asyncio.Event()
        self.bot.loop.create_task(self.queue_task())

        self.titles = {}

        self.gid = None

    async def queue_task(self):
        # method used to play songs on multiple servers
        while True:
            self.play_next.clear()
            await self.play_next.wait()

            # queue empty, no songs playing
            if self.songs[self.gid].empty and len(self.titles[self.gid]) == 0:
                continue

            ctx, player = await self.songs[self.gid].get()
            self.title = player.title

            ctx.voice_client.play(player, after = lambda _: self.toggle_next())
            await ctx.send(embed=EmbedBuilder.embed_one(self.bot, 'Playing:', 'Song name:', player.title))
            
            
    def toggle_next(self):
        if len(self.titles[self.gid]) > 0:
            self.titles[self.gid].pop(0)
        self.bot.loop.call_soon_threadsafe(self.play_next.set)

    async def cog_before_invoke(self, ctx):
        self.gid = ctx.message.guild.id

    @commands.command(pass_context=True, aliases=['play'])
    async def stream(self, ctx, *, url):
        vc = ctx.voice_client

        if vc is None:
            return

        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)

        if vc.is_playing():
            self.titles[self.gid].append(player.title)
            await ctx.send(embed=EmbedBuilder.embed_one(self.bot, 'Queued:', 'Song name:', player.title))
        else:
            self.titles[self.gid] = [player.title]
            self.songs[self.gid] = asyncio.Queue()
            self.bot.loop.call_soon_threadsafe(self.play_next.set)

        await self.songs[self.gid].put((ctx, player))

    @commands.command()
    async def ytd(self, ctx, *, url):
        vc = ctx.voice_client

        if vc is None:
            return

        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=False)

        if vc.is_playing():
            self.titles[self.gid].append(player.title)
            await ctx.send(embed=EmbedBuilder.embed_one(self.bot, 'Queued:', 'Song name:', player.title))
        else:
            self.titles[self.gid] = [player.title]
            self.bot.loop.call_soon_threadsafe(self.play_next.set)
            self.songs[self.gid] = asyncio.Queue()


        await self.songs[self.gid].put((ctx, player))

        
    @commands.command()
    async def volume(self, ctx, volume: int):
        vc = ctx.voice_client
        if vc is None:
            return await ctx.send(embed=EmbedBuilder.embed_one(self.bot, 'User not in voice channel.', ctx.author.name, 'AA '))

        vc.source.volume = volume / 100
        await ctx.send(embed=EmbedBuilder.embed_one(self.bot, 'Volume:', 'New value:', volume))

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None: 
            return await ctx.send(embed=EmbedBuilder.embed_one(self.bot, 'User not in voice channel.', 'Please join a channel:', ctx.author.name))

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
            await ctx.send(embed=EmbedBuilder.embed_one(self.bot, 'Skipping:', 'Song name:', self.title))
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

    @commands.command(pass_context=True, aliases=['q'])
    async def queue(self, ctx):
        await ctx.send(embed=EmbedBuilder.embed_queue(self.bot, 'Queue:', self.titles[self.gid]))

class BotEmojiHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # every animated emoji contained in a single .csv file (all servers)
        self.animojis = pandas.read_csv('animated_emoji_data/animated_emojis.csv')

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

class Memester(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_file = 'meme_database/meme.db'

        self.image_types = ['png', 'jpg', 'jpeg', 'webp']

        self.src_path = 'media/src_img/'
        self.db_path = 'media/db_img/'
        self.ext = '.jpg'
        
    async def cog_before_invoke(self, ctx):
        self.gid = ctx.message.guild.id

    @commands.Cog.listener()
    async def on_ready(self):
        create_keywords = ''' CREATE TABLE IF NOT EXISTS metadata (
                              id integer PRIMARY KEY, 
                              gid integer,
                              meme_text text
                              ); 
                          '''

        conn = await aiosqlite.connect(self.db_file)
        curr = await conn.cursor()
        await curr.execute(create_keywords)
        await conn.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        self.gid = message.guild.id

        count_rows = 'SELECT COUNT(*) FROM metadata'

        conn = await aiosqlite.connect(self.db_file)
        curr = await conn.cursor()
        await curr.execute(count_rows)

        row = await curr.fetchone()
        num = row[0]

        i = 0
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in self.image_types):
                newid = num+i+1
                img_name = str(newid)
                await attachment.save(self.src_path+attachment.filename)

                loop = self.bot.loop or asyncio.get_event_loop()

                img = await loop.run_in_executor(None, lambda: Image.open(self.src_path+attachment.filename))
                rgb_img = await loop.run_in_executor(None, lambda: img.convert('RGB'))
                await loop.run_in_executor(None, lambda: rgb_img.save(self.db_path+img_name+self.ext))

                txt = await loop.run_in_executor(None, lambda: pytesseract.image_to_string(img))
                txt = txt.lower()

                task = (newid, self.gid, txt)
                insert_meta = 'INSERT INTO metadata(id, gid, meme_text) VALUES(?, ?, ?)'
                await curr.execute(insert_meta, task)
                await conn.commit()

                i += 1

        await conn.close()

    @commands.command()
    async def search_meme(self, ctx, *, keywords):
        find_memes = 'SELECT id FROM metadata WHERE meme_text LIKE ? AND gid=?'

        conn = await aiosqlite.connect(self.db_file)
        curr = await conn.cursor()
        await curr.execute(find_memes, ('%'+keywords+'%', self.gid))

        rows = await curr.fetchall()
        for row in rows:
            img_id = str(row[0])
            
            loop = self.bot.loop or asyncio.get_event_loop()

            img = await loop.run_in_executor(None, lambda: open(self.db_path+img_id+self.ext, 'rb'))
            await ctx.channel.send('', file=discord.File(img))

        await conn.close()


bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(r'------')

with open('token.txt') as f:
    token = f.read()

bot.add_cog(Memester(bot))
bot.add_cog(MusicPlayer(bot))
bot.add_cog(BotEmojiHandler(bot))
bot.run(token)
