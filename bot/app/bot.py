import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo

from app.config import settings


dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message) -> None:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='Открыть FitMiniApp', web_app=WebAppInfo(url=f'{settings.frontend_base_url}/app'))]],
        resize_keyboard=True,
    )
    await message.answer('Открой Mini App кнопкой ниже.', reply_markup=keyboard)


@dp.message(F.text == 'Помощь')
async def help_text(message: Message) -> None:
    await message.answer('Используй /start, чтобы открыть Mini App.')


async def main() -> None:
    if not settings.bot_token or settings.bot_token == 'replace-me':
        print('BOT_TOKEN not configured - bot is idle')
        while True:
            await asyncio.sleep(3600)
    bot = Bot(settings.bot_token)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
