import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os
import shutil
from dotenv import load_dotenv
import time

load_dotenv()

TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

if not TOKEN:
    print("Lỗi: Chưa thiết lập biến môi trường DISCORD_BOT_TOKEN trong file .env trong file .env")
    exit()

bot = commands.Bot(command_prefix='miku!', intents=discord.Intents.all(), help_command=None)

CACHE_DIR = './cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': f'{CACHE_DIR}/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch5',
    'source_address': '0.0.0.0',
    'cachedir': False,
    'rm-cache-dir': False,
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class Song:
    def __init__(self, source, title, url, requester, cached_file):
        self.source = source
        self.title = title
        self.url = url
        self.requester = requester
        self.cached_file = cached_file

    @classmethod
    async def from_url(cls, url, requester, loop=None):
        loop = loop or bot.loop
        start_time = time.time()
        cached_file = None
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))
        except Exception as e:
            print(f"LỖI yt-dlp from_url: Không thể tải thông tin từ URL {url} - {e}")
            return None

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url']
        title = data.get('title') or "Unknown Title"
        cached_file = ytdl.prepare_filename(data)

        song_obj = cls(discord.FFmpegPCMAudio(cached_file, **ffmpeg_options), title, url, requester, cached_file)
        end_time = time.time()
        print(f"from_url: Thời gian xử lý Song.from_url cho URL {url}: {end_time - start_time:.4f} giây, File cache: {cached_file}")
        return song_obj

    @classmethod
    async def from_query(cls, query, requester, source_type='youtube', loop=None):
        loop = loop or bot.loop
        print(f"Bắt đầu tìm kiếm {source_type} với query: {query}")
        start_time_query = time.time()
        songs = []
        if source_type == 'youtube':
            try:
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch5:{query}", download=False))
                if data is None:
                    print(f"LỖI yt-dlp from_query (youtube): yt-dlp trả về None cho query '{query}'")
                    return None, None
            except Exception as e:
                print(f"LỖI yt-dlp from_query (youtube): Lỗi tìm kiếm YouTube với query '{query}' - {e}")
                return None, None
            entries = data.get('entries', [])
            if not entries:
                print(f"LỖI yt-dlp from_query (youtube): Không tìm thấy kết quả cho query '{query}'")
                return None, None

            for entry in entries:
                url = entry.get('webpage_url')
                title = entry.get('title') or "Unknown Title"
                songs.append({'title': title, 'url': url})
        else:
            print(f"LỖI from_query: source_type không hợp lệ: '{source_type}'")
            return None, None

        end_time_query = time.time()
        print(f"from_query: Thời gian tìm kiếm {source_type} cho query '{query}': {end_time_query - start_time_query:.4f} giây, Tìm thấy {len(songs)} kết quả")
        return songs, source_type


class MusicQueue:
    def __init__(self):
        self.queue = []

    def add(self, song):
        self.queue.append(song)

    def get_next_song(self):
        if self.queue:
            return self.queue[0]
        else:
            return None

    def pop_song(self):
        if self.queue:
            return self.queue.pop(0)
        return None

    def peek_queue(self, start_index=0, items_per_page=5):
        if not self.queue:
            return [], 0, 0
        total_items = len(self.queue)
        start_index = max(0, min(start_index, total_items - 1))
        end_index = min(start_index + items_per_page, total_items)
        page_queue = self.queue[start_index:end_index]
        return page_queue, start_index, total_items

    def remove_song(self, index):
        if 1 <= index <= len(self.queue):
            removed_song = self.queue.pop(index - 1)
            return removed_song
        return None

    def clear_queue(self):
        self.queue = []

    def is_empty(self):
        return not self.queue


