import sqlite3
import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER,
        daily_streak INTEGER
    )''')
    conn.commit()
    conn.close()

# Получение или создание пользователя
def get_or_create_user(user_id, username):
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    if not user:
        c.execute('INSERT INTO users (user_id, username, balance, daily_streak) VALUES (?, ?, ?, ?)',
                  (user_id, username, 1000, 0))
        conn.commit()
        user = (user_id, username, 1000, 0)
    conn.close()
    return user

# Обновление баланса
def update_balance(user_id, amount):
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# Получение топ-10 игроков
def get_leaderboard():
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT username, balance FROM users ORDER BY balance DESC LIMIT 10')
    leaders = c.fetchall()
    conn.close()
    return leaders

# Создание главного меню
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎰 Слоты", callback_data='slots'),
         InlineKeyboardButton("🎲 Кости", callback_data='dice')],
        [InlineKeyboardButton("❓ Викторина", callback_data='quiz'),
         InlineKeyboardButton("🎁 Ежедневный бонус", callback_data='bonus')],
        [InlineKeyboardButton("🏆 Лидеры", callback_data='leaderboard'),
         InlineKeyboardButton("💰 Баланс", callback_data='balance')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username or "Anonymous")
    await update.message.reply_text(
        f"Добро пожаловать в FunCasino, {user.first_name}! 🎉\n"
        "Ты получил 1000 FunCoins для игры. Выбирай, во что сыграть!",
        reply_markup=main_menu()
    )

# Обработчик кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    user_data = get_or_create_user(user.id, user.username or "Anonymous")
    balance = user_data[2]

    if query.data == 'balance':
        await query.message.reply_text(f"Твой баланс: {balance} FunCoins 💰", reply_markup=main_menu())
    
    elif query.data == 'bonus':
        update_balance(user.id, 100)
        await query.message.reply_text("Ты получил 100 FunCoins за ежедневный вход! 🎁", reply_markup=main_menu())
    
    elif query.data == 'leaderboard':
        leaders = get_leaderboard()
        text = "🏆 Топ-10 игроков:\n"
        for i, (username, bal) in enumerate(leaders, 1):
            text += f"{i}. {username}: {bal} FunCoins\n"
        await query.message.reply_text(text, reply_markup=main_menu())
    
    elif query.data == 'slots':
        if balance < 50:
            await query.message.reply_text("Недостаточно FunCoins! Пополни баланс бонусами.", reply_markup=main_menu())
            return
        update_balance(user.id, -50)
        result = [random.choice(['🍒', '🍋', '⭐']) for _ in range(3)]
        win = result[0] == result[1] == result[2]
        prize = 200 if win else 0
        if win:
            update_balance(user.id, prize)
        text = f"🎰 {result[0]} | {result[1]} | {result[2]}\n"
        text += f"{'Победа! +200 FunCoins!' if win else 'Попробуй снова!'}\n"
        text += f"Баланс: {balance - 50 + prize} FunCoins"
        await query.message.reply_text(text, reply_markup=main_menu())
    
    elif query.data == 'dice':
        if balance < 50:
            await query.message.reply_text("Недостаточно FunCoins! Пополни баланс бонусами.", reply_markup=main_menu())
            return
        update_balance(user.id, -50)
        player = random.randint(1, 6)
        bot = random.randint(1, 6)
        win = player > bot
        prize = 100 if win else 0
        if win:
            update_balance(user.id, prize)
        text = f"🎲 Ты: {player} | Бот: {bot}\n"
        text += f"{'Победа! +100 FunCoins!' if win else 'Попробуй снова!'}\n"
        text += f"Баланс: {balance - 50 + prize} FunCoins"
        await query.message.reply_text(text, reply_markup=main_menu())
    
    elif query.data == 'quiz':
        questions = [
            {"q": "Какой фрукт на слотах самый популярный?", "a": ["🍒 Вишня", "🍋 Лимон", "🍎 Яблоко"], "correct": 0}
        ]
        q = questions[0]
        keyboard = [[InlineKeyboardButton(a, callback_data=f'quiz_{i}')] for i, a in enumerate(q["a"])]
        await query.message.reply_text(q["q"], reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data.startswith('quiz_'):
        answer = int(query.data.split('_')[1])
        prize = 50 if answer == 0 else 0
        update_balance(user.id, prize)
        text = f"{'Правильно! +50 FunCoins!' if prize else 'Неправильно!'}\n"
        text += f"Баланс: {balance + prize} FunCoins"
        await query.message.reply_text(text, reply_markup=main_menu())

# Основная функция
async def main():
    init_db()
    token = os.getenv("7696218265:AAGOiJEmkg2Wo8qL32ZQwfk2i3A3sbwbNEE")
    if not token:
        raise ValueError("BOT_TOKEN not set in environment variables")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
