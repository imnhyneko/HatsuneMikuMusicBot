import discord
import logging
import asyncio
import math
from discord.ext import commands
from typing import Union
from classes import Song

log = logging.getLogger(__name__)
AnyContext = Union[commands.Context, discord.Interaction]

class SearchView(discord.ui.View):
    """Giao diện cho kết quả tìm kiếm."""

    def __init__(self, *, music_cog, ctx: AnyContext, results: list[Song]):
        super().__init__(timeout=180.0)
        self.music_cog = music_cog
        self.ctx = ctx
        self.requester = ctx.author if isinstance(ctx, commands.Context) else ctx.user
        self.results = results
        self.current_page = 1
        self.songs_per_page = 5
        self.total_pages = math.ceil(len(self.results) / self.songs_per_page)
        self.message = None
        self.update_components()

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(
                    content="Hết thời gian tìm kiếm.", embed=None, view=None
                )
            except discord.NotFound:
                pass
        self.stop()

    async def start(self):
        embed = self.create_page_embed()
        if isinstance(self.ctx, discord.Interaction):
            if self.ctx.response.is_done():
                self.message = await self.ctx.followup.send(
                    embed=embed, view=self, ephemeral=True
                )
            else:
                await self.ctx.response.send_message(
                    embed=embed, view=self, ephemeral=True
                )
                self.message = await self.ctx.original_response()
        else:
            self.message = await self.ctx.send(embed=embed, view=self)

    def update_components(self):
        self.prev_page_button.disabled = self.current_page == 1
        self.next_page_button.disabled = self.current_page >= self.total_pages
        self.clear_items()
        self.add_item(self.create_select_menu())
        self.add_item(self.prev_page_button)
        self.add_item(self.next_page_button)
        self.add_item(self.cancel_button)

    def create_page_embed(self) -> discord.Embed:
        start_index = (self.current_page - 1) * self.songs_per_page
        end_index = start_index + self.songs_per_page
        page_results = self.results[start_index:end_index]
        description = "".join(
            f"`{i+1}.` [{s.title}]({s.url})\n`{s.uploader or 'N/A'} - {s.format_duration()}`\n\n"
            for i, s in enumerate(page_results, start=start_index)
        )
        embed = discord.Embed(
            title=f"🔎 Kết quả tìm kiếm (Trang {self.current_page}/{self.total_pages})",
            description=description,
            color=discord.Color.blue(),
        )
        embed.set_footer(
            text=f"Yêu cầu bởi {self.requester.display_name}",
            icon_url=self.requester.display_avatar.url,
        )
        return embed

    def create_select_menu(self) -> discord.ui.Select:
        start_index = (self.current_page - 1) * self.songs_per_page
        end_index = start_index + self.songs_per_page
        options = [
            discord.SelectOption(label=f"{i+1}. {s.title[:80]}", value=str(i))
            for i, s in enumerate(
                self.results[start_index:end_index], start=start_index
            )
        ]
        select = discord.ui.Select(
            placeholder="Chọn một bài hát để thêm...",
            options=options,
            custom_id="search_select_menu",
        )
        select.callback = self.select_callback
        return select

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.requester.id:
            return await interaction.response.send_message(
                "Bạn không phải người yêu cầu!", ephemeral=True
            )
        
        await interaction.response.defer()
        await self.message.edit(
            content="⏳ Đang tải bài hát bạn chọn...", embed=None, view=None
        )

        selected_song = await Song.from_url_and_download(
            self.results[int(interaction.data["values"][0])].url, self.requester
        )

        if selected_song:
            state = self.music_cog.get_guild_state(interaction.guild_id)
            await state.add_song(selected_song)

            if state.player_task is None or state.player_task.done():
                state.player_task = asyncio.create_task(state.player_loop())
            await self.message.edit(
                content=f"✅ Đã thêm **{selected_song.title}** vào hàng đợi."
            )
        else:
            await self.message.edit(
                content=f"❌ Rất tiếc, đã có lỗi khi tải về bài hát này."
            )

        self.stop()

    @discord.ui.button(label="Trước", style=discord.ButtonStyle.secondary, emoji="⬅️")
    async def prev_page_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.requester.id:
            return await interaction.response.send_message(
                "Bạn không phải người yêu cầu!", ephemeral=True
            )
        self.current_page -= 1
        self.update_components()
        await interaction.response.edit_message(
            embed=self.create_page_embed(), view=self
        )

    @discord.ui.button(label="Sau", style=discord.ButtonStyle.secondary, emoji="➡️")
    async def next_page_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.requester.id:
            return await interaction.response.send_message(
                "Bạn không phải người yêu cầu!", ephemeral=True
            )
        self.current_page += 1
        self.update_components()
        await interaction.response.edit_message(
            embed=self.create_page_embed(), view=self
        )

    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def cancel_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.requester.id:
            return await interaction.response.send_message(
                "Bạn không phải người yêu cầu!", ephemeral=True
            )
        await self.message.edit(content="Đã hủy tìm kiếm.", embed=None, view=None)
        self.stop()