class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.music_queues = {}

    def get_voice_client(self, guild):
        return self.voice_clients.get(guild.id)

    def get_music_queue(self, guild):
        if guild.id not in self.music_queues:
            self.music_queues[guild.id] = MusicQueue()
        return self.music_queues[guild.id]

    async def play_song(self, ctx, song):
        print("Bắt đầu play_song")
        guild_id = ctx.guild.id
        voice_client = self.get_voice_client(ctx.guild)
        music_queue = self.get_music_queue(ctx.guild)

        if voice_client is None:
            voice_channel = ctx.author.voice.channel
            if voice_channel is None:
                await ctx.send("Bạn cần phải ở trong kênh thoại để dùng lệnh này.")
                print("play_song: Người dùng không ở trong kênh thoại")
                return False
            try:
                voice_client = await voice_channel.connect(timeout=10.0, reconnect=True)
                self.voice_clients[guild_id] = voice_client
                print(f"play_song: Đã kết nối tới kênh thoại: {voice_channel.name}")
            except discord.errors.ClientException as e:
                print(f"LỖI voice_client connect (play_song): ClientException - {e}")
                await ctx.send("Bot đã kết nối tới kênh thoại ở server này rồi.")
                return False
            except asyncio.TimeoutError as e:
                print(f"LỖI voice_client connect (play_song): TimeoutError - {e}")
                await ctx.send("Kết nối kênh thoại bị quá thời gian chờ. Vui lòng kiểm tra kết nối mạng hoặc thử lại sau.")
                return False
            except Exception as e:
                print(f"LỖI voice_client connect (play_song): Lỗi không xác định - {e}")
                await ctx.send("Có lỗi xảy ra khi kết nối kênh thoại. Vui lòng thử lại sau.")
                return False

        if song.source is None:
            await ctx.send("Không thể phát bài hát này.")
            print("play_song: song.source is None")
            return False

        try:
            voice_client.play(song.source, after=lambda e: self.after_song(ctx, song, e))
            await ctx.send(f"🎶 Đang phát: **{song.title}** (Yêu cầu bởi {song.requester.mention})")
            print(f"play_song: Đang phát bài hát: {song.title}")
            return True
        except Exception as e:
            print(f"Lỗi khi phát nhạc trong play_song: {e}")
            await ctx.send("Có lỗi xảy ra khi phát bài hát. Vui lòng thử lại sau.")
            return False

    def after_song(self, ctx, song, error=None):
        print("Bắt đầu after_song")
        if error:
            print(f"Lỗi khi phát nhạc: {error}")

        music_queue = self.get_music_queue(ctx.guild)

        if song and song.cached_file and os.path.exists(song.cached_file):
            print(f"after_song: Xóa file cache: {song.cached_file}")
            try:
                os.remove(song.cached_file)
            except Exception as e:
                print(f"LỖI after_song: Không thể xóa file cache {song.cached_file}: {e}")

        music_queue.pop_song()

        next_song = music_queue.get_next_song()
        if next_song:
            print("after_song: Phát bài tiếp theo - Tên bài:", next_song.title)
            coroutine = self.play_song(ctx, next_song)
            bot.loop.create_task(coroutine)
            print("after_song: Đã scheduled play_song task")
        else:
            print("after_song: Hết hàng đợi, dừng nhạc")
            bot.loop.create_task(self.leave_after_delay(ctx))

    async def leave_after_delay(self, ctx):
        voice_client = self.get_voice_client(ctx.guild)
        if voice_client and not self.get_music_queue(ctx.guild).queue:
            await self.send_queue_finished_embed(ctx)
            await asyncio.sleep(905)
            await self.disconnect_voice_client(ctx.guild)
            await self.send_leave_embed(ctx)

    async def send_queue_finished_embed(self, ctx):
        embed = discord.Embed(title="😴 Đã phát hết hàng đợi", color=discord.Color.gold())
        await ctx.send(embed=embed)

    async def send_leave_embed(self, ctx):
        embed = discord.Embed(title="👋 Đã rời kênh thoại do không hoạt động", color=discord.Color.red())
        await ctx.send(embed=embed)

    async def disconnect_voice_client(self, guild):
        voice_client = self.get_voice_client(guild)
        if voice_client:
            try:
                await voice_client.disconnect()
            except Exception as e:
                print(f"Lỗi ngắt kết nối: {e}")

            if guild.id in self.voice_clients:
                del self.voice_clients[guild.id]

            print("stop_music: Xóa thư mục cache:", CACHE_DIR)
            try:
                shutil.rmtree(CACHE_DIR)
                os.makedirs(CACHE_DIR)
                print("stop_music: Đã xóa thư mục cache thành công")
            except Exception as e:
                print(f"LỖI stop_music: Lỗi khi xóa thư mục cache {CACHE_DIR}: {e}")

    async def display_search_results(self, ctx, search_results, source_type, page=1, songs_per_page=5, embed_message=None, selection_message=None):
        print("display_search_results function called")
        if not search_results:
            print("No search results in display_search_results")
            await ctx.send("Không tìm thấy bài hát nào.")
            return

        start_index = (page - 1) * songs_per_page
        end_index = min(start_index + songs_per_page, len(search_results))
        current_page_songs = search_results[start_index:end_index]

        embed = discord.Embed(title=f"Kết quả tìm kiếm từ {source_type.capitalize()} (Trang {page})", color=discord.Color.blue())
        description = ""
        for i, song_info in enumerate(current_page_songs):
            description += f"{start_index + i + 1}. [{song_info['title']}]({song_info['url']})\n"
        embed.description = description
        embed.set_footer(text=f"Trang {page}/{((len(search_results) - 1) // songs_per_page) + 1}")

        if embed_message:
            print("Editing existing embed message")
            await embed_message.edit(embed=embed)
        else:
            print("Sending new embed message")
            embed_message = await ctx.send(embed=embed)

        if selection_message:
            await selection_message.delete()

        if len(search_results) > songs_per_page:
            if page > 1:
                await embed_message.add_reaction("⬅️")
            if end_index < len(search_results):
                await embed_message.add_reaction("➡️")

        selection_message = await ctx.send("Chọn số bài hát bạn muốn thêm vào hàng đợi (hoặc cancel để hủy):")

        def check_reaction(reaction, user):
            return user == ctx.author and reaction.message.id == embed_message.id and str(reaction.emoji) in ["⬅️", "➡️"]

        def check_selection(message):
            if message.author == ctx.author and message.channel == ctx.channel:
                if message.content.lower() == 'cancel':
                    return True
                try:
                    selection = int(message.content)
                    return 1 <= selection <= len(search_results)
                except ValueError:
                    return False
            return False

        try:
            reaction_task = asyncio.create_task(bot.wait_for('reaction_add', check=check_reaction, timeout=60.0))
            message_task = asyncio.create_task(bot.wait_for('message', check=check_selection, timeout=60.0))
      
            done, pending = await asyncio.wait(
                [reaction_task, message_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

            if done:
                future = done.pop()
                try:
                    result = future.result()
                    if isinstance(result, tuple):
                        reaction, user = result
                        if str(reaction.emoji) == "⬅️":
                            new_page = max(1, page - 1)
                            await embed_message.clear_reactions()
                            await selection_message.delete()
                            await self.display_search_results(ctx, search_results, source_type, new_page, songs_per_page, embed_message)
                        elif str(reaction.emoji) == "➡️":
                            new_page = min(page + 1, ((len(search_results) - 1) // songs_per_page) + 1)
                            await embed_message.clear_reactions()
                            await selection_message.delete()
                            await self.display_search_results(ctx, search_results, source_type, new_page, songs_per_page, embed_message)
                    else:
                        message = result
                        if message.content.lower() == 'cancel':
                            await ctx.send("Đã hủy tìm kiếm.")
                        else:
                            try:
                                selection = int(message.content)
                                selected_song_info = search_results[selection - 1]
                                song_url = selected_song_info['url']
                                song_title = selected_song_info['title']
                                start_time_song_from_url = time.time()
                                song = await Song.from_url(song_url, ctx.author, loop=bot.loop)
                                end_time_song_from_url = time.time()
                                print(f"display_search_results: Thời gian Song.from_url: {end_time_song_from_url - start_time_song_from_url:.4f} giây")
                                if song:
                                    music_queue = self.get_music_queue(ctx.guild)
                                    start_time_queue_add = time.time()
                                    music_queue.add(song)
                                    end_time_queue_add = time.time()
                                    print(f"display_search_results: Thời gian queue.add: {end_time_queue_add - start_time_queue_add:.4f} giây")
                                    await ctx.send(f"✅ Đã thêm **{song.title}** vào hàng đợi.")

                                    voice_client = ctx.voice_client
                                    if voice_client is None:
                                        voice_channel = ctx.author.voice.channel
                                        if voice_channel:
                                            try:
                                                voice_client = await voice_channel.connect(timeout=10.0, reconnect=True)
                                                self.voice_clients[ctx.guild.id] = voice_client
                                                print(f"Bot tự động tham gia kênh thoại: {voice_channel.name}")
                                            except Exception as e:
                                                print(f"LỖI tự động join kênh thoại: {e}")
                                        else:
                                            print("Người dùng không ở trong kênh thoại, không tự động join.")

                                    if not ctx.voice_client or not ctx.voice_client.is_playing():
                                        next_song = music_queue.get_next_song()
                                        if next_song:
                                            await self.play_song(ctx, next_song)
                                else:
                                    await ctx.send("Không thể tải bài hát này. Vui lòng thử lại sau.")

                            except ValueError:
                                await ctx.send("Lựa chọn không hợp lệ. Vui lòng nhập số từ danh sách.")
                            except Exception as e:
                                print(f"Lỗi không xác định khi chọn bài hát: {e}")
                                await ctx.send("Có lỗi xảy ra khi chọn bài hát. Vui lòng thử lại sau.")

                        await message.delete()
                        await selection_message.delete()
                except asyncio.TimeoutError:
                    await ctx.send("Hết thời gian chờ chọn bài hát.")
                    await embed_message.clear_reactions()
                    await selection_message.delete()
                except Exception as e:
                    print(f"Lỗi trong quá trình xử lý kết quả: {e}")
                    await ctx.send("Có lỗi xảy ra. Vui lòng thử lại sau.")
            else:
                await ctx.send("Hết thời gian chờ chọn bài hát.")
                await embed_message.clear_reactions()
                await selection_message.delete()

        except asyncio.TimeoutError:
            await ctx.send("Hết thời gian chờ chọn bài hát.")
            await embed_message.clear_reactions()
            await selection_message.delete()
        except Exception as e:
            print(f"Lỗi lớn trong display_search_results: {e}")
            await ctx.send("Đã xảy ra lỗi không mong muốn. Vui lòng thử lại sau.")
        print("display_search_results function finished")

    @commands.command(name='play', aliases=['p', 'phat'])
    async def play_command(self, ctx, *, query: str):
        if ctx.author.voice is None:
            return await ctx.send("Bạn cần phải ở trong kênh thoại để dùng lệnh này.")

        voice_client = self.get_voice_client(ctx.guild)
        if voice_client is None:
            voice_channel = ctx.author.voice.channel
            if voice_channel is None:
                return await ctx.send("Bạn không ở trong kênh thoại nào.")

        async with ctx.typing():
            start_time_play_youtube = time.time()
            if query.startswith(('http://', 'https://', 'www.youtube.com', 'm.youtube.com', 'youtu.be', 'youtube.com', 'youtu.be')):
                try:
                    start_time_song_from_url_py = time.time()
                    song = await Song.from_url(query, ctx.author, loop=bot.loop)
                    end_time_song_from_url_py = time.time()
                    print(f"play_youtube: Thời gian Song.from_url (link): {end_time_song_from_url_py - start_time_song_from_url_py:.4f} giây")
                    if song:
                        music_queue = self.get_music_queue(ctx.guild)
                        start_time_queue_add_py = time.time()
                        music_queue.add(song)
                        end_time_queue_add_py = time.time()
                        print(f"play_youtube: Thời gian queue.add (link): {end_time_queue_add_py - start_time_queue_add_py:.4f} giây")
                        await ctx.send(f"✅ Đã thêm **{song.title}** vào hàng đợi.")
                        if not voice_client or not voice_client.is_playing():
                            next_song = music_queue.get_next_song()
                            if next_song:
                                await self.play_song(ctx, next_song)
                    else:
                        await ctx.send("Không thể tải bài hát từ URL YouTube này. Vui lòng thử lại sau.")
                except Exception as e:
                    print(f"LỖI play_youtube: Lỗi khi tải bài hát từ URL YouTube: {e}")
                    await ctx.send("Lỗi khi tải bài hát từ URL YouTube. Vui lòng thử lại sau.")
            else:
                print(f"Bắt đầu xử lý lệnh play với query: {query}")
                start_time_from_query_py = time.time()
                search_results, source_type = await Song.from_query(query, ctx.author, 'youtube', loop=bot.loop)
                end_time_from_query_py = time.time()
                print(f"play_youtube: Thời gian Song.from_query (query): {end_time_from_query_py - start_time_from_query_py:.4f} giây")
                if search_results:
                    if not search_results:
                        print(f"LỖI play_youtube: Song.from_query trả về search_results rỗng cho query: {query}")
                        return await ctx.send("Không tìm thấy bài hát nào trên Youtube.")
                    await self.display_search_results(ctx, search_results, source_type)
                else:
                    print(f"LỖI play_youtube: Song.from_query trả về None cho query: {query}")
                    await ctx.send("Không tìm thấy bài hát nào trên Youtube.")
            end_time_play_youtube = time.time()
            print(f"play_youtube: Tổng thời gian xử lý lệnh play: {end_time_play_youtube - start_time_play_youtube:.4f} giây")

    @commands.command(name='skip', aliases=['sk', 'boqua'])
    async def skip_command(self, ctx):
        voice_client = self.get_voice_client(ctx.guild)
        if voice_client is not None and voice_client.is_playing():
            print("skip_song: Đang dừng phát nhạc hiện tại")
            voice_client.stop()
            await ctx.send("⏭️ Đã bỏ qua bài hát hiện tại.")
            print("skip_song: Đã gửi thông báo skip")
        else:
            print("skip_song: Không có bài hát nào đang phát để skip")
            await ctx.send("Không có bài hát nào đang phát để bỏ qua.")

    @commands.command(name='stop', aliases=['st', 'dung'])
    async def stop_command(self, ctx):
        voice_client = self.get_voice_client(ctx.guild)
        if voice_client:
            music_queue = self.get_music_queue(ctx.guild)
            music_queue.clear_queue()
            voice_client.stop()
            await self.disconnect_voice_client(ctx.guild)
            await ctx.send("👋 Đã dừng phát nhạc và rời kênh thoại.")
        else:
            await ctx.send("Bot không ở trong kênh thoại.")

    @commands.command(name='queue', aliases=['q', 'list'])
    async def queue_command(self, ctx, page: int = 1):
        await self.show_queue(ctx, page)

    async def show_queue(self, ctx, page=1):
        music_queue = self.get_music_queue(ctx.guild)
        if music_queue.is_empty():
            return await ctx.send("Hàng đợi hiện đang trống.")

        items_per_page = 10
        queue_list, start_index, total_items = music_queue.peek_queue((page - 1) * items_per_page, items_per_page)
        if not queue_list:
            return await ctx.send(f"Không có trang {page} trong hàng đợi.")

        embed = discord.Embed(title=f"🎶 Hàng đợi bài hát (Trang {page}/{((total_items - 1) // items_per_page) + 1})", color=discord.Color.blue())
        description = ""
        for i, song in enumerate(queue_list):
            description += f"{start_index + i + 1}. [{song.title}]({song.url}) - Yêu cầu bởi {song.requester.mention}\n"
        embed.description = description
        embed.set_footer(text=f"{total_items} bài hát trong hàng đợi.")
        await ctx.send(embed=embed)

    @commands.command(name='help', aliases=['h', 'trogiup'])
    async def miku_help_command(self, ctx):
        embed = discord.Embed(title="🎵 Lệnh Bot Nhạc Miku", color=discord.Color.blue())
        embed.add_field(name="miku!play <tên bài hát YouTube hoặc link YouTube>", value="Phát nhạc từ Youtube.", inline=False)
        embed.add_field(name="miku!skip", value="Bỏ qua bài hát hiện tại.", inline=False)
        embed.add_field(name="miku!stop", value="Dừng phát nhạc và rời kênh thoại.", inline=False)
        embed.add_field(name="miku!queue [trang]", value="Hiển thị hàng đợi bài hát (mặc định trang 1).", inline=False)
        embed.add_field(name="miku!nowplaying hoặc miku!np", value="Hiển thị bài hát đang phát.", inline=False)
        embed.add_field(name="miku!help", value="Hiển thị trợ giúp.", inline=False)
        embed.add_field(name="miku!join", value="Tham gia kênh thoại bạn đang ở.", inline=False)
        embed.set_footer(text="HatsuneMiku Youtube Music Bot created by @imnhyneko.")
        await ctx.send(embed=embed)

    @commands.command(name='helpme')
    async def help_miku_command_alias(self, ctx):
        await ctx.invoke(self.miku_help_command)

    @commands.command(name='nowplaying', aliases=['np', 'now'])
    async def now_playing_command(self, ctx):
        await self.now_playing(ctx)

    async def now_playing(self, ctx):
        music_queue = self.get_music_queue(ctx.guild)
        if music_queue.is_empty():
            return await ctx.send("Hiện tại không có bài hát nào đang phát.")

        next_song = music_queue.get_next_song()
        if not next_song:
            return await ctx.send("Hiện tại không có bài hát nào đang phát.")

        embed = discord.Embed(title="🎶 Đang phát", color=discord.Color.green())
        embed.description = f"[{next_song.title}]({next_song.url}) - Yêu cầu bởi {next_song.requester.mention}"
        await ctx.send(embed=embed)

    @commands.command(name='join', aliases=['j', 'vao'])
    async def join_command(self, ctx):
        await self.join_voice_channel(ctx)

    async def join_voice_channel(self, ctx):
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            return await ctx.send("Bạn không ở trong kênh thoại nào.")

        voice_client = self.get_voice_client(ctx.guild)
        if voice_client is None:
            try:
                voice_client = await voice_channel.connect(timeout=10.0, reconnect=True)
                self.voice_clients[ctx.guild.id] = voice_client
                await ctx.send(f"✅ Đã tham gia kênh **{voice_channel.name}**.")
            except discord.errors.ClientException as e:
                print(f"LỖI join_voice_channel: ClientException - {e}")
                await ctx.send("Bot đã kết nối tới kênh thoại ở server này rồi.")
            except asyncio.TimeoutError as e:
                print(f"LỖI join_voice_channel: TimeoutError - {e}")
                await ctx.send("Kết nối kênh thoại bị quá thời gian chờ. Vui lòng thử lại sau.")
            except Exception as e:
                print(f"LỖI join_voice_channel: Lỗi không xác định - {e}")
                await ctx.send("Có lỗi xảy ra khi kết nối kênh thoại. Vui lòng thử lại sau.")
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)
            await ctx.send(f"✅ Đã di chuyển tới kênh **{voice_channel.name}**.")
        else:
            await ctx.send("Bot đã ở trong kênh thoại này rồi.")


@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập thành công với tên: {bot.user.name}')
    print("Các kênh bot có thể truy cập:")
    for guild in bot.guilds:
        print(f"- Server: {guild.name}")
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel) and channel.permissions_for(guild.me).read_messages and channel.permissions_for(guild.me).view_channel:
                print(f"  - Kênh văn bản: {channel.name} (ID: {channel.id})")
            elif isinstance(channel, discord.VoiceChannel) and channel.permissions_for(guild.me).view_channel and channel.permissions_for(guild.me).connect:
                print(f"  - Kênh thoại: {channel.name} (ID: {channel.id})")
            elif isinstance(channel, discord.CategoryChannel) and channel.permissions_for(guild.me).view_channel:
                print(f"  - Danh mục: {channel.name} (ID: {channel.id})")
            elif isinstance(channel, discord.StageChannel) and channel.permissions_for(guild.me).view_channel and channel.permissions_for(guild.me).connect:
                print(f"  - Kênh sân khấu: {channel.name} (ID: {channel.id})")
        print("---")

    await bot.change_presence(activity=discord.Activity(name="miku!help", type=discord.ActivityType.listening, details="Cùng lắng nghe"))


async def setup(bot):
    await bot.add_cog(MusicBot(bot))

async def main():
    await setup(bot)
    await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
