"""
Работа с базой данных SQLite
"""

import sqlite3



class Database:
    """
    Класс для работы с базой данных.
    Использует SQLite
    """

    def __init__(self, db_name="english_words.db"):
        """
        Инициализация базы данных.
        """
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_tables()
        self.add_common_words()

        print(f"База данных подключена: {db_name}")

    def create_tables(self):
        """
        Создаём таблицы в базе данных.
        """

        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица слов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english TEXT NOT NULL,
                russian TEXT NOT NULL,
                is_common BOOLEAN DEFAULT 1,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица связи пользователей и слов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                word_id INTEGER NOT NULL,
                correct_answers INTEGER DEFAULT 0,
                wrong_answers INTEGER DEFAULT 0, 
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (word_id) REFERENCES words(id),
                UNIQUE(user_id, word_id)
            )
        ''')

        self.connection.commit()

    def add_common_words(self):
        """
        Добавляем общие слова для всех пользователей.
        """

        common_words = [
            ("red", "красный"),
            ("blue", "синий"),
            ("green", "зелёный"),
            ("yellow", "жёлтый"),
            ("black", "чёрный"),
            ("white", "белый"),
            ("I", "я"),
            ("you", "ты"),
            ("he", "он"),
            ("she", "она"),
            ("it", "оно"),
            ("we", "мы"),
            ("they", "они")
        ]

        # Проверяем, есть ли уже общие слова
        self.cursor.execute("SELECT COUNT(*) FROM words WHERE is_common = 1")
        count = self.cursor.fetchone()[0]

        # Если общих слов нет - добавляем
        if count == 0:
            for english, russian in common_words:
                self.cursor.execute(
                    "INSERT INTO words (english, russian, is_common) VALUES (?, ?, 1)",
                    (english, russian)
                )

            self.connection.commit()
            print(f"✅ Добавлено {len(common_words)} общих слов")

    def add_user(self, telegram_id, username, first_name):
        """
        Добавляем пользователя в базу.

        Параметры:
        telegram_id - ID пользователя в Telegram
        username - имя пользователя (например, @username)
        first_name - имя пользователя в профиле Telegram

        Возвращает:
        ID пользователя в нашей базе
        """
        try:
            # Добавляем пользователя (если ещё нет)
            self.cursor.execute(
                "INSERT OR IGNORE INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
                (telegram_id, username, first_name)
            )
            self.connection.commit()

            # Получаем ID пользователя
            self.cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            user_id = self.cursor.fetchone()[0]

            # Добавляем все общие слова для этого пользователя
            self.cursor.execute("SELECT id FROM words WHERE is_common = 1")
            common_words = self.cursor.fetchall()

            for word in common_words:
                word_id = word[0]
                try:
                    self.cursor.execute(
                        "INSERT OR IGNORE INTO user_words (user_id, word_id) VALUES (?, ?)",
                        (user_id, word_id)
                    )
                except:
                    pass  # Если уже есть - пропускаем

            self.connection.commit()
            return user_id

        except Exception as e:
            print(f"❌ Ошибка при добавлении пользователя: {e}")
            return None

    def add_personal_word(self, telegram_id, english, russian):
        """
        Добавляем персональное слово для пользователя.

        Параметры:
        telegram_id
        english - английское слово
        russian - русский перевод

        Возвращает:
        True - если успешно, False - если ошибка
        """
        try:
            self.cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            user = self.cursor.fetchone()

            if not user:
                return False

            user_id = user[0]

            # Добавляем слово (персональное, is_common = 0)
            self.cursor.execute(
                "INSERT INTO words (english, russian, is_common, created_by) VALUES (?, ?, 0, ?)",
                (english.lower(), russian.lower(), user_id)
            )
            word_id = self.cursor.lastrowid

            # Связываем слово с пользователем
            self.cursor.execute(
                "INSERT INTO user_words (user_id, word_id) VALUES (?, ?)",
                (user_id, word_id)
            )

            self.connection.commit()
            return True

        except Exception as e:
            print(f"❌ Ошибка при добавлении слова: {e}")
            return False

    def get_random_word(self, telegram_id):
        """
        Получаем случайное слово для пользователя.

        Параметры:
        telegram_id

        Возвращает:
        Словарь с информацией о слове или None
        """
        try:
            self.cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            user = self.cursor.fetchone()

            if not user:
                return None

            user_id = user[0]

            # Ищем активное слово для пользователя (случайное)
            self.cursor.execute('''
                SELECT w.id, w.english, w.russian 
                FROM words w
                JOIN user_words uw ON w.id = uw.word_id
                WHERE uw.user_id = ? AND uw.is_active = 1
                ORDER BY RANDOM()
                LIMIT 1
            ''', (user_id,))

            word = self.cursor.fetchone()

            if word:
                return {
                    "id": word[0],
                    "english": word[1],
                    "russian": word[2]
                }

            return None

        except Exception as e:
            print(f"❌ Ошибка при получении слова: {e}")
            return None

    def get_wrong_answers(self, correct_word_id, limit=3):
        """
        Получаем неправильные варианты ответов.

        Параметры:
        correct_word_id - ID правильного слова
        limit - сколько неправильных вариантов нужно

        Возвращает:
        Список английских слов (неправильные варианты)
        """
        try:
            self.cursor.execute('''
                SELECT english FROM words 
                WHERE id != ? AND is_common = 1 
                ORDER BY RANDOM() 
                LIMIT ?
            ''', (correct_word_id, limit))

            wrong_words = self.cursor.fetchall()
            return [word[0] for word in wrong_words]

        except Exception as e:
            print(f"❌ Ошибка при получении неправильных ответов: {e}")
            return []

    def get_user_words(self, telegram_id):
        """
        Получаем все активные слова пользователя.

        Параметры:
        telegram_id

        Возвращает:
        Список кортежей (id, english, russian)
        """
        try:
            self.cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            user = self.cursor.fetchone()

            if not user:
                return []

            user_id = user[0]

            # Получаем все активные слова пользователя
            self.cursor.execute('''
                SELECT w.id, w.english, w.russian 
                FROM words w
                JOIN user_words uw ON w.id = uw.word_id
                WHERE uw.user_id = ? AND uw.is_active = 1
                ORDER BY w.russian
            ''', (user_id,))

            return self.cursor.fetchall()

        except Exception as e:
            print(f"❌ Ошибка при получении слов пользователя: {e}")
            return []

    def deactivate_word(self, telegram_id, word_id):
        """
        Деактивируем слово для пользователя (удаляем из обучения).

        Параметры:

        telegram_id
        word_id

        Возвращает:
        True - если успешно, False - если ошибка
        """
        try:
            self.cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            user = self.cursor.fetchone()

            if not user:
                return False

            user_id = user[0]

            # Деактивируем слово
            self.cursor.execute(
                "UPDATE user_words SET is_active = 0 WHERE user_id = ? AND word_id = ?",
                (user_id, word_id)
            )

            self.connection.commit()
            return True

        except Exception as e:
            print(f"❌ Ошибка при удалении слова: {e}")
            return False

    def close(self):
        """Закрываем соединение с базой данных"""
        self.connection.close()
        print("Соединение с базой данных закрыто")