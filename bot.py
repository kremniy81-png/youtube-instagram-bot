import asyncio
import os
import yt_dlp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

# 🔑 Bot token
API_TOKEN = "8321843899:AAFgnXcFi0REvMS3o7Pv0HdtZ6VZ38VG5Zg"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# /start komandasi
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "👋 Salom!\n"
        "Menga YouTube yoki Instagram link yuboring.\n"
        "Men video yoki audio yuklab beraman 📥"
    )

# Link kelganda tugmalar chiqaramiz
@dp.message()
async def ask_quality(message: Message):
    url = message.text.strip()

    if url.startswith("ohttps://"):
        url = url.replace("ohttps://", "https://", 1)
    if "m.youtube.com" in url:
        url = url.replace("m.youtube.com", "youtube.com")

    if not ("youtube.com" in url or "youtu.be" in url or "instagram.com" in url):
        await message.answer("❌ Faqat YouTube va Instagram link yuboring!")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📹 480p", callback_data=f"download|480|{url}")],
            [InlineKeyboardButton(text="📺 720p", callback_data=f"download|720|{url}")],
            [InlineKeyboardButton(text="🎵 MP3 (audio)", callback_data=f"download|audio|{url}")]
        ]
    )

    await message.answer("📥 Yuklab olish formatini tanlang:", reply_markup=keyboard)

# Callback tugmalar
@dp.callback_query(F.data.startswith("download"))
async def download_video(call: CallbackQuery):
    _, quality, url = call.data.split("|")

    await call.message.edit_text(f"⏳ Yuklab olinmoqda... ({quality})")

    try:
        if quality == "audio":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '%(id)s.%(ext)s',
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }
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
