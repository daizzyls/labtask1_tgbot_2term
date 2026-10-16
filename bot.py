#=====================================LIB_IMPORTS
import asyncio
import csv
import logging
import os
import re
from datetime import datetime

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

#====================================FILE_IMPORTS
from ANI import ANILIST_QUE
from strTOK import BOT_TOKEN, NYT_API_KEY

#====================================VARIABLE
TOKEN = BOT_TOKEN
NYT_SEARCH_URL = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
ANILIST_QUERY = ANILIST_QUE

logging.basicConfig(level=logging.INFO)
LOG_FILE = "bot_logs.csv"

bot = Bot(TOKEN)
dp = Dispatcher()

class SearchState(StatesGroup):
    waiting_for_input = State()
    waiting_for_news_keyword = State()
#=======================================API

TRACE_MOE_API = "https://api.trace.moe/search?url="
ANILIST_API = "https://graphql.anilist.co"
NYT_API = NYT_API_KEY


#===============================================HENDLERS
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📰 Новости"), KeyboardButton(text="⛩️ Аниме")],
        [KeyboardButton(text="🐶 Собачки")]
    ],
    resize_keyboard=True
)
#=================================================keyboard
@dp.message(CommandStart())
async def start_mess(message : Message):
    message.answer(
        "<b>Hi! I'm bot for some tasks</b>\n"
        "Check my COMMANDS:"
        "\n"
        ""
        

        , parse_mode="HTML")


@dp.message(Command("shot"))
async def cmd_shot(message: Message, state: FSMContext):
    await state.set_state(SearchState.waiting_for_input)
    await message.answer(
        "📸 **Отправьте скриншот** (картинку) или **ссылку (URL)** на изображение:"
    )

@dp.message(Command("news"))
async def cmd_news(message: Message, state: FSMContext):
    # Переводим пользователя в состояние ожидания ключевого слова
    await state.set_state(SearchState.waiting_for_news_keyword)
    await message.answer(
        "📰 **Поиск новостей The New York Times**\n\n"
        "Введите ключевое слово или фразу для поиска (на английском языке, например: `AI`, `Space`, `Technology`):",
        parse_mode="Markdown"
    )

@dp.message(Command("dog"))
async def cmd_dog(message: Message):
    status_msg = await message.answer("🐶 Ищу милого пёсика...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://dog.ceo/api/breeds/image/random") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    dog_image_url = data.get("message")

                    await status_msg.delete()
                    await message.answer_photo(
                        photo=dog_image_url,
                        caption="🐶 **Вот твой случайный пёсик!**\n\n_Напиши /dog, чтобы получить ещё одного._",
                        parse_mode="Markdown"
                    )
                else:
                    await status_msg.edit_text("❌ Не удалось загрузить пёсика, попробуй позже.")
        except Exception as e:
            logging.error(f"Ошибка Dog API: {e}")
            await status_msg.edit_text("⚠️ Произошла ошибка при запросе к Dog API.")

