"""
Создание клавиатур и кнопок для бота
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


class Keyboards:
    """
    Класс для создания клавиатур бота.
    Все клавиатуры собраны здесь для удобства.
    """

    @staticmethod
    def get_main_keyboard():
        """
        Основная клавиатура под полем ввода.

        Возвращает:
        ReplyKeyboardMarkup - клавиатура с основными кнопками
        """
        # Создаём кнопки
        keyboard = [
            [KeyboardButton("🎓 Учить слова")],
            [KeyboardButton("➕ Добавить слово"), KeyboardButton("➖ Удалить слово")],
            [KeyboardButton("📋 Мои слова"), KeyboardButton("❓ Помощь")]
        ]

        # Создаём разметку клавиатуры
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def get_answer_keyboard(answers):
        """
        Клавиатура с вариантами ответов (под сообщением).

        Параметры:
        answers - список вариантов ответов (английские слова)

        Возвращает:
        InlineKeyboardMarkup - клавиатура с вариантами ответов
        """
        buttons = []

        for answer in answers:
            # Каждая кнопка содержит текст (ответ) и callback_data для обработки
            buttons.append([
                InlineKeyboardButton(answer, callback_data=f"answer_{answer}")
            ])

        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def get_delete_keyboard(words_list):
        """
        Клавиатура для удаления слов.

        Параметры:
        words_list - список слов пользователя [(id, english, russian), ...]

        Возвращает:
        InlineKeyboardMarkup - клавиатура со словами для удаления
        """
        buttons = []

        for word in words_list[:10]:  # Показываем не более 10 слов
            word_id, english, russian = word

            # Обрезаем длинные слова для отображения на кнопке
            if len(russian) > 15:
                display_text = f"{russian[:15]}... ({english[:10]}...)"
            else:
                display_text = f"{russian} ({english})"

            # Кнопка для удаления конкретного слова
            buttons.append([
                InlineKeyboardButton(
                    f"❌ {display_text}",
                    callback_data=f"delete_{word_id}"
                )
            ])

        return InlineKeyboardMarkup(buttons)