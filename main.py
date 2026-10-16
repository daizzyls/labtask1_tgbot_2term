import asyncio
import logging

from aiogram.types import BotCommand

from bot import bot, dp


async def set_main_menu(bot):
    main_menu_commands = [
        BotCommand(command="start", description="Запустить бота / Справка"),
        BotCommand(command="shot", description="Найти аниме по кадру"),
        BotCommand(command="news", description="Поиск новостей NYT по слову"),
        BotCommand(command="dog", description="Получить случайного пёсика 🐶"),
    ]
    await bot.set_my_commands(main_menu_commands)


async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Устанавливаем синюю кнопку "Меню" в чате с ботом
    await set_main_menu(bot)
    
    print("Бот успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())