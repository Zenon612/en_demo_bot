"""
Обработчики команд и сообщений бота
"""

import random
import asyncio
from telegram import Update
from telegram.ext import ContextTypes


class Handlers:
    """
    Класс с обработчиками для бота.
    Здесь собраны все функции, которые реагируют на команды и сообщения.
    """

    def __init__(self, db, keyboards):
        """
        Инициализация обработчиков.

        Параметры:
        db - объект базы данных (из database.py)
        keyboards - объект клавиатур (из keyboard.py)
        """
        self.db = db
        self.keyboards = keyboards

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /start.
        Вызывается при первом запуске бота.
        """
        # Получаем информацию о пользователе
        user = update.effective_user # удобный класс для получения информации о пользователе

        # Добавляем пользователя в базу
        user_id = self.db.add_user(user.id, user.username, user.first_name)


        if user_id:
            # Получаем основную клавиатуру
            reply_markup = self.keyboards.get_main_keyboard()

            # Отправляем приветственное сообщение
            await update.message.reply_text(
                f"👋 Привет, {user.first_name}!\n\n"
                f"🤖 Я - бот для изучения английских слов.\n"
                f"📚 У меня уже есть общие слова (цвета и местоимения).\n"
                f"➕ Ты можешь добавлять свои слова.\n\n"
                f"🔸 Используй кнопки ниже или команды:\n"
                f"/learn - начать урок\n"
                f"/add - добавить слово\n"
                f"/remove - удалить слово\n"
                f"/list - список твоих слов\n\n"
                f"🎓 Нажми 'Учить слова', чтобы начать!",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте ещё раз.")

    async def learn_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /learn.
        Начинает урок - показывает слово и варианты перевода.
        """
        await self.ask_word_question(update, context)

    async def ask_word_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Показывает вопрос с 4 вариантами ответа.
        """
        user_id = update.effective_user.id

        # Получаем случайное слово из базы
        word = self.db.get_random_word(user_id)

        # Если слов нет - предлагаем добавить
        if not word:
            await update.message.reply_text(
                "📭 У вас пока нет слов для изучения.\n"
                "Добавьте слова с помощью кнопки '➕ Добавить слово' или команды /add"
            )
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                "📭 У вас пока нет слов для изучения.\n"
                "Добавьте слова с помощью кнопки '➕ Добавить слово' или команды /add"
            )
            return

        # Сохраняем текущее слово в памяти бота (user_data)
        context.user_data['current_word'] = word

        # Получаем 3 неправильных варианта ответа
        wrong_answers = self.db.get_wrong_answers(word['id'], 3)

        # Собираем все варианты: правильный + 3 неправильных
        all_answers = [word['english']] + wrong_answers

        # Перемешиваем варианты
        random.shuffle(all_answers)

        # Создаём клавиатуру с вариантами ответов
        reply_markup = self.keyboards.get_answer_keyboard(all_answers)

        # Проверяем, откуда пришёл запрос и отправляем вопрос
        if update.message:
            # Если вызвано из команды /learn или кнопки "Учить слова"
            await update.message.reply_text(
                f"📖 Как переводится слово:\n\n"
                f"<b>{word['russian']}</b>\n\n"
                f"Выбери правильный вариант:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        elif update.callback_query:
            # Если вызвано после ответа на предыдущий вопрос
            await update.callback_query.message.reply_text(
                f"📖 Как переводится слово:\n\n"
                f"<b>{word['russian']}</b>\n\n"
                f"Выбери правильный вариант:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

    async def button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик нажатий на inline-кнопки (варианты ответов).
        """
        # Получаем информацию о нажатой кнопке
        query = update.callback_query

        # Обязательно отвечаем на callback
        await query.answer()

        # Получаем данные из кнопки
        button_data = query.data

        # Получаем текущее слово из памяти
        current_word = context.user_data.get('current_word')

        if not current_word:
            await query.edit_message_text("❌ Произошла ошибка. Начните урок заново.")
            return

        # Обработка вариантов ответа
        if button_data.startswith("answer_"):
            # Извлекаем ответ пользователя
            user_answer = button_data.replace("answer_", "")
            correct_answer = current_word['english']

            # Проверяем ответ
            if user_answer == correct_answer:
                # Правильный ответ
                await query.edit_message_text(
                    f"✅ <b>Правильно!</b>\n\n"
                    f"{current_word['russian']} = {current_word['english']}\n\n"
                    f"Молодец! 🎉",
                    parse_mode='HTML'
                )

                # Ждём 1 секунду и задаём следующий вопрос
                # Передаём тот же update и context
                await asyncio.sleep(1)


                new_word = self.db.get_random_word(update.effective_user.id)

                if new_word:
                    # Сохраняем новое слово в контексте
                    context.user_data['current_word'] = new_word

                    # Получаем неправильные варианты
                    wrong_answers = self.db.get_wrong_answers(new_word['id'], 3)
                    all_answers = [new_word['english']] + wrong_answers
                    random.shuffle(all_answers)

                    # Создаём клавиатуру
                    reply_markup = self.keyboards.get_answer_keyboard(all_answers)

                    # Отправляем новый вопрос
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=f"📖 Как переводится слово:\n\n<b>{new_word['russian']}</b>\n\nВыбери правильный вариант:",
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )

            else:
                # Неправильный ответ
                await query.edit_message_text(
                    f"❌ <b>Неправильно!</b>\n\n"
                    f"Правильный ответ: <b>{correct_answer}</b>\n"
                    f"Твой ответ: {user_answer}\n\n"
                    f"Попробуй ещё раз это слово:",
                    parse_mode='HTML'
                )

                # Ждём 2 секунды и повторяем то же слово
                await asyncio.sleep(2)

                # Повторяем то же слово, в котором ошибка
                wrong_answers = self.db.get_wrong_answers(current_word['id'], 3)
                all_answers = [current_word['english']] + wrong_answers
                random.shuffle(all_answers)

                reply_markup = self.keyboards.get_answer_keyboard(all_answers)

                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"📖 Как переводится слово:\n\n<b>{current_word['russian']}</b>\n\nВыбери правильный вариант:",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )

        # Обработка кнопок удаления слов
        elif button_data.startswith("delete_"):
            # Извлекаем ID слова для удаления
            word_id = int(button_data.replace("delete_", ""))

            # Деактивируем слово для пользователя
            success = self.db.deactivate_word(update.effective_user.id, word_id)

            if success:
                await query.edit_message_text("✅ Слово удалено из твоих уроков!")
            else:
                await query.edit_message_text("❌ Не удалось удалить слово.")

    async def add_word_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /add.
        Добавление нового слова.

        Формат: /add apple яблоко
        """
        # Проверяем, есть ли аргументы у команды
        if context.args and len(context.args) >= 2:
            english = context.args[0].lower()
            russian = ' '.join(context.args[1:]).lower()

            # Добавляем слово в базу
            success = self.db.add_personal_word(update.effective_user.id, english, russian)

            if success:
                await update.message.reply_text(
                    f"✅ Слово добавлено!\n\n"
                    f"🇬🇧 {english}\n"
                    f"🇷🇺 {russian}\n\n"
                    f"Теперь оно будет в твоих уроках."
                )
            else:
                await update.message.reply_text("❌ Не удалось добавить слово.")
        else:
            # Если аргументов нет - показываем инструкцию
            await update.message.reply_text(
                "📝 Чтобы добавить слово, напиши:\n"
                "<code>/add apple яблоко</code>\n\n"
                "Или просто напиши <code>яблоко = apple</code>",
                parse_mode='HTML'
            )

    async def remove_word_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /remove.
        Показывает список слов для удаления.
        """
        # Получаем все слова пользователя
        user_words = self.db.get_user_words(update.effective_user.id)

        if not user_words:
            await update.message.reply_text("📭 У тебя пока нет слов для удаления.")
            return

        # Создаём клавиатуру для удаления слов
        reply_markup = self.keyboards.get_delete_keyboard(user_words)

        # Отправляем сообщение с кнопками
        await update.message.reply_text(
            "🗑️ Выбери слово для удаления:\n"
            "(Оно исчезнет только из твоих уроков)",
            reply_markup=reply_markup
        )

    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /list.
        Показывает список всех слов пользователя.
        """
        # Получаем слова пользователя
        user_words = self.db.get_user_words(update.effective_user.id)

        if not user_words:
            await update.message.reply_text("📭 У тебя пока нет слов. Добавь их командой /add")
            return

        # Формируем список
        words_list = "📋 Твои слова для изучения:\n\n"

        for i, word in enumerate(user_words, 1):
            word_id, english, russian = word
            words_list += f"{i}. {russian} = {english}\n"

        await update.message.reply_text(words_list)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /help и кнопки "Помощь".
        Показывает справку по боту.
        """
        help_text = """
🤖 <b>Помощь по боту:</b>

<b>Основные команды:</b>
/start - Начало работы
/learn - Начать урок
/add - Добавить слово
/remove - Удалить слово
/list - Список слов
/help - Эта справка

<b>Добавление слов:</b>
1. Через команду: <code>/add apple яблоко</code>
2. Через сообщение: <code>яблоко = apple</code>

<b>Как работает обучение:</b>
1. Бот показывает русское слово
2. Ты выбираешь английский перевод из 4 вариантов
3. Бот проверяет ответ и показывает результат

<b>Удаление слов:</b>
Слова удаляются только из твоих уроков.
Другие пользователи их всё ещё видят.

<b>Общие слова:</b>
У бота уже есть 13 общих слов (цвета и местоимения).
Они доступны всем пользователям.
"""

        await update.message.reply_text(help_text, parse_mode='HTML')

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик текстовых сообщений.
        Обрабатывает кнопки главного меню и добавление слов через "=".
        """
        text = update.message.text

        # Обработка кнопок главного меню
        if text == "🎓 Учить слова":
            await self.ask_word_question(update, context)

        elif text == "➕ Добавить слово":
            await update.message.reply_text(
                "📝 Напиши слово и перевод в формате:\n"
                "<code>яблоко = apple</code>\n\n"
                "Или используй команду: <code>/add apple яблоко</code>",
                parse_mode='HTML'
            )

        elif text == "➖ Удалить слово":
            await self.remove_word_command(update, context)

        elif text == "📋 Мои слова":
            await self.list_command(update, context)

        elif text == "❓ Помощь":
            await self.help_command(update, context)

        # Обработка добавления слова через "="
        elif "=" in text:
            try:
                # Разделяем на русское и английское слово
                parts = text.split("=")
                if len(parts) == 2:
                    russian = parts[0].strip()
                    english = parts[1].strip()

                    # Добавляем слово
                    success = self.db.add_personal_word(update.effective_user.id, english, russian)

                    if success:
                        await update.message.reply_text(
                            f"✅ Слово добавлено!\n\n"
                            f"🇷🇺 {russian}\n"
                            f"🇬🇧 {english}"
                        )
                    else:
                        await update.message.reply_text("❌ Не удалось добавить слово.")
            except Exception as e:
                await update.message.reply_text("❌ Неверный формат. Используй: слово = перевод")

        # Неизвестное сообщение
        else:
            await update.message.reply_text(
                "🤔 Я не понял твоё сообщение.\n"
                "Используй кнопки или команды:\n"
                "/start - начало работы\n"
                "/help - помощь"
            )