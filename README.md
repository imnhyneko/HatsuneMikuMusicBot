# 🎶 Miku Music Bot - Discord Bot

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub Stars](https://img.shields.io/github/stars/imnhyneko/HatsuneMikuMusicBot?style=social)](https://github.com/imnhyneko/HatsuneMikuMusicBot)
[![GitHub Forks](https://img.shields.io/github/forks/imnhyneko/HatsuneMikuMusicBot?style=social)](https://github.com/imnhyneko/HatsuneMikuMusicBot)

**Miku Music Bot** is a Discord bot that allows you to enjoy music from YouTube directly in your voice channel. Built with `discord.py`, `yt-dlp`, and `ffmpeg`, it delivers a smooth and enjoyable music experience.

---

## 🌟 Key Features

- 🎵 **Play Music from YouTube**: Supports playing music via direct links or search queries.
- 📜 **Queue System**: Create your favorite playlist.
- ⏭️ **Skip Tracks**: Jump to the next song in the queue.
- ⏹️ **Stop Music**: Stop playback and clear the queue.
- 🧾 **View Queue**: Display the upcoming songs.
- 🎧 **Now Playing**: Show details of the currently playing track.
- 😴 **Auto-Leave**: Automatically leaves the voice channel when the queue is empty to save resources.
- 🔎 **Search and Select**: Pick songs from a list of search results.
- ⌨️ **Command Aliases**: Shortened command options for convenience.
- 🖼️ **Hatsune Miku Avatar**: Adds a cute touch to your server.

---

## ⚙️ System Requirements

- 🐍 Python 3.7+
- 📦 Required Python libraries: See `requirements.txt`
- 🔊 `ffmpeg`

---

## 🚀 Installation

### 1️⃣ Clone the Repository

Clone the source code to your local machine using Git:

```bash
git clone https://github.com/imnhyneko/HatsuneMikuMusicBot.git
cd HatsuneMikuMusicBot
```

### 2️⃣ Configure the `.env` File

The bot requires a **Discord Bot Token** to function.

- Create a `.env` file from `.env.example`.
- Add your token to `.env`:

```ini
DISCORD_BOT_TOKEN=Your_Discord_Bot_Token_Here
```

How to obtain a **Discord Bot Token**:

1. Visit [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a new application or select an existing one.
3. Navigate to the "Bot" tab and create a bot.
4. Copy the token and paste it into `.env`.

### 3️⃣ Install Dependencies

Use pip to install the required libraries from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4️⃣ Install ffmpeg

#### 🔹 Windows:
- Download from the [ffmpeg official website](https://ffmpeg.org/download.html) and extract.
- Add the `bin` folder of ffmpeg to your `PATH` environment variable.

#### 🔹 Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install ffmpeg
```

#### 🔹 Linux (Arch-distro):
```bash
yay -Syu or paru -Syu
yay -S ffmpeg or paru -S ffmpeg
```

#### 🔹 Linux (CentOS/RHEL):
```bash
sudo yum update
sudo yum install ffmpeg
```

### 5️⃣ Run the Bot

After completing the setup, start the bot with:

```bash
python main.py
```

---

## 🎮 Usage

Once the bot is running, you can use the following commands in Discord:

| Command | Description | Aliases |
|------|----------|-------|
| `miku!play <song name/YouTube link>` | Play music from YouTube | `miku!p`, `miku!phat` |
| `miku!skip` | Skip the current track | `miku!sk`, `miku!boqua` |
| `miku!stop` | Stop playback and leave the channel | `miku!st`, `miku!dung` |
| `miku!queue [page]` | View the queue | `miku!q`, `miku!list` |
| `miku!nowplaying` | Display the currently playing track | `miku!np`, `miku!now` |
| `miku!help` | Show command list | `miku!h`, `miku!trogiup` |
| `miku!join` | Request the bot to join a voice channel | `miku!j`, `miku!vao` |

---

## 📜 License

This project is released under the **Apache 2.0** license – see the `LICENSE` file for details.

---

## 💖 Contributions

Contributions are welcome! If you'd like to contribute, feel free to create a **pull request**.

---

## 🙏 Acknowledgments

Thank you for using **Miku Music Bot**! If you encounter any issues, please report them in the **Issues** section on GitHub.

---

