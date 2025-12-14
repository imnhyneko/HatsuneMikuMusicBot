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
        self.title = data.get("title") or data.get("fulltitle") or "Không có tiêu đề"
        self.thumbnail = data.get("thumbnail")
        self.duration = data.get("duration")
        self.uploader = data.get("uploader") or data.get("channel") or data.get("creator") or "Không rõ"
        self.is_live = False
        self.filepath = None
        self.start_time = 0
        self.id = data.get("id")
        self.guild: GuildState = None

    def format_duration(self):
        # For live content, always return "🔴 LIVE"
        if getattr(self, "is_live", False):
            return "🔴 LIVE"
        if self.duration is None:
            return "N/A"

        m, s = divmod(self.duration, 60)
        h, m = divmod(m, 60)

        return (
            f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
            if h > 0
            else f"{int(m):02d}:{int(s):02d}"
        )
    
    def get_playback_options(self):
        options = []

        if (self.start_time > 0):
            options.append(f"-ss {self.start_time}")

        return {
            "before_options": " ".join(options),
            "options": "-vn"
        }

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
        info_partial = functools.partial(ytdl.extract_info, url, download=False)
        try:
            info_data = await loop.run_in_executor(None, info_partial)
            if not info_data:
                return None
            if "entries" in info_data:
                info_data = info_data["entries"][0]

            is_live = info_data.get("is_live") or info_data.get("was_live") or False

            # Additional robust check for generic/icecast/streams
            if not is_live:
                extractor = info_data.get("extractor_key", "").lower()
                duration = info_data.get("duration")
                formats = info_data.get("formats", [])
                # If generic extractor and no duration, or only one format and it's a stream type
                stream_exts = {"ogg", "mp3", "aac", "opus", "webm"}
                if (
                    (extractor == "generic" and duration is None)
                    or (
                        len(formats) == 1 and
                        (formats[0].get("ext") in stream_exts or formats[0].get("protocol") in ("http", "https"))
                    )
                ):
                    is_live = True
                elif any(
                    (f.get("protocol") in ("m3u8", "m3u8_native") and f.get("preference", 0) == 0)
                    or f.get("is_live")
                    for f in formats
                ):
                    is_live = True

            if is_live:
                song = cls(info_data, requester)
                song.is_live = True
                song.filepath = None
                return song

            # Not live, proceed to download
            partial = functools.partial(ytdl.extract_info, url, download=True)
            data = await loop.run_in_executor(None, partial)
            if not data:
                return None
            if "entries" in data:
                data = data["entries"][0]

            song = cls(data, requester)
            song.is_live = False
            song.filepath = ytdl.prepare_filename(data)
            return song
        except Exception as e:
            log.error(f"Lỗi yt-dlp khi TẢI VỀ '{url}': {e}", exc_info=True)
            return None
