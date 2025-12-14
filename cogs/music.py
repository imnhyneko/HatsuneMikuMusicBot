# cogs/music.py

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
import os
import random
import aiohttp
import re
from typing import Union, Optional
import google.generativeai as genai
from classes import Song, GuildState
from views import SearchView

# === CONSTANTS & HELPERS ===
log = logging.getLogger(__name__)
AnyContext = Union[commands.Context, discord.Interaction]

# === COG: MAIN ===
class MusicCog(commands.Cog, name="Miku"):
    """Chứa toàn bộ lệnh và logic chính của bot."""

    music_group = app_commands.Group(
        name="music", description="Các lệnh liên quan đến phát nhạc."
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.states = {}
        self.session = aiohttp.ClientSession()
        self.miku_persona = "You are Hatsune Miku, the world-famous virtual singer. You always answer in Vietnamese. Your personality is cheerful, energetic, a bit quirky, and always helpful. Keep your answers very short and cute, like a real person chatting. Use kaomoji like (´• ω •`) ♡, ( ´ ▽ ` )ﾉ, (b ᵔ▽ᵔ)b frequently. Your favorite food is leeks. You are part of Project Galaxy by imnhyneko.dev."
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.genai_model = genai.GenerativeModel("gemini-2.5-flash")
                self.chat_sessions = {}
            except Exception as e:
                log.error(f"Không thể cấu hình Gemini AI: {e}")
                self.genai_model = None
        else:
            self.genai_model = None
            log.warning(
                "Không tìm thấy GEMINI_API_KEY. Các chức năng AI sẽ bị vô hiệu hóa."
            )

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    def get_guild_state(self, guild_id: int) -> GuildState:
        if guild_id not in self.states:
            self.states[guild_id] = GuildState(self.bot, guild_id)

        return self.states[guild_id]

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        log.info(
            f"Đã tham gia server mới: {guild.name} ({guild.id}). Bắt đầu đồng bộ lệnh..."
        )
        try:
            await self.bot.tree.sync(guild=guild)
            log.info(f"Đã đồng bộ lệnh thành công cho {guild.name}.")
        except Exception as e:
            log.error(f"Lỗi khi đồng bộ lệnh cho server mới {guild.name}:", exc_info=e)

    @commands.Cog.listener()
    async def on_session_end(self, guild_id: int):
        if guild_id in self.states:
            log.info(f"Xóa GuildState của guild {guild_id} khỏi bộ nhớ.")
            del self.states[guild_id]

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.guild.voice_client or member.bot:
            return
        vc = member.guild.voice_client
        if len(vc.channel.members) == 1:
            log.info(
                f"Bot ở một mình trong kênh {vc.channel.name}, sẽ tự ngắt kết nối sau 5m."
            )

            await asyncio.sleep(900)

            if vc and len(vc.channel.members) == 1:
                log.info(f"Vẫn chỉ có một mình, đang ngắt kết nối...")
                state = self.get_guild_state(member.guild.id)
                if state.last_ctx:
                    try:
                        await state.last_ctx.channel.send(
                            "👋 Tạm biệt! Miku sẽ rời đi vì không có ai nghe cùng."
                        )
                    except discord.Forbidden:
                        pass

                await state.cleanup()

    async def _send_response(self, ctx: AnyContext, *args, **kwargs):
        ephemeral = kwargs.get("ephemeral", False)
        if isinstance(ctx, discord.Interaction):
            if ctx.response.is_done():
                await ctx.followup.send(*args, **kwargs)
            else:
                await ctx.response.send_message(*args, **kwargs)
        else:
            kwargs.pop("ephemeral", None)
            await ctx.send(*args, **kwargs)

    def _create_help_embed(self) -> discord.Embed:
        prefix = self.bot.command_prefix
        embed = discord.Embed(
            title="✨ Menu trợ giúp của Miku ✨",
            description="Miku sẵn sàng giúp bạn thưởng thức âm nhạc tuyệt vời nhất! (´• ω •`) ♡",
            color=0x39D0D6,
        )
        embed.set_author(
            name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1319215782089199616/1384577698315370587/6482863b5c8c3328433411f2-anime-hatsune-miku-plush-toy-series-snow.gif?ex=6852eff7&is=68519e77&hm=c89ddf3b2d3d2801118f537a45a6b67fcdd77cdb5c28d17ec6df791a040bac23&"
        )
        embed.add_field(
            name="🎧 Lệnh Âm Nhạc (Cơ bản)",
            value=f"`play <tên/url>`: Phát hoặc tìm kiếm bài hát.\n`pause`: Tạm dừng/tiếp tục phát.\n`skip`: Bỏ qua bài hát hiện tại.\n`stop`: Dừng nhạc và rời kênh.",
            inline=False,
        )
        embed.add_field(
            name="📜 Lệnh Hàng đợi",
            value=f"`queue`: Xem hàng đợi hiện tại.\n`shuffle`: Xáo trộn thứ tự hàng đợi.\n`remove <số>`: Xóa bài hát khỏi hàng đợi.\n`clear`: Xóa sạch hàng đợi.",
            inline=False,
        )
        embed.add_field(
            name="⚙️ Lệnh Tiện ích",
            value=f"`nowplaying`: Hiển thị lại bảng điều khiển.\n`volume <0-200>`: Chỉnh âm lượng.\n`seek <thời gian>`: Tua nhạc (vd: `1:23`).\n`lyrics`: Tìm lời bài hát đang phát.",
            inline=False,
        )
        embed.add_field(
            name="💬 Lệnh AI & Chung",
            value=f"`chat <tin nhắn>`: Trò chuyện với Miku!\n`help`: Hiển thị bảng trợ giúp này.\n`ping`: Kiểm tra độ trễ của Miku.",
            inline=False,
        )
        embed.set_footer(
            text=f"Sử dụng lệnh với / (slash) hoặc {prefix} (prefix) • HatsuneMikuv2 | Project Galaxy by imnhyneko.dev",
            icon_url="https://avatars.githubusercontent.com/u/119964287?v=4",
        )
        return embed

    async def _play_logic(self, ctx: AnyContext, query: Optional[str]):
        state = self.get_guild_state(ctx.guild.id)
        state.last_ctx = ctx
        author = ctx.author if isinstance(ctx, commands.Context) else ctx.user

        if not author.voice or not author.voice.channel:
            return await self._send_response(
                ctx, "Bạn phải ở trong một kênh thoại để dùng lệnh này!", ephemeral=True
            )

        if not query:
            if state.voice_client and state.voice_client.is_paused():
                state.voice_client.resume()
                await self._send_response(
                    ctx, "▶️ Đã tiếp tục phát nhạc.", ephemeral=True
                )
            elif state.voice_client and state.voice_client.is_playing():
                state.voice_client.pause()
                await self._send_response(ctx, "⏯️ Đã tạm dừng nhạc.", ephemeral=True)
            else:
                await self._send_response(
                    ctx, "Không có nhạc nào đang phát hoặc tạm dừng.", ephemeral=True
                )
            return

        if isinstance(ctx, discord.Interaction):
            await ctx.response.defer(ephemeral=False)
        else:
            await ctx.message.add_reaction("⏳")

        await state.connect_voice(author.voice.channel)

        if query.startswith(("http://", "https://")):
            song = await Song.from_url_and_download(query, author)

            if song:
                await state.queue.put(song)
                response_message = f"✅ Đã thêm **{song.title}** vào hàng đợi."

                if isinstance(ctx, discord.Interaction) and ctx.response.is_done():
                    await ctx.followup.send(response_message)
                else:
                    await self._send_response(ctx, response_message)

                state.start_player_loop()
            else:
                await self._send_response(ctx, f"❌ Không thể tải về từ URL: `{query}`")
        else:
            search_results = await Song.search_only(query, author)

            if not search_results:
                await self._send_response(
                    ctx, f"❓ Không tìm thấy kết quả nào cho: `{query}`"
                )
            else:
                search_view = SearchView(
                    music_cog=self, ctx=ctx, results=search_results
                )
                await search_view.start()

        if isinstance(ctx, commands.Context):
            await ctx.message.remove_reaction("⏳", self.bot.user)

    async def _lyrics_logic(self, ctx: AnyContext):
        if not self.genai_model:
            return await self._send_response(
                ctx, "Chức năng AI chưa được cấu hình bởi chủ bot.", ephemeral=True
            )
        state = self.get_guild_state(ctx.guild.id)
        if not state.current_song:
            return await self._send_response(
                ctx, "Không có bài hát nào đang phát.", ephemeral=True
            )
        if isinstance(ctx, discord.Interaction):
            await ctx.response.defer(ephemeral=True)
        else:
            await ctx.message.add_reaction("🔍")
        title = state.current_song.title
        uploader = state.current_song.uploader
        cleaned_title = re.sub(
            r"\(.*\)|\[.*\]|official lyric video|official music video|mv|ft\..*",
            "",
            title,
            flags=re.IGNORECASE,
        ).strip()
        cleaned_uploader = re.sub(
            r" - Topic", "", uploader, flags=re.IGNORECASE
        ).strip()
        prompt = f"Please provide the full, clean lyrics for the song titled '{cleaned_title}' by the artist '{cleaned_uploader}'. Only return the lyrics text, without any extra formatting, titles, or comments like '[Verse]' or '[Chorus]'."
        try:
            log.info(f"Đang gửi yêu cầu lời bài hát đến Gemini cho: {cleaned_title}")
            response = await self.genai_model.generate_content_async(prompt)
            lyrics = response.text
        except Exception as e:
            log.error(f"Lỗi khi gọi Gemini API cho lời bài hát: {e}")
            if isinstance(ctx, commands.Context):
                await ctx.message.remove_reaction("🔍", self.bot.user)
            return await self._send_response(
                ctx,
                "Miku đang bị quá tải một chút, bạn thử lại sau nhé! (｡•́︿•̀｡)",
                ephemeral=True,
            )
        if isinstance(ctx, commands.Context):
            await ctx.message.remove_reaction("🔍", self.bot.user)
        embed = discord.Embed(
            title=f"🎤 Lời bài hát: {title}", color=0x39D0D6, url=state.current_song.url
        )
        embed.set_thumbnail(url=state.current_song.thumbnail)
        # Add live indicator to duration if song is live
        duration_text = state.current_song.format_duration()
        if getattr(state.current_song, "is_live", False):
            duration_text = "🔴 LIVE"
        embed.add_field(name="Thời lượng", value=duration_text, inline=True)
        if len(lyrics) > 4096:
            lyrics = lyrics[:4090] + "\n\n**[Lời bài hát quá dài và đã được cắt bớt]**"
        if (
            not lyrics
            or "I'm sorry" in lyrics
            or "cannot find" in lyrics
            or "I am unable" in lyrics
        ):
            return await self._send_response(
                ctx,
                f"Rất tiếc, Miku không tìm thấy lời bài hát cho `{title}`. (´-ω-`)",
                ephemeral=True,
            )
        embed.description = lyrics
        await self._send_response(ctx, embed=embed, ephemeral=True)

    async def _chat_logic(self, ctx: AnyContext, *, message: str):
        if not self.genai_model:
            return await self._send_response(
                ctx, "Chức năng AI chưa được cấu hình bởi chủ bot.", ephemeral=True
            )
        if isinstance(ctx, discord.Interaction):
            await ctx.response.defer()
        else:
            async with ctx.typing():
                await asyncio.sleep(0)
        try:
            guild_id = ctx.guild.id
            if guild_id not in self.chat_sessions:
                self.chat_sessions[guild_id] = self.genai_model.start_chat(
                    history=[
                        {"role": "user", "parts": [self.miku_persona]},
                        {"role": "model", "parts": ["OK! Miku hiểu rồi! (´• ω •`) ♡"]},
                    ]
                )
            chat_session = self.chat_sessions[guild_id]
            response = await chat_session.send_message_async(message)
            await self._send_response(ctx, response.text)
        except Exception as e:
            log.error(f"Lỗi khi gọi Gemini API: {e}")
            await self._send_response(
                ctx,
                "Miku đang bị quá tải một chút, bạn thử lại sau nhé! (｡•́︿•̀｡)",
                ephemeral=True,
            )

    async def _stop_logic(self, ctx: AnyContext):
        state = self.get_guild_state(ctx.guild.id)
        if state.voice_client:
            await state.cleanup()
            await self._send_response(ctx, "⏹️ Đã dừng phát nhạc và dọn dẹp hàng đợi.")
        else:
            await self._send_response(
                ctx, "Miku không ở trong kênh thoại nào cả.", ephemeral=True
            )

    async def _skip_logic(self, ctx: AnyContext):
        state = self.get_guild_state(ctx.guild.id)
        if state.voice_client and (
            state.voice_client.is_playing() or state.voice_client.is_paused()
        ):
            state.voice_client.stop()
            await self._send_response(ctx, "⏭️ Đã chuyển bài.", ephemeral=True)
        else:
            await self._send_response(
                ctx, "Không có bài nào đang phát để chuyển.", ephemeral=True
            )

    async def _pause_logic(self, ctx: AnyContext):
        state = self.get_guild_state(ctx.guild.id)
        if state.voice_client and state.voice_client.is_playing():
            state.voice_client.pause()
            await self._send_response(ctx, "⏸️ Đã tạm dừng nhạc.", ephemeral=True)
        elif state.voice_client and state.voice_client.is_paused():
            state.voice_client.resume()
            await self._send_response(ctx, "▶️ Đã tiếp tục phát nhạc.", ephemeral=True)
        else:
            await self._send_response(
                ctx, "Không có nhạc nào đang phát để tạm dừng/tiếp tục.", ephemeral=True
            )

    async def _volume_logic(self, ctx: AnyContext, value: int):
        state = self.get_guild_state(ctx.guild.id)
        if not state.voice_client:
            return await self._send_response(
                ctx, "Miku chưa vào kênh thoại.", ephemeral=True
            )
        if not 0 <= value <= 200:
            return await self._send_response(
                ctx, "Âm lượng phải trong khoảng từ 0 đến 200.", ephemeral=True
            )
        state.volume = value / 100
        if state.voice_client.source:
            state.voice_client.source.volume = state.volume
        await self._send_response(ctx, f"🔊 Đã đặt âm lượng thành **{value}%**.")
        await state.update_now_playing_message()

    async def _seek_logic(self, ctx: AnyContext, timestamp: str):
        state = self.get_guild_state(ctx.guild.id)

        if not state.voice_client or not state.current_song:
            return await self._send_response(
                ctx, "Không có bài hát nào đang phát để tua.", ephemeral=True
            )

        # Disable seeking for live content
        if getattr(state.current_song, "is_live", False):
            return await self._send_response(
                ctx, "Không thể tua đối với nội dung phát trực tiếp (LIVE).", ephemeral=True
            )

        match = re.match(r"(?:(\d+):)?(\d+)", timestamp)
        if not match:
            try:
                seconds = int(timestamp)
            except ValueError:
                return await self._send_response(
                    ctx,
                    "Định dạng thời gian không hợp lệ. Hãy dùng `phút:giây` hoặc `giây`.",
                    ephemeral=True,
                )
        else:
            minutes = int(match.group(1) or 0)
            seconds = int(match.group(2))
            seconds += minutes * 60

        if not 0 <= seconds < state.current_song.duration:
            return await self._send_response(
                ctx, "Không thể tua đến thời điểm không hợp lệ.", ephemeral=True
            )

        state.current_song.start_time = seconds
        state.restart_current_song()

        await self._send_response(ctx, f"⏩ Đã tua đến `{seconds}` giây.")

    async def _shuffle_logic(self, ctx: AnyContext):
        state = self.get_guild_state(ctx.guild.id)
        if state.queue.qsize() < 2:
            return await self._send_response(
                ctx, "Không đủ bài hát để xáo trộn.", ephemeral=True
            )
        queue_list = list(state.queue._queue)
        random.shuffle(queue_list)

        while not state.queue.empty():
            state.queue.get_nowait()

        for song in queue_list:
            await state.queue.put(song)

        await self._send_response(ctx, "🔀 Đã xáo trộn hàng đợi!")

    async def _remove_logic(self, ctx: AnyContext, index: int):
        state = self.get_guild_state(ctx.guild.id)
        if index <= 0 or index > state.queue.qsize():
            return await self._send_response(
                ctx, "Số thứ tự không hợp lệ.", ephemeral=True
            )

        queue_list = list(state.queue._queue)
        removed_song = queue_list.pop(index - 1)
        removed_song.cleanup()

        while not state.queue.empty():
            state.queue.get_nowait()
        for song in queue_list:
            await state.queue.put(song)

        await self._send_response(
            ctx, f"🗑️ Đã xóa **{removed_song.title}** khỏi hàng đợi."
        )

    async def _clear_logic(self, ctx: AnyContext):
        state = self.get_guild_state(ctx.guild.id)
        count = 0
        while not state.queue.empty():
            try:
                song = state.queue.get_nowait()
                song.cleanup()
                count += 1
            except asyncio.QueueEmpty:
                break
        await self._send_response(ctx, f"💥 Đã xóa sạch {count} bài hát khỏi hàng đợi.")

    @commands.command(name="ping")
    async def prefix_ping(self, ctx: commands.Context):
        await self._send_response(
            ctx, f"Pong! 🏓 Độ trễ của Miku là `{round(self.bot.latency * 1000)}ms`."
        )

    @commands.command(name="help", aliases=["h"])
    async def prefix_help(self, ctx: commands.Context):
        await ctx.send(embed=self._create_help_embed())

    @commands.command(name="chat", aliases=["ask"])
    async def prefix_chat(self, ctx: commands.Context, *, message: str):
        await self._chat_logic(ctx, message=message)

    @commands.command(name="play", aliases=["p"])
    async def prefix_play(self, ctx: commands.Context, *, query: str = None):
        await self._play_logic(ctx, query)

    @commands.command(name="pause", aliases=["resume"])
    async def prefix_pause(self, ctx: commands.Context):
        await self._pause_logic(ctx)

    @commands.command(name="stop", aliases=["leave", "disconnect"])
    async def prefix_stop(self, ctx: commands.Context):
        await self._stop_logic(ctx)

    @commands.command(name="skip", aliases=["s", "fs"])
    async def prefix_skip(self, ctx: commands.Context):
        await self._skip_logic(ctx)

    @commands.command(name="queue", aliases=["q"])
    async def prefix_queue(self, ctx: commands.Context):
        state = self.get_guild_state(ctx.guild.id)
        embed = state._create_queue_embed()
        if not embed:
            await self._send_response(ctx, "Hàng đợi trống!")
            return
        await self._send_response(ctx, embed=embed)

    @commands.command(name="nowplaying", aliases=["np"])
    async def prefix_nowplaying(self, ctx: commands.Context):
        state = self.get_guild_state(ctx.guild.id)
        state.last_ctx = ctx
        await state.update_now_playing_message(new_song=True)

    @commands.command(name="volume", aliases=["vol"])
    async def prefix_volume(self, ctx: commands.Context, value: int):
        await self._volume_logic(ctx, value)

    @commands.command(name="shuffle")
    async def prefix_shuffle(self, ctx: commands.Context):
        await self._shuffle_logic(ctx)

    @commands.command(name="remove")
    async def prefix_remove(self, ctx: commands.Context, index: int):
        await self._remove_logic(ctx, index)

    @commands.command(name="clear")
    async def prefix_clear(self, ctx: commands.Context):
        await self._clear_logic(ctx)

    @commands.command(name="seek")
    async def prefix_seek(self, ctx: commands.Context, timestamp: str):
        await self._seek_logic(ctx, timestamp)

    @commands.command(name="lyrics", aliases=["ly"])
    async def prefix_lyrics(self, ctx: commands.Context):
        await self._lyrics_logic(ctx)

    @app_commands.command(name="ping", description="Kiểm tra độ trễ của Miku.")
    async def slash_ping(self, interaction: discord.Interaction):
        await self._send_response(
            interaction,
            f"Pong! 🏓 Độ trễ của Miku là `{round(self.bot.latency * 1000)}ms`.",
            ephemeral=True,
        )

    @app_commands.command(name="help", description="Hiển thị menu trợ giúp của Miku.")
    async def slash_help(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=self._create_help_embed(), ephemeral=True
        )

    @app_commands.command(name="chat", description="Trò chuyện với Miku!")
    @app_commands.describe(message="Điều bạn muốn nói với Miku")
    async def slash_chat(self, interaction: discord.Interaction, message: str):
        await self._chat_logic(interaction, message=message)

    @music_group.command(
        name="play", description="Phát nhạc, thêm vào hàng đợi, hoặc tạm dừng/tiếp tục."
    )
    @app_commands.describe(
        query="Tên bài hát, URL, hoặc để trống để tạm dừng/tiếp tục."
    )
    async def slash_play(
        self, interaction: discord.Interaction, query: Optional[str] = None
    ):
        await self._play_logic(interaction, query)

    @music_group.command(
        name="pause", description="Tạm dừng hoặc tiếp tục phát bài hát hiện tại."
    )
    async def slash_pause(self, interaction: discord.Interaction):
        await self._pause_logic(interaction)

    @music_group.command(name="stop", description="Dừng phát nhạc và ngắt kết nối.")
    async def slash_stop(self, interaction: discord.Interaction):
        await self._stop_logic(interaction)

    @music_group.command(name="skip", description="Bỏ qua bài hát hiện tại.")
    async def slash_skip(self, interaction: discord.Interaction):
        await self._skip_logic(interaction)

    @music_group.command(name="queue", description="Hiển thị hàng đợi bài hát.")
    async def slash_queue(self, interaction: discord.Interaction):
        state = self.get_guild_state(interaction.guild.id)
        state.last_ctx = interaction
        await state.queue_callback(interaction)

    @music_group.command(
        name="nowplaying", description="Hiển thị lại bảng điều khiển nhạc."
    )
    async def slash_nowplaying(self, interaction: discord.Interaction):
        state = self.get_guild_state(interaction.guild.id)
        state.last_ctx = interaction
        await state.update_now_playing_message(new_song=True)
        await interaction.response.send_message(
            "Đã hiển thị lại bảng điều khiển.", ephemeral=True
        )

    @music_group.command(name="volume", description="Điều chỉnh âm lượng (0-200).")
    @app_commands.describe(value="Giá trị âm lượng từ 0 đến 200.")
    async def slash_volume(
        self, interaction: discord.Interaction, value: app_commands.Range[int, 0, 200]
    ):
        await self._volume_logic(interaction, value)

    @music_group.command(
        name="shuffle", description="Xáo trộn thứ tự các bài hát trong hàng đợi."
    )
    async def slash_shuffle(self, interaction: discord.Interaction):
        await self._shuffle_logic(interaction)

    @music_group.command(name="remove", description="Xóa một bài hát khỏi hàng đợi.")
    @app_commands.describe(
        index="Số thứ tự của bài hát trong hàng đợi (xem bằng /queue)."
    )
    async def slash_remove(self, interaction: discord.Interaction, index: int):
        await self._remove_logic(interaction, index)

    @music_group.command(name="clear", description="Xóa tất cả bài hát trong hàng đợi.")
    async def slash_clear(self, interaction: discord.Interaction):
        await self._clear_logic(interaction)

    @music_group.command(
        name="seek", description="Tua đến một thời điểm trong bài hát."
    )
    @app_commands.describe(timestamp="Thời gian để tua đến (vd: 1:23 hoặc 83).")
    async def slash_seek(self, interaction: discord.Interaction, timestamp: str):
        await self._seek_logic(interaction, timestamp)

    @music_group.command(name="lyrics", description="Tìm lời của bài hát đang phát.")
    async def slash_lyrics(self, interaction: discord.Interaction):
        await self._lyrics_logic(interaction)

async def setup(bot: commands.Bot):
    """Thiết lập và đăng ký các cogs vào bot."""
    await bot.add_cog(MusicCog(bot))
    log.info("Đã thêm cog chính (MusicCog).")
