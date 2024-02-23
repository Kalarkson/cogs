import datetime
import asyncio
import sys
import traceback
from functools import partial
import disnake
from disnake.ext import commands
from yt_dlp import YoutubeDL
import re
URL_REG = re.compile(r'https?://(?:www\.)?.+')
YOUTUBE_VIDEO_REG = re.compile(r"(https?://)?(www\.)?youtube\.(com|nl)/watch\?v=([-\w]+)")
transparent_color = disnake.Colour.from_rgb(44,45,49)


filters = {
    'nightcore': 'aresample=48000,asetrate=48000*1.25'
}


def utc_time():
    return datetime.datetime.now(datetime.timezone.utc)


YDL_OPTIONS = {
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'retries': 5,
    'extract_flat': 'in_playlist',
    'cachedir': False,
    'extractor_args': {
        'youtube': {
            'skip': [
                'hls',
                'dash'
            ],
            'player_skip': [
                'js',
                'configs',
                'webpage'
            ]
        },
        'youtubetab': ['webpage']
    }
}


FFMPEG_OPTIONS = {
    'before_options': '-nostdin'
                      ' -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}


def fix_characters(text: str):
    replaces = [
        ('&quot;', '"'),
        ('&amp;', '&'),
        ('(', '\u0028'),
        (')', '\u0029'),
        ('[', '【'),
        (']', '】'),
        ("  ", " "),
        ("*", '"'),
        ("_", ' '),
        ("{", "\u0028"),
        ("}", "\u0029"),
    ]
    for r in replaces:
        text = text.replace(r[0], r[1])
    return text


ytdl = YoutubeDL(YDL_OPTIONS)


def is_requester():
    def predicate(inter):
        player = inter.bot.players.get(inter.guild.id)
        if not player:
            return True
        if inter.author.guild_permissions.manage_channels:
            return True
        if inter.author.voice and not any(
                m for m in inter.author.voice.channel.members if not m.bot and m.guild_permissions.manage_channels):
            return True
        if player.current['requester'] == inter.author:
            return True
    return commands.check(predicate)


class YTDLSource(disnake.PCMVolumeTransformer):
    def __init__(self, source):
        super().__init__(source)
    @classmethod
    async def source(cls, url, *, ffmpeg_opts):
        return cls(disnake.FFmpegPCMAudio(url, **ffmpeg_opts))


class MusicPlayer:
    def __init__(self, inter: commands.Context):
        self.inter = inter
        self.bot = inter.bot
        self.queue = []
        self.current = None
        self.event = asyncio.Event()
        self.now_playing = None
        self.timeout_task = None
        self.channel: disnake.VoiceChannel = None
        self.disconnect_timeout = 180
        self.loop = False
        self.exiting = False
        self.nightcore = False
        self.fx = []
        self.no_message = False
        self.locked = False
        self.volume = 100
        print('Модуль {} активирован'.format(self.__class__.__name__))


    async def player_timeout(self):
        await asyncio.sleep(self.disconnect_timeout)
        self.exiting = True
        self.bot.loop.create_task(self.inter.cog.destroy_player(self.inter))


    async def process_next(self):
        self.event.clear()
        if self.locked:
            return
        if self.exiting:
            return
        try:
            self.timeout_task.cancel()
        except:
            pass
        if not self.queue:
            self.timeout_task = self.bot.loop.create_task(self.player_timeout())
            embed = disnake.Embed(
                description=f"Очередь пуста...\nБот отключиться через 3 минуты если не будет новых песен",
                color=transparent_color)
            await self.inter.channel.send(embed=embed)
            self.player_timeout()
            return
        await self.start_play()


    async def renew_url(self):
        info = self.queue.pop(0)
        self.current = info
        try:
            if info['formats']:
                return info
        except KeyError:
            pass
        try:
            url = info['webpage_url']
        except KeyError:
            url = info['url']
        to_run = partial(ytdl.extract_info, url=url, download=False)
        info = await self.bot.loop.run_in_executor(None, to_run)
        return info


    def ffmpeg_after(self, e):
        if e:
            print(f"ffmpeg error: {e}")
        self.event.set()


    async def start_play(self):
        await self.bot.wait_until_ready()
        if self.exiting:
            return
        self.event.clear()
        try:
            info = await self.renew_url()
        except Exception as e:
            traceback.print_exc()
            try:
                await self.inter.channel.send(embed=disnake.Embed(
                    description=f"**Произошла ошибка при воспроизведении песни:\n[{self.current['title']}]({self.current['webpage_url']})** ```css\n{e}\n```",
                    color=transparent_color))
            except:
                pass
            self.locked = True
            await asyncio.sleep(6)
            self.locked = False
            await self.process_next()
            return
        url = ""
        for format in info['formats']:
            if format['ext'] == 'm4a':
                url = format['url']
                break
        if not url:
            url = info['formats'][0]['url']
        ffmpg_opts = dict(FFMPEG_OPTIONS)
        self.fx = []
        if self.nightcore:
            self.fx.append(filters['nightcore'])
        if self.fx:
            ffmpg_opts['options'] += (f" -af \"" + ", ".join(self.fx) + "\"")
        try:
            if self.channel != self.inter.me.voice.channel:
                self.channel = self.inter.me.voice.channel
                await self.inter.guild.voice_client.move_to(self.channel)
        except AttributeError:
            return
        source = await YTDLSource.source(url, ffmpeg_opts=ffmpg_opts)
        source.volume = self.volume / 100
        self.inter.guild.voice_client.play(source, after=lambda e: self.ffmpeg_after(e))
        if self.no_message:
            self.no_message = False
        else:
            try:
                embed = disnake.Embed(
                    description=f"**Сейчас играет:**\n[**{info['title']}**]({info['webpage_url']})\n\n**Продолжительность:** `{datetime.timedelta(seconds=info['duration'])}`",
                    color=transparent_color,
                )
                thumb = info.get('thumbnail')
                if self.loop:
                    embed.description += " **| Повторение:** `включено`"
                if self.nightcore:
                    embed.description += " **| Повторение:** `Включено`"
                if thumb:
                    embed.set_thumbnail(url=thumb)
                self.now_playing = await self.inter.channel.send(embed=embed)
            except Exception:
                traceback.print_exc()
        await self.event.wait()
        source.cleanup()
        if self.loop:
            self.queue.insert(0, self.current)
            self.no_message = True
        self.current = None
        await self.process_next()


class music(commands.Cog):
    def __init__(self, bot):
        if not hasattr(bot, 'players'):
            bot.players = {}
        self.bot = bot


    def get_player(self, inter):
        try:
            player = inter.bot.players[inter.guild.id]
        except KeyError:
            player = MusicPlayer(inter)
            self.bot.players[inter.guild.id] = player
        return player


    async def destroy_player(self, inter):
        inter.player.exiting = True
        inter.player.loop = False
        try:
            inter.player.timeout_task.cancel()
        except:
            pass
        del self.bot.players[inter.guild.id]
        if inter.me.voice:
            await inter.guild.voice_client.disconnect()
        elif inter.guild.voice_client:
            inter.guild.voice_client.cleanup()


    async def search_yt(self, item):
        if (yt_url := YOUTUBE_VIDEO_REG.match(item)):
            item = yt_url.group()
        elif not URL_REG.match(item):
            item = f"ytsearch:{item}"
        to_run = partial(ytdl.extract_info, url=item, download=False)
        info = await self.bot.loop.run_in_executor(None, to_run)
        try:
            entries = info["entries"]
        except KeyError:
            entries = [info]
        if info["extractor_key"] == "YoutubeSearch":
            entries = entries[:1]
        tracks = []
        for t in entries:
            if not (duration := t.get('duration')):
                continue
            url = t.get('webpage_url') or t['url']
            if not URL_REG.match(url):
                url = f"https://www.youtube.com/watch?v={url}"
            tracks.append(
                {
                    'url': url,
                    'title': fix_characters(t['title']),
                    'uploader': t['uploader'],
                    'duration': duration
                }
            )
        return tracks


    @commands.slash_command()
    async def music(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @music.sub_command(name="play", description="включить музыку с ютуба.")
    async def p(
            self,
            inter: disnake.ApplicationCommandInteraction,
            query: str = commands.Param(description="Имя или ссылка на музыку.")
    ):
        if not inter.author.voice:
            embedvc = disnake.Embed(
                colour=transparent_color,
                description='Чтобы слушать музыку, сначала подключитесь к каналу голоса.'
            )
            await inter.send(embed=embedvc)
            return
        query = query.strip("<>")
        try:
            await inter.response.defer(ephemeral=False)
            songs = await self.search_yt(query)
        except Exception as e:
            return
        if not songs:
            return
        if not inter.player:
            inter.player = self.get_player(inter)
        player = inter.player
        vc_channel = inter.author.voice.channel
        print(vc_channel)
        if (size := len(songs)) > 1:
            txt = f"{size}"
        else:
            txt = f"{songs[0]['title']}"
        for song in songs:
            song['requester'] = inter.author
            player.queue.append(song)
        embed2 = disnake.Embed(
            colour=transparent_color,
            description=f"`{txt}` добавлено в очередь."
        )
        await inter.edit_original_message(embed=embed2)
        if not inter.guild.voice_client or not inter.guild.voice_client.is_connected():
            player.channel = vc_channel
            await vc_channel.connect(timeout=None, reconnect=False)
        if not inter.guild.voice_client.is_playing() or inter.guild.voice_client.is_paused():
            await player.process_next()

    @music.sub_command(name="queue", description="показывает текущие песни из очереди.")
    async def q(self, inter: disnake.ApplicationCommandInteraction):
        player = inter.player
        if not player:
            embedvc = disnake.Embed(
                colour=transparent_color,
                description='Бот неактивен')
            await inter.send(embed=embedvc)
            return
        if not player.queue:
            embed = disnake.Embed(
                colour=transparent_color,
                description='На данный момент в очереди нет песен.'
            )
            await inter.send(embed=embed)
            return
        retval = ""
        def limit(text):
            if len(text) > 30:
                return text[:28] + "..."
            return text
        for n, i in enumerate(player.queue[:20]):
            retval += f'**{n + 1} | `{datetime.timedelta(seconds=i["duration"])}` - ** [{limit(i["title"])}]({i["url"]}) | {i["requester"].mention}\n'
        if (qsize := len(player.queue)) > 20:
            retval += f"\nБолее **{qsize - 20}** треков"
        embedvc = disnake.Embed(
            colour=transparent_color,
            description=f"{retval}"
        )
        await inter.send(embed=embedvc)

    @is_requester()
    @music.sub_command(name="skip", description="пропускает текущую воспроизводимую песню.")
    async def skip(self, inter: disnake.ApplicationCommandInteraction):
        player = inter.player
        if not player:
            embed = disnake.Embed(
                colour=transparent_color,
                description='Бот неактивен')
            await inter.send(embed=embed)
            return
        if not inter.guild.voice_client or not inter.guild.voice_client.is_playing():
            embed = disnake.Embed(
                colour=transparent_color,
                description='На данный момент в очереди нет песен.'
            )
            await inter.send(embed=embed)
            return
        embed = disnake.Embed(description="**Пропущенная музыка.**", color=transparent_color)
        await inter.send(embed=embed)
        player.loop = False
        inter.guild.voice_client.stop()

    @music.sub_command(description="включить / отключить повтор текущей песни")
    async def repeat(self, inter: disnake.ApplicationCommandInteraction):
        player = inter.player
        embed = disnake.Embed(color=transparent_color)
        if not player:
            embed = disnake.Embed(
                colour=transparent_color,
                description='Бот неактивен')
            await inter.send(embed=embed)
            return
        player.loop = not player.loop
        embed.colour = transparent_color
        embed.description = f"**Повтор {'включено для текущей песни' if player.loop else 'отключен'}.**"
        await inter.send(embed=embed)

    @music.sub_command(description="включить / отключить эффект nightcore (ускоренная музыка с более высоким тоном.)")
    async def nightcore(self, inter: disnake.ApplicationCommandInteraction):
        player = inter.player
        embed = disnake.Embed(color=transparent_color)
        if not player:
            embed = disnake.Embed(
                colour=transparent_color,
                description='Бот неактивен')
            await inter.send(embed=embed)
            return
        player.nightcore = not player.nightcore
        player.queue.insert(0, player.current)
        player.no_message = True
        inter.guild.voice_client.stop()
        embed.description = f"**эффект nightcore {'включен' if player.nightcore else 'выключен'}.**"
        embed.colour = transparent_color
        await inter.send(embed=embed)

    @music.sub_command(description="остановить плеер и отключить меня от голосового канала.")
    async def stop(self, inter: disnake.ApplicationCommandInteraction):
        embed = disnake.Embed(colour=transparent_color)
        player = inter.player
        if not player:
            embed = disnake.Embed(
                colour=transparent_color,
                description='Бот неактивен')
            await inter.send(embed=embed)
            return
        if not inter.me.voice:
            embed.description = "Бот не подключен к каналу."
            await inter.send(embed=embed)
            return
        if not inter.author.voice or inter.author.voice.channel != inter.me.voice.channel:
            embed.description = "Вы должны быть на текущем голосовом канале бота, чтобы использовать эту команду."
            await inter.send(embed=embed)
            return
        if any(m for m in inter.me.voice.channel.members if
               not m.bot and m.guild_permissions.manage_channels) and not inter.author.guild_permissions.manage_channels:
            embed.description = " На данный момент вам не разрешено использовать эту команду."
            await inter.send(embed=embed)
            return
        await self.destroy_player(inter)
        embed.colour = transparent_color
        embed.description = "Вы остановили плеер"
        await inter.send(embed=embed)

    @commands.Cog.listener("on_voice_state_update")
    async def player_vc_disconnect(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if member.id != self.bot.user.id:
            return
        if after.channel:
            return
        player: MusicPlayer = self.bot.players.get(member.guild.id)
        if not player:
            return
        if player.exiting:
            return
        embed = disnake.Embed(description="**Бот выключен**", color=transparent_color)
        await player.inter.channel.send(embed=embed)
        await self.destroy_player(player.inter)

    @is_requester()
    @music.sub_command(description="изменить громкость музыки.")
    async def volume(
            self,
            inter: disnake.ApplicationCommandInteraction, *,
            value: int = commands.Param(description="от 5 до 100", min_value=5.0, max_value=100.0)
    ):
        vc = inter.guild.voice_client
        if not vc or not vc.is_connected():
            embed = disnake.Embed(
                colour=transparent_color,
                description='Бот неактивен')
            await inter.send(embed=embed)
        player = self.get_player(inter)
        if vc.source:
            vc.source.volume = value / 100
        player.volume = value / 100
        embed = disnake.Embed(description=f"**Новая громкость бота {value}%**", color=transparent_color)
        await inter.send(embed=embed)

    async def cog_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error: Exception):
        error = getattr(error, 'original', error)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        if isinstance(error, commands.CommandNotFound):
            return

    async def cog_before_slash_command_invoke(self, inter):
        inter.player = self.bot.players.get(inter.guild.id)

def setup(client):
    client.add_cog(music(client))