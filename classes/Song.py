import discord
import asyncio
import yt_dlp
import functools
import logging
import os
import logging
from classes import GuildState

log = logging.getLogger(__name__)

YTDL_SEARCH_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": False,
    "no_warnings": True,
    "default_search": "ytsearch7",
    "source_address": "0.0.0.0",
    "extract_flat": "search"
}

YTDL_DOWNLOAD_OPTIONS = {
    "format": "bestaudio[ext=m4a]/bestaudio/best",
    "outtmpl": "cache/%(id)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": False,
    "no_warnings": True,
    "source_address": "0.0.0.0",
    "cachedir": False
}

class Song:
    """Đại diện cho một bài hát."""

    def __init__(self, data, requester: discord.Member | discord.User):
        self.requester = requester
        self.data = data
        self.url = data.get("webpage_url") or data.get("url")
        self.title = data.get("title")
        self.thumbnail = data.get("thumbnail")
        self.duration = data.get("duration")
        self.uploader = data.get("uploader")
        self.filepath = None
        self.id = data.get("id")
        self.guild: GuildState = None

    def format_duration(self):
        if self.duration is None:
            return "N/A"

        m, s = divmod(self.duration, 60)
        h, m = divmod(m, 60)

        return (
            f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
            if h > 0
            else f"{int(m):02d}:{int(s):02d}"
        )

    def cleanup(self):
        if self.filepath and os.path.exists(self.filepath):
            try:
                os.remove(self.filepath)
                log.info(f"Đã xóa file cache: {self.filepath}")
            except OSError as e:
                log.error(f"Lỗi khi xóa file cache {self.filepath}: {e}")

    @classmethod
    async def search_only(cls, query: str, requester: discord.Member | discord.User):
        loop = asyncio.get_running_loop()
        partial = functools.partial(
            yt_dlp.YoutubeDL(YTDL_SEARCH_OPTIONS).extract_info, query, download=False
        )

        try:
            data = await loop.run_in_executor(None, partial)
            if not data or "entries" not in data or not data["entries"]:
                return []
            return [cls(entry, requester) for entry in data["entries"]]
        except Exception as e:
            log.error(f"Lỗi yt-dlp khi TÌM KIẾM '{query}': {e}", exc_info=True)
            return []

    @classmethod
    async def from_url_and_download(
        cls, url: str, requester: discord.Member | discord.User
    ):
        loop = asyncio.get_running_loop()
        ytdl = yt_dlp.YoutubeDL(YTDL_DOWNLOAD_OPTIONS)
        partial = functools.partial(ytdl.extract_info, url, download=True)
        try:
            data = await loop.run_in_executor(None, partial)

            if not data:
                return None
            if "entries" in data:
                data = data["entries"][0]

            song = cls(data, requester)
            song.filepath = ytdl.prepare_filename(data)
            return song
        except Exception as e:
            log.error(f"Lỗi yt-dlp khi TẢI VỀ '{url}': {e}", exc_info=True)
            return None
