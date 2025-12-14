import discord
import asyncio
import logging
from discord.ext import commands
import discord.http
from classes import Song
from typing import Union
from enums import LoopMode

log = logging.getLogger(__name__)
AnyContext = Union[commands.Context, discord.Interaction]
VocalGuildChannel = Union[discord.VoiceChannel, discord.StageChannel]

class GuildState:
    """Quản lý trạng thái của từng server."""

    def __init__(self, bot: commands.Bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.queue = asyncio.Queue[Song]()
        self.voice_client: discord.VoiceClient | None = None
        self.voice_channel: discord.VoiceChannel | None = None
        self.now_playing_message: discord.Message | None = None
        self.current_song: Song | None = None
        self.loop_mode = LoopMode.OFF
        self.player_task: asyncio.Task | None = None
        self.last_ctx: AnyContext | None = None
        self.song_finished_event = asyncio.Event()
        self.volume = 0.5
        self.restarting = False

    async def connect_voice(self, channel: VocalGuildChannel):
        if not self.voice_client or not self.voice_client.is_connected():
            log.info(f"Connecting to voice channel #{channel.id}")
            self.voice_client = await channel.connect()
            self.voice_channel = channel
            return

        if self.voice_client.channel != channel:
            log.info(f"Moving to voice channel #{channel.id}")
            await self.voice_client.move_to(channel)
            self.voice_channel = channel

    async def add_song(self, song: Song):
        await self.queue.put(song)
        song.guild = self
        log.info(f"Added song {song.title} to guild {self.guild_id}'s queue")

    def start_player_loop(self):
        if self.player_task is None or self.player_task.done():
            self.player_task = asyncio.create_task(self.player_loop())

    def start_stream(self):
        log.info("Starting audio stream...")
        if self.voice_client.is_playing():
            self.voice_client.stop()

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(
                self.current_song.url if self.current_song.is_live else self.current_song.filepath,
                **self.current_song.get_playback_options()
            ),
            volume=self.volume,
        )

        self.voice_client.play(
            source,
            expected_packet_loss=0.2,
            signal_type="music",
            after=lambda e: self.bot.loop.call_soon_threadsafe(
                self.song_finished_event.set
            ),
        )

    def restart_current_song(self):
        log.info("Restarting current song...")
        self.restarting = True
        self.voice_client.stop()

    async def player_loop(self):
        await self.bot.wait_until_ready()
        log.info(f"Started player loop for guild {self.guild_id}")

        while True:
            self.song_finished_event.clear()

            if not self.restarting:
                # Xử lý bài hát vừa phát xong (nếu có)
                previous_song = self.current_song
                if previous_song:
                    if self.loop_mode == LoopMode.QUEUE:
                        await self.queue.put(previous_song)
                    elif self.loop_mode != LoopMode.SONG:
                        previous_song.cleanup()

                # Lấy bài hát tiếp theo
                try:
                    # Nếu không lặp lại bài hát, lấy bài mới từ hàng đợi
                    if self.loop_mode != LoopMode.SONG or not self.current_song:
                        self.current_song = await asyncio.wait_for(
                            self.queue.get(), timeout=300
                        )
                    # Nếu lặp lại, self.current_song vẫn giữ nguyên
                except asyncio.TimeoutError:
                    log.info(
                        f"Guild {self.guild_id} không hoạt động trong 5 phút, bắt đầu dọn dẹp."
                    )

                    if self.last_ctx and self.last_ctx.channel:
                        try:
                            await self.last_ctx.channel.send(
                                "😴 Đã tự động ngắt kết nối do không hoạt động."
                            )
                        except discord.Forbidden:
                            pass

                    return await self.cleanup()

                log.info(
                    f"Guild {self.guild_id}: Lấy bài hát '{self.current_song.title}' từ hàng đợi."
                )

                await self.update_voice_channel_status()
                await self.update_now_playing_message(new_song=True)

            # Phát bài hát mới
            try:
                self.start_stream()
                self.restarting = False

                await self.song_finished_event.wait()

                if self.restarting:
                    continue

                if self.current_song:
                    log.info(
                        f"Guild {self.guild_id}: Sự kiện kết thúc bài hát '{self.current_song.title}' được kích hoạt."
                    )
            except Exception as e:
                log.error(
                    f"Lỗi nghiêm trọng trong player loop của guild {self.guild_id}:",
                    exc_info=e,
                )

                if self.last_ctx and self.last_ctx.channel:
                    try:
                        await self.last_ctx.channel.send(
                            f"🤖 Gặp lỗi nghiêm trọng, Miku cần khởi động lại trình phát nhạc. Lỗi: `{e}`"
                        )
                    except discord.Forbidden:
                        pass
                return await self.cleanup()

            # Kiểm tra nếu hàng đợi trống sau khi bài hát kết thúc
            if self.queue.empty() and self.loop_mode == LoopMode.OFF:
                log.info(f"Guild {self.guild_id}: Hàng đợi đã hết.")
                if self.last_ctx and self.last_ctx.channel:
                    try:
                        await self.last_ctx.channel.send(
                            "🎶 Hàng đợi đã kết thúc! Miku đi nghỉ đây (´｡• ᵕ •｡`) ♡"
                        )
                    except discord.Forbidden:
                        pass

                return await self.cleanup()

    async def update_voice_channel_status(self):
        guild = self.bot.get_guild(self.guild_id)
        route = discord.http.Route("PUT", "/channels/{channel_id}/voice-status", channel_id=self.voice_client.channel.id)
        payload = {
            "status": f"🎵 {self.current_song.title}" if self.current_song else ""
        }

        await guild._state.http.request(route, json=payload)

    async def update_now_playing_message(self, new_song=False):
        if not self.last_ctx:
            return
        
        if not self.current_song and self.now_playing_message:
            try:
                await self.now_playing_message.delete()
            except discord.NotFound:
                pass

            self.now_playing_message = None
            return

        if not self.current_song:
            return
        
        embed = self.create_now_playing_embed()
        view = self.create_control_view()
        
        if new_song and self.now_playing_message:
            try:
                await self.now_playing_message.delete()
            except discord.NotFound:
                pass
            self.now_playing_message = None
            
        if self.now_playing_message:
            try:
                await self.now_playing_message.edit(embed=embed, view=view)
                return
            except discord.NotFound:
                self.now_playing_message = None
                
        if not self.now_playing_message:
            try:
                self.now_playing_message = await self.last_ctx.channel.send(
                    embed=embed, view=view
                )
            except (discord.Forbidden, discord.HTTPException) as e:
                log.warning(f"Không thể gửi/cập nhật tin nhắn Now Playing: {e}")
                self.now_playing_message = None

    def create_now_playing_embed(self) -> discord.Embed:
        song = self.current_song
        embed = discord.Embed(title=song.title, url=song.url, color=0x39D0D6)
        embed.set_author(
            name=f"Đang phát 🎵 (Âm lượng: {int(self.volume*100)}%)",
            icon_url=self.bot.user.display_avatar.url,
        )
        embed.set_thumbnail(url=song.thumbnail)
        embed.add_field(name="Nghệ sĩ", value=song.uploader or "N/A", inline=True)
        # Add live indicator to duration if song is live
        duration_text = song.format_duration()
        if getattr(song, "is_live", False):
            duration_text = "🔴 LIVE"
        embed.add_field(name="Thời lượng", value=duration_text, inline=True)
        embed.add_field(name="Yêu cầu bởi", value=song.requester.mention, inline=True)
        loop_status = {
            LoopMode.OFF: "Tắt",
            LoopMode.SONG: "🔁 Bài hát",
            LoopMode.QUEUE: "🔁 Hàng đợi",
        }
        next_song_title = (
            "Không có"
            if self.queue.empty()
            else self.queue._queue[0].title[:50] + "..."
        )
        total_songs = self.queue.qsize() + (1 if self.current_song else 0)
        embed.set_footer(
            text=f"Tiếp theo: {next_song_title} • Lặp: {loop_status[self.loop_mode]} • Tổng cộng: {total_songs} bài"
        )
        return embed

    def create_control_view(self) -> discord.ui.View:
        view = discord.ui.View(timeout=None)
        pause_resume_btn = discord.ui.Button(
            emoji="⏯️",
            style=discord.ButtonStyle.secondary,
            custom_id=f"ctrl_pause_{self.guild_id}",
        )
        skip_btn = discord.ui.Button(
            emoji="⏭️",
            style=discord.ButtonStyle.secondary,
            custom_id=f"ctrl_skip_{self.guild_id}",
        )
        stop_btn = discord.ui.Button(
            emoji="⏹️",
            style=discord.ButtonStyle.danger,
            custom_id=f"ctrl_stop_{self.guild_id}",
        )
        loop_btn = discord.ui.Button(
            emoji="🔁",
            style=discord.ButtonStyle.secondary,
            custom_id=f"ctrl_loop_{self.guild_id}",
        )
        queue_btn = discord.ui.Button(
            label="Hàng đợi",
            emoji="📜",
            style=discord.ButtonStyle.primary,
            custom_id=f"ctrl_queue_{self.guild_id}",
        )
        pause_resume_btn.callback = self.pause_resume_callback
        skip_btn.callback = self.skip_callback
        stop_btn.callback = self.stop_callback
        loop_btn.callback = self.loop_callback
        queue_btn.callback = self.queue_callback
        view.add_item(pause_resume_btn)
        view.add_item(skip_btn)
        view.add_item(stop_btn)
        view.add_item(loop_btn)
        view.add_item(queue_btn)
        return view

    async def pause_resume_callback(self, interaction: discord.Interaction):
        if self.voice_client.is_paused():
            self.voice_client.resume()
            await interaction.response.send_message(
                "▶️ Đã tiếp tục phát.", ephemeral=True
            )
        else:
            self.voice_client.pause()
            await interaction.response.send_message("⏸️ Đã tạm dừng.", ephemeral=True)

    async def skip_callback(self, interaction: discord.Interaction):
        if self.voice_client and (
            self.voice_client.is_playing() or self.voice_client.is_paused()
        ):
            self.voice_client.stop()
            await interaction.response.send_message("⏭️ Đã chuyển bài.", ephemeral=True)
        else:
            await interaction.response.send_message(
                "Không có bài nào đang phát để chuyển.", ephemeral=True
            )

    async def stop_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "⏹️ Đang dừng phát nhạc và dọn dẹp hàng đợi...", ephemeral=True
        )
        await self.cleanup()

    async def loop_callback(self, interaction: discord.Interaction):
        self.loop_mode = LoopMode((self.loop_mode.value + 1) % 3)
        log.info(f"Guild {self.guild_id} đã đổi chế độ lặp thành {self.loop_mode.name}")
        mode_text = {
            LoopMode.OFF: "Tắt lặp.",
            LoopMode.SONG: "🔁 Lặp lại bài hát hiện tại.",
            LoopMode.QUEUE: "🔁 Lặp lại toàn bộ hàng đợi.",
        }

        await interaction.response.send_message(
            mode_text[self.loop_mode], ephemeral=True
        )

        await self.update_now_playing_message()

    async def queue_callback(self, interaction: discord.Interaction):
        embed = self._create_queue_embed()
        if not embed:
            return await interaction.response.send_message(
                "Hàng đợi trống!", ephemeral=True
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    def _create_queue_embed(self) -> discord.Embed | None:
        if self.queue.empty() and not self.current_song:
            return None
        embed = discord.Embed(title="📜 Hàng đợi bài hát", color=discord.Color.gold())
        if self.current_song:
            embed.add_field(
                name="▶️ Đang phát",
                value=f"[{self.current_song.title}]({self.current_song.url}) - Y/c bởi {self.current_song.requester.mention}",
                inline=False,
            )
        queue_list = list(self.queue._queue)
        if queue_list:
            queue_text = "\n".join(
                [
                    f"`{i+1}.` [{song.title}]({song.url})"
                    for i, song in enumerate(queue_list[:10])
                ]
            )
            if len(queue_list) > 10:
                queue_text += f"\n... và {len(queue_list) - 10} bài hát khác."
            embed.add_field(name="🎶 Tiếp theo", value=queue_text, inline=False)
        embed.set_footer(
            text=f"Tổng cộng: {len(queue_list) + (1 if self.current_song else 0)} bài hát"
        )
        return embed

    async def cleanup(self):
        log.info(f"Bắt đầu cleanup cho guild {self.guild_id}")
        self.bot.dispatch("session_end", self.guild_id)

        if self.voice_client:
            await self.voice_client.disconnect(force=True)
            log.info(f"Đã ngắt kết nối voice client khỏi guild {self.guild_id}")

        if self.current_song:
            self.current_song.cleanup()
            self.current_song = None

        try:
            await self.update_now_playing_message()
            await self.update_voice_channel_status()
        except Exception as e:
            log.warning(f"Error occured while updating playing message and status: {e}")

        # Cleanup cache files after voice client clean up to avoid cache file locking by ffmpeg
        while not self.queue.empty():
            try:
                song = self.queue.get_nowait()
                song.cleanup()
            except asyncio.QueueEmpty:
                break

        # Finally, we can commit sudoku our task.
        if self.player_task:
            self.player_task.cancel()
