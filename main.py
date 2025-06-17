import sys
import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging

def setup_logging():
    """Thiết lập logging để ghi ra file và console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler("miku.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

setup_logging()
load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    logging.critical("LỖI: Vui lòng thiết lập biến DISCORD_BOT_TOKEN trong file .env")
    sys.exit()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

class MikuBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="miku!",
            help_command=None,
            intents=intents
        )
        self.initial_cogs = ['cogs.music']
        self.synced = False

    async def setup_hook(self):
        """Chỉ tải cogs, không làm gì khác."""
        for extension in self.initial_cogs:
            try:
                await self.load_extension(extension)
                logging.info(f"Đã tải thành công: {extension}")
            except Exception as e:
                logging.error(f"Lỗi khi tải extension {extension}:", exc_info=e)

    async def on_ready(self):
        """
        Sự kiện sau khi bot kết nối.
        Đây là nơi an toàn để đồng bộ lệnh cho các server hiện có.
        """
        await self.wait_until_ready()
        if not self.synced:
            logging.info("Bắt đầu đồng bộ lệnh lần đầu cho các server hiện có...")
            synced_count = 0
            for guild in self.guilds:
                try:
                    await self.tree.sync(guild=guild)
                    synced_count += 1
                except discord.errors.Forbidden:
                    logging.warning(f"Không có quyền đồng bộ lệnh cho server: {guild.name} ({guild.id})")
                except Exception as e:
                    logging.error(f"Lỗi khi đồng bộ lệnh cho guild {guild.id}:", exc_info=e)

            logging.info(f"Đã đồng bộ lệnh cho {synced_count}/{len(self.guilds)} server.")
            self.synced = True

        logging.info(f'Đăng nhập thành công với tên {self.user} (ID: {self.user.id})')
        logging.info(f'Miku đã sẵn sàng trong {len(self.guilds)} servers!')
        logging.info('--------------------------------------------------')
        activity = discord.Activity(type=discord.ActivityType.listening, name=f"{self.command_prefix}help | /help")
        await self.change_presence(activity=activity)

async def main():
    if not os.path.exists('./cache'):
        os.makedirs('./cache')
        logging.info("Đã tạo thư mục './cache")
    
    async with MikuBot() as bot:
        await bot.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot đã tắt theo yêu cầu của người dùng.")
