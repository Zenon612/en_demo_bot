"""
Основной класс Telegram бота
"""

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters


class EnglishBot:
    """
    Главный класс бота.
    Собирает все компоненты вместе.
    """

    def __init__(self, token, db, keyboards, handlers):
        """
        Инициализация бота.

        Параметры:
        token - токен
        db - объект базы данных
        keyboards - объект клавиатур
        handlers - объект обработчиков
        """
        self.token = token
        self.db = db
        self.keyboards = keyboards
        self.handlers = handlers

        # Создаём приложение бота
        self.application = Application.builder().token(self.token).build()

        # Настраиваем обработчики
        self.setup_handlers()

    def setup_handlers(self):
        """
        Настройка обработчиков команд и сообщений.
        """

        # Команды бота
        self.application.add_handler(CommandHandler("start", self.handlers.start_command))
        self.application.add_handler(CommandHandler("learn", self.handlers.learn_command))
        self.application.add_handler(CommandHandler("add", self.handlers.add_word_command))
        self.application.add_handler(CommandHandler("remove", self.handlers.remove_word_command))
        self.application.add_handler(CommandHandler("list", self.handlers.list_command))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))

        # Обработчик нажатий на inline-кнопки (варианты ответов, удаление)
        self.application.add_handler(CallbackQueryHandler(self.handlers.button_click))

        # Обработчик текстовых сообщений (кнопки главного меню, добавление через "=")
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_text_message)
        )

        print("Обработчики настроены")

    def run(self):
        """
        Запуск бота.
        """
        print("Бот запускается")

        # Запускаем бота в режиме опроса (polling)
        self.application.run_polling(allowed_updates=None)

    def stop(self):
        """
        Остановка бота.
        Закрываем соединение с базой данных.
        """
        print("\n🛑 Останавливаю бота...")
        self.db.close()