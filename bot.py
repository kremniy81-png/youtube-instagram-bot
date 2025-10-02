import asyncio
import os
import yt_dlp
import hashlib
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

# 🔑 Bot token
API_TOKEN = "8321843899:AAFgnXcFi0REvMS3o7Pv0HdtZ6VZ38VG5Zg"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Global dict URL saqlash uchun
downloads = {}

# /start komandasi
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "👋 Salom!\n"
        "Menga YouTube yoki Instagram link yuboring.\n"
        "Men video yoki audio yuklab beraman 📥"
    )

# URL’ni hash qilib callback_data yaratish
def make_callback_data(url: str, quality: str) -> str:
    url_hash = hashlib.md5(url.encode()).hexdigest()  # 32 belgi
    return f"download|{quality}|{url_hash}"

# Link kelganda tugmalar chiqaramiz
@dp.message()
async def ask_quality(message: Message):
    url = message.text.strip()

    # Ba'zi mobil linklarni tozalash
    if url.startswith("ohttps://"):
        url = url.replace("ohttps://", "https://", 1)
    if "m.youtube.com" in url:
        url = url.replace("m.youtube.com", "youtube.com")

    if not ("youtube.com" in url or "youtu.be" in url or "instagram.com" in url):
        await message.answer("❌ Faqat YouTube va Instagram link yuboring!")
        return

    # Inline tugmalar yaratish
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📹 480p",
                callback_data=make_callback_data(url, "480")
            )],
            [InlineKeyboardButton(
                text="📺 720p",
                callback_data=make_callback_data(url, "720")
            )],
            [InlineKeyboardButton(
                text="🎵 MP3 (audio)",
                callback_data=make_callback_data(url, "audio")
            )]
        ]
    )

    # URL’ni dict’ga saqlash
    for row in keyboard.inline_keyboard:
        for button in row:
            downloads[button.callback_data] = url

    await message.answer("📥 Yuklab olish formatini tanlang:", reply_markup=keyboard)

# Callback tugmalar
@dp.callback_query(F.data.startswith("download"))
async def download_video(call: CallbackQuery):
    _, quality, url_hash = call.data.split("|")
    url = downloads.get(call.data)

    if not url:
        await call.message.answer("❌ URL topilmadi!")
        return

    await call.message.edit_text(f"⏳ Yuklab olinmoqda... ({quality})")

    try:
        # Audio yoki video variantlarini tanlash
        if quality == "audio":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '%(id)s.%(ext)s',
                'postprocessors': [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}
                ],
                'quiet': True,
                'no_warnings': True,
                'external_downloader': 'aria2c',
                'external_downloader_args': ['-x16', '-k1M']
            }
        else:
            ydl_opts = {
                'outtmpl': '%(id)s.%(ext)s',
                'format': f'bestvideo[height<={quality}]+bestaudio/best',
                'merge_output_format': 'mp4',
                'noplaylist': True,
                'retries': 5,
                'fragment_retries': 5,
                'quiet': True,
                'no_warnings': True,
                'external_downloader': 'aria2c',
                'external_downloader_args': ['-x16', '-k1M']
            }

        if os.path.exists("cookies.txt"):
            ydl_opts["cookiefile"] = "cookies.txt"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if quality == "audio":
                filename = os.path.splitext(filename)[0] + ".mp3"

        file = FSInputFile(filename)
        if quality == "audio":
            await call.message.answer_audio(file)
        else:
            await call.message.answer_video(file)

        os.remove(filename)

    except Exception as e:
        await call.message.answer(f"❌ Xatolik: {e}")

# Botni ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