@dp.message(SearchState.waiting_for_news_keyword, F.text)
async def process_news_search(message: Message, state: FSMContext):
    if message.text:
        keyword = message.text.strip()
    status_msg = await message.answer(f"🔎 Ищу свежие новости по запросу «{keyword}»...")
    
    # Сбрасываем состояние
    await state.clear()

    params = {
        "q": keyword,
        "api-key": NYT_API_KEY,
        "sort": "newest"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(NYT_SEARCH_URL, params=params) as resp:
                if resp.status != 200:
                    await status_msg.edit_text("❌ Ошибка при обращении к сервису новостей.")
                    return

                data = await resp.json()
                docs = data.get("response", {}).get("docs", [])

                if not docs:
                    await status_msg.edit_text(f"😔 По запросу «{keyword}» ничего не найдено.")
                    return

                articles_text = f"📰 **Топ новостей по запросу «{keyword}»:**\n\n"
                
                for idx, doc in enumerate(docs[:5], 1):
                    headline = doc.get("headline", {}).get("main", "Без названия")
                    snippet = doc.get("snippet", "Описание отсутствует.")
                    web_url = doc.get("web_url", "")
                    pub_date = doc.get("pub_date", "")[:10]

                    articles_text += (
                        f"**{idx}. [{headline}]({web_url})**\n"
                        f"📅 _{pub_date}_\n"
                        f"📝 {snippet}\n\n"
                    )

                await status_msg.edit_text(
                    articles_text,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )

        except Exception as e:
            logging.error(f"Ошибка при поиске новостей: {e}")
            await status_msg.edit_text("⚠️ Произошла ошибка при загрузке новостей.")

#==========================================FUNCTIONS
def log_action(user_id: int, username: str, motion: str, api_name: str, api_answer: str):
    file_exists = os.path.isfile(LOG_FILE)
    
    
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    tg_nick = f"@{username}" if username else "NONE"
    
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        
        if not file_exists:
            writer.writerow(["Unic_ID", "@TG_nick", "Motion", "API", "Date", "Time", "API_answer"])
        
        writer.writerow([user_id, tg_nick, motion, api_name, date_str, time_str, api_answer])


async def fetch_anilist_data(session: aiohttp.ClientSession, anilist_id: int):
    try:
        async with session.post(
            ANILIST_API,
            json={'query': ANILIST_QUERY, 'variables': {'id': anilist_id}}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get('data', {}).get('Media', {})
    except Exception as e:
        logging.error(f"Ошибка при запросе к AniList: {e}")
    return {}



def clean_html(raw_html: str) -> str:
    if not raw_html:
        return "Описание отсутствует."
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext[:350] + "..." if len(cleantext) > 350 else cleantext

async def process_anime_search(message: Message, image_url: str, state: FSMContext):
    status_msg = await message.answer("🔍 Ищу кадр и собираю информацию об аниме...")
    await state.clear()

    async with aiohttp.ClientSession() as session:
        try:
            # 1. Запрос к Trace Moe
            async with session.get(f"{TRACE_MOE_API}{image_url}") as response:
                if response.status != 200:
                    await status_msg.edit_text("❌ Ошибка при запросе к сервису поиска.")
                    return
                data = await response.json()

            results = data.get("result", [])
            if not results:
                await status_msg.edit_text("😔 К сожалению, совпадений не найдено.")
                return

            best_match = results[0]
            similarity = round(best_match["similarity"] * 100, 1)
            episode = best_match.get("episode", "1")
            anilist_id = best_match.get("anilist")
            video_url = best_match.get("video")  # URL короткого видео отрывка

            # Таймкод
            from_sec = int(best_match["from"])
            from_time = f"{from_sec // 60:02d}:{from_sec % 60:02d}"

            # 2. Запрос к AniList за деталями
            media = await fetch_anilist_data(session, anilist_id)

            titles = media.get("title", {})
            title_jp = titles.get("native", "—")
            title_en = titles.get("english") or titles.get("romaji") or "—"
            
            # Жанры, рейтинг и описание
            genres = ", ".join(media.get("genres", ["Не указано"]))
            score = media.get("averageScore")
            score_str = f"{score} / 100 ⭐️" if score else "Нет оценки"
            description = clean_html(media.get("description", ""))

            caption = (
                f"🎬 **Результат поиска ({similarity}% совпадения):**\n\n"
                f"🇯🇵 **Японское название:** {title_jp}\n"
                f"🇬🇧 **Английское/Ромадзи:** {title_en}\n\n"
                f"🎞 **Серия:** {episode} | ⏱ **Таймкод:** ~{from_time}\n"
                f"⭐ **Рейтинг:** {score_str}\n"
                f"🏷 **Жанры:** {genres}\n\n"
                f"📝 **Описание:**\n_{description}_\n\n"
                f"💡 _Для нового поиска введите /shot_"
            )

            # 3. Отправляем короткое видео отрывка
            if video_url:
                await status_msg.delete()
                await message.answer_video(
                    video=video_url,
                    caption=caption,
                    parse_mode="Markdown"
                )
            else:
                await status_msg.edit_text(caption, parse_mode="Markdown")

        except Exception as e:
            logging.error(f"Ошибка при обработке: {e}")
            await status_msg.edit_text("⚠️ Произошла ошибка при обработке.")


@dp.message(SearchState.waiting_for_input, F.photo)
async def handle_photo_input(message: Message, state: FSMContext):
    if message.photo:
        photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    await process_anime_search(message, file_url, state)



@dp.message(SearchState.waiting_for_input, F.text)
async def handle_text_input(message: Message, state: FSMContext):
    if message.text:
        url = message.text.strip()
    if url.startswith("http://") or url.startswith("https://"):
        await process_anime_search(message, url, state)
    else:
        await message.answer("⚠️ Это не похоже на ссылку. Отправьте валидный URL (начинающийся с http:// или https://) или загрузите картинку.")


