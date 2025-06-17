<div align="center">
  <img src="https://cdn.discordapp.com/attachments/1319215782089199616/1384576393521795152/FnBDe4WXwAQ9sjv.jpg?ex=6852eec0&is=68519d40&hm=fbf4e41a233317bb508ae993c4e07494267691af9786e3cf65773a73868f3797&" alt="Hatsune Miku" width="700"/>
  <h1>HatsuneMiku - Project Galaxy</h1>
  <p>
    An intelligent, feature-rich Discord music bot powered by Google's Gemini AI.
  </p>
  
  <p>
    <a href="https://github.com/imnhyneko/HatsuneMikuMusicBot/releases"><img src="https://img.shields.io/github/v/release/imnhyneko/HatsuneMikuMusicBot?style=for-the-badge&color=39d0d6" alt="Latest Release"></a>
    <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge&color=39d0d6" alt="License"></a>
    <a href="https://github.com/imnhyneko/HatsuneMikuMusicBot/stargazers"><img src="https://img.shields.io/github/stars/imnhyneko/HatsuneMikuMusicBot?style=for-the-badge&color=39d0d6" alt="GitHub Stars"></a>
  </p>
</div>

---

## 🎤 About Miku

**HatsuneMiku** is not just another music bot. It's a complete rewrite of the original, infused with the power of **Google's Gemini AI** to create a smarter, more reliable, and more interactive musical companion for your Discord server.

This project, codenamed **Project Galaxy**, aims to take your server's music experience to the stars.

## ✨ Key Features

- **🚀 Dual Command System**: Supports both modern **Slash Commands** (`/play`) and traditional **Prefix Commands** (`miku!play`).
- **🧠 Gemini-Powered Lyrics**: Utilizes Google's Gemini AI to find accurate, clean lyrics for any song, overcoming messy YouTube titles.
- **💬 AI Chatbot Persona**: Chat directly with Miku! Powered by Gemini, she has a unique, cheerful personality and remembers your conversation history within each server.
- **🎶 Comprehensive Music Controls**: All the commands you need: `play`, `pause`, `skip`, `stop`, `queue`, `shuffle`, `seek`, `volume`, and more.
- **🔎 Smart Search & Select**: Don't have a link? Just search for a song, and Miku will present you with a list of results to choose from.
- **🎧 High-Quality Audio**: Uses `yt-dlp` and `FFmpeg` to deliver the best possible audio quality from YouTube.
- **😴 Auto-Leave & Cleanup**: Automatically disconnects and cleans up resources when left alone or when the queue ends, ensuring efficiency.
- **🔁 Advanced Loop Modes**: Supports looping a single track or the entire queue.

---

## ⚙️ Requirements

- 🐍 Python 3.10+
- 📦 All Python libraries listed in `requirements.txt`.
- 🔊 `FFmpeg` installed and accessible in your system's PATH.

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/imnhyneko/HatsuneMikuMusicBot.git
cd HatsuneMikuMusicBot
```

### 2. Install Dependencies
Create a virtual environment (recommended) and install the required packages.
```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 3. Install FFmpeg
You need FFmpeg to process audio.
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html), extract it, and add the `bin` folder to your system's `PATH`.
- **macOS (via Homebrew)**: `brew install ffmpeg`
- **Linux (Debian/Ubuntu)**: `sudo apt update && sudo apt install ffmpeg`

### 4. Configure Environment Variables
The bot requires API keys to function. Create a `.env` file in the root directory and add the following:

```ini
# Your Discord bot's token
DISCORD_BOT_TOKEN="YOUR_DISCORD_BOT_TOKEN_HERE"

# (Optional but Recommended) Your Google Gemini API key for AI features
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
```

- **Discord Token**: Get it from the [Discord Developer Portal](https://discord.com/developers/applications) under your application's "Bot" tab.
- **Gemini API Key**: Get it from [Google AI Studio](https://aistudio.google.com/). The free tier is very generous and sufficient for most use cases.

### 5. Run the Bot
Once everything is configured, start Miku with:
```bash
python main.py
```

---

## 🎮 Command List

Miku understands both `/` (slash) and `miku!` (prefix) commands.

### 🎧 Music Commands
| Command | Description |
| :--- | :--- |
| `play <name/url>` | Plays, queues, or searches for a song. |
| `pause` | Pauses or resumes the current track. |
| `skip` | Skips to the next song. |
| `stop` | Stops the music and clears the queue. |
| `queue` | Shows the current song queue. |
| `shuffle` | Randomizes the queue. |
| `nowplaying` | Re-displays the music control panel. |
| `volume <0-200>`| Adjusts the bot's volume. |
| `seek <timestamp>`| Seeks to a specific time (e.g., `1:23`). |
| `lyrics` | Fetches lyrics for the current song using AI. |
| `remove <number>` | Removes a specific song from the queue. |
| `clear` | Clears the entire queue. |

### 💬 AI & General Commands
| Command | Description |
| :--- | :--- |
| `chat <message>` | Chat directly with Miku! |
| `help` | Shows the detailed help menu. |
| `ping` | Checks the bot's latency. |

---

## 📜 License

This project is licensed under the **Apache 2.0 License**. See the `LICENSE` file for details.

---

## 💖 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/imnhyneko/HatsuneMikuMusicBot/issues).

---

<div align="center">
  Thank you for bringing Miku to your server! ( ´ ▽ ` )ﾉ
</div>
