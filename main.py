"""
Главный файл для запуска бота
"""

import sys
import os

# Добавляем путь к папке с модулями
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database
from keyboard import Keyboards
from handlers import Handlers
from bot import EnglishBot


def get_token():
    """
    Получаем токен бота.
    Сначала проверяем файл token.txt, потом переменную окружения.
    """

    # Пробуем прочитать из файла (у меня токен в txt файле)
    try:
        with open("token.txt", "r") as file:
            token = file.read().strip()
            if token:
                return token
    except FileNotFoundError:
        pass

    # Или из переменной окружения
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        return token

    print("Токен бота не найден!")

    return None


def main():
    """
    Главная функция программы.
    Создаёт все компоненты и запускает бота.
    """
    print("=" * 50)
    print("Запуск бота")
    print("=" * 50)

    token = get_token()
    if not token:
        return

    try:
        print("\n Создание базы данных")
        db = Database()

        print("Создание клавиатуры")
        keyboards = Keyboards()

        print("Создание обработчиков")
        handlers = Handlers(db, keyboards)

        print("Создание бота")
        bot = EnglishBot(token, db, keyboards, handlers)

        print("\n" + "=" * 50)
        print("Программа запущена")
        print("=" * 50)


        bot.run()

    except KeyboardInterrupt:
        # Пользователь нажал Ctrl+C
        print("\n\n👋 Бот остановлен пользователем")

    except Exception as e:
        print(f"\n\n❌ Ошибка при работе бота: {e}")

    finally:
        try:
            if 'db' in locals():
                db.close()
        except:
            pass


if __name__ == "__main__":
    main()