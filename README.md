# 🎶 Miku Music Bot - Discord Bot

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub Stars](https://img.shields.io/github/stars/imnhyneko/HatsuneMikuMusicBot?style=social)](https://github.com/imnhyneko/HatsuneMikuMusicBot)
[![GitHub Forks](https://img.shields.io/github/forks/imnhyneko/HatsuneMikuMusicBot?style=social)](https://github.com/imnhyneko/HatsuneMikuMusicBot)

**Miku Music Bot** là bot Discord giúp bạn thưởng thức âm nhạc từ YouTube ngay trong kênh thoại của mình. Được xây dựng bằng `discord.py`, `yt-dlp` và `ffmpeg`, bot mang đến trải nghiệm âm nhạc mượt mà và thú vị.

---

## 🌟 Tính năng nổi bật

- 🎵 **Phát nhạc từ YouTube**: Hỗ trợ phát nhạc bằng link trực tiếp hoặc tìm kiếm theo tên bài hát.
- 📜 **Hàng chờ phát nhạc**: Tạo danh sách phát yêu thích của bạn.
- ⏭️ **Bỏ qua bài hát**: Chuyển sang bài tiếp theo trong danh sách.
- ⏹️ **Dừng phát nhạc**: Ngừng nhạc và xoá danh sách phát.
- 🧾 **Xem danh sách phát**: Hiển thị danh sách các bài hát đang chờ.
- 🎧 **Đang phát**: Hiển thị bài hát hiện đang phát.
- 😴 **Tự động rời kênh**: Tiết kiệm tài nguyên bằng cách tự động rời kênh sau khi danh sách phát trống.
- 🔎 **Tìm kiếm và chọn bài hát**: Chọn bài hát từ danh sách kết quả tìm kiếm.
- ⌨️ **Hỗ trợ lệnh alias**: Cung cấp các alias giúp nhập lệnh nhanh hơn.
- 🖼️ **Hình đại diện Hatsune Miku**: Mang đến sự dễ thương cho server của bạn.

---

## ⚙️ Yêu cầu hệ thống

- 🐍 Python 3.7+
- 📦 Các thư viện Python: Xem trong tệp `requirements.txt`
- 🔊 `ffmpeg`

---

## 🚀 Cài đặt

### 1️⃣ Clone Repository

Sao chép mã nguồn về máy của bạn bằng Git:

```bash
git clone https://github.com/imnhyneko/HatsuneMikuMusicBot.git
cd HatsuneMikuMusicBot
```

### 2️⃣ Cấu hình tệp `.env`

Bot cần **Discord Bot Token** để hoạt động.

- Tạo file `.env` từ `.env.example`.
- Thêm token vào `.env`:

```ini
DISCORD_BOT_TOKEN=Your_Discord_Bot_Token_Here
```

Cách lấy **Discord Bot Token**:

1. Truy cập [Discord Developer Portal](https://discord.com/developers/applications).
2. Tạo ứng dụng mới hoặc chọn ứng dụng có sẵn.
3. Vào tab "Bot", tạo bot mới.
4. Sao chép token và dán vào `.env`.

### 3️⃣ Cài đặt thư viện cần thiết

Dùng pip để cài đặt các thư viện từ `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4️⃣ Cài đặt ffmpeg

#### 🔹 Windows:
- Tải xuống từ [trang chủ ffmpeg](https://ffmpeg.org/download.html) và giải nén.
- Thêm thư mục `bin` của ffmpeg vào biến môi trường `PATH`.

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

### 5️⃣ Chạy bot

Sau khi cài đặt đầy đủ, chạy bot bằng lệnh:

```bash
python main.py
```

---

## 🎮 Cách sử dụng

Khi bot hoạt động, bạn có thể sử dụng các lệnh sau trong Discord:

| Lệnh | Chức năng | Alias |
|------|----------|-------|
| `miku!play <tên bài hát/link YouTube>` | Phát nhạc từ YouTube | `miku!p`, `miku!phat` |
| `miku!skip` | Bỏ qua bài hát hiện tại | `miku!sk`, `miku!boqua` |
| `miku!stop` | Dừng nhạc và rời kênh | `miku!st`, `miku!dung` |
| `miku!queue [trang]` | Xem danh sách phát | `miku!q`, `miku!list` |
| `miku!nowplaying` | Hiển thị bài hát hiện tại | `miku!np`, `miku!now` |
| `miku!help` | Hiển thị danh sách lệnh | `miku!h`, `miku!trogiup` |
| `miku!join` | Yêu cầu bot vào kênh thoại | `miku!j`, `miku!vao` |

---

## 📜 Giấy phép

Dự án này được phát hành theo giấy phép **Apache 2.0** – xem tệp `LICENSE` để biết thêm chi tiết.

---

## 💖 Đóng góp

Mọi đóng góp đều được hoan nghênh! Nếu bạn muốn đóng góp, hãy tạo một **pull request**.

---

## 🙏 Cảm ơn

Cảm ơn bạn đã sử dụng **Miku Music Bot**! Nếu gặp bất kỳ lỗi nào, vui lòng báo cáo trong phần **Issues** trên GitHub.

---

