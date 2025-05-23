import asyncio
import json
import os
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from matplotlib.pylab import set_state
from config import TOKEN

# --- ИНИЦИАЛИЗАЦИЯ БОТА ---
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КОНФИГУРАЦИЯ ---
ADMIN_IDS = [(5247307710), (1318179688)]
DATA_FILE = 'storage.json'

# --- FSM СОСТОЯНИЯ ---
class Onboarding(StatesGroup):
    goal = State()
    reminder = State()

class DailyCheckin(StatesGroup):
    mood = State()
    concerns = State()

class ValuesTest(StatesGroup):
    question = State()

class Broadcast(StatesGroup):
    message = State()

class Cleanup(StatesGroup):
    user_id = State()

# --- КРИЗИСНЫЕ РЕСУРСЫ ---
CRISIS_KEYWORDS = [
    'суицид', 'самоубийство', 'одиночество', 'депрессия', 'тоска', 'беспокойство', 
    'паника', 'страх', 'безысходность', 'отчаяние', 'помоги', 'не хочу жить', 
    'кризис', 'разочарование', 'горе', 'печаль', 'тревога', 'боль', 
    'потеря', 'развод', 'конец света', 'безысходность', 'самоубийство мысли',
    'жить не хочу', 'сильная грусть', 'безнадега', 'отчаяние',
    'помогите мне', 'я не справляюсь', 'мне плохо'
]
CRISIS_RESOURCES = {
    'lines': [
        '+7 800 7000 600 (Россия, круглосуточно)',
        '+1-800-273-8255 (США, круглосуточно)'
    ],
    'therapists': [
        'https://www.7cups.com',
        'https://betterhelp.com'
    ],
    'articles': [
        'https://www.who.int/ru/news-room/fact-sheets/detail/mental-health',
        'https://www.psychologytoday.com'
    ]
}

# --- УТИЛИТЫ ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def ensure_user(uid: int):
    data = load_data()
    if str(uid) not in data:
        data[str(uid)] = {
            'goal': None, 'reminder': None,
            'last_checkin': None, 'mood_history': [],
            'values_answers': []
        }
        save_data(data)
    return data

# --- КОНТЕНТ ---
BREATHING = [
    "4-7-8 дыхание: вдох 4с, задержка 7с, выдох 8с ×5 циклов.",
    "Квадратное дыхание: вдох-4с, задержка-4с, выдох-4с, пауза-4с ×4."
]
MEDITATIONS = [
    "3-минутная осознанность: наблюдайте за дыханием.",
    "Благодарность: вспоминайте 3 вещи, за которые благодарны."
]
AFFIRMATIONS = [
    "Я достоин любви и заботы.",
    "Каждый день я расту и развиваюсь.",
    "Мои мысли под моим контролем.",
    "Я принимаю себя таким, какой я есть."
]
RESOURCES = {
    'music': ['https://vk.com/music/album/-2000054706_21054706_c1090c02460faa9780', 'https://vk.com/music/album/-2000967097_23967097_fe5eeaccdb29c1ba4c'],
    'podcasts': ['https://podcasts.apple.com/podcast/id123456', 'https://vk.com/audio_playlist/-1_987654321'],
    'prompts': [
        'Опишите три хорошие вещи, случившиеся сегодня.',
        'Что бы вы хотели улучшить в себе?',
        'Какие ваши достижения вы цените больше всего?'
    ]
}
ETHICS = {
    'Утилитаризм': 'Действие правильно, если приносит наибольшее благо большинству.',
    'Деонтология': 'Следуйте моральным правилам вне зависимости от контекста.',
    'Этика добродетелей': 'Фокус на развитии благородных черт характера.'
}
VALUES_Q = [
    'Что для вас является наибольшей ценностью в жизни?',
    'Каким вы видите своё идеальное завтра?',
    'Какое достижение вы считаете своим главным?'
]
STAR = (
    '🧩 *STAR-метод*:\n'
    '*S*ituation — опишите ситуацию.\n'
    '*T*ask — сформулируйте задачу.\n'
    '*A*ction — какие действия возможны?\n'
    '*R*esult — возможные результаты. '
)

# --- ДИЗАЙН: Inline клавиатуры ---
def main_menu(is_admin=False):
    buttons = [
        [
            InlineKeyboardButton(text='❤️ Поддержка', callback_data='support'),
            InlineKeyboardButton(text='⚖️ Этика', callback_data='ethics')
        ],
        [
            InlineKeyboardButton(text='🧠 Саморефлексия', callback_data='reflect'),
            InlineKeyboardButton(text='⚠️ Экстренная', callback_data='emergency')
        ],
        [InlineKeyboardButton(text='📊 Тренды', callback_data='trends')],
        [InlineKeyboardButton(text='📝 Чек-ин', callback_data='checkin')]
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton(text='🔧 Admin', callback_data='admin')])
    return InlineKeyboardMarkup(inline_keyboard=buttons, row_width=2)

support_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='🌬️ Дыхание', callback_data='breath'),
            InlineKeyboardButton(text='🧘 Медитация', callback_data='meditate')
        ],
        [
            InlineKeyboardButton(text='✨ Аффирмации', callback_data='affirm'),
            InlineKeyboardButton(text='📚 Ресурсы', callback_data='resources')
        ],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back')]
])

ethics_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='🧩 STAR', callback_data='star'),
            InlineKeyboardButton(text='📘 Теории', callback_data='theories')
        ],
        [
            InlineKeyboardButton(text='💡 Ценности', callback_data='values'),
            InlineKeyboardButton(text='🔙 Назад', callback_data='back')
        ]
    ]
)

crisis_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Горячие линии', callback_data='cr_lines')],
        [InlineKeyboardButton(text='Онлайн-терапевты', callback_data='cr_therapists')],
        [InlineKeyboardButton(text='Статьи', callback_data='cr_articles')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back')]
    ]
)

# --- Обработчики ---

@dp.message(CommandStart())
async def on_start(msg: Message, state: FSMContext):
    ensure_user(msg.from_user.id)
    is_admin = msg.from_user.id in ADMIN_IDS
    welcome_text = (
        "👋 *Добро пожаловать!* \n\n"
        "Я — ваш личный помощник для проведения чек-инов, тестов ценностей и получения поддержки.\n\n"
        "Вот что я могу для вас сделать:\n"
        "🔹 Провести чек-ин и отслеживать ваше настроение.\n"
        "🔹 Помочь пройти тесты ценностей.\n"
        "🔹 Предоставить полезные ресурсы и контакты.\n"
        "🔹 Отправлять напоминания и новости.\n\n"
        "Чтобы начать работу:\n"
        "1. Выберите нужную функцию из меню ниже или используйте команды:\n"
        "/help — получить помощь\n"
        "/menu — главное меню\n\n"
        "Если у вас есть вопросы или нужна поддержка — пишите мне!"
    )
    # Отправляем сообщение и сохраняем его id для редактирования
    msg_obj = await msg.answer(welcome_text, parse_mode='Markdown', reply_markup=main_menu(is_admin))
    await state.set_data({'main_msg_id': msg_obj.message_id})

@dp.callback_query(F.data == 'support')
async def cb_support(cq: types.CallbackQuery):
    await cq.message.edit_text('🛠️ *Эмоциональная поддержка:*', parse_mode='Markdown', reply_markup=support_kb)

@dp.callback_query(F.data == 'ethics')
async def cb_ethics(cq: types.CallbackQuery):
    await cq.message.edit_text('⚖️ *Этические вопросы:*', parse_mode='Markdown', reply_markup=ethics_kb)

@dp.callback_query(F.data == 'reflect')
async def cb_reflect(cq: types.CallbackQuery):
    # Обновляем сообщение с кнопками
    await cq.message.edit_text('🧠 *Саморефлексия*\nНажмите кнопку Чек-ин.', parse_mode='Markdown', reply_markup=main_menu(cq.from_user.id in ADMIN_IDS))

@dp.callback_query(F.data == 'trends')
async def cb_trends(cq: types.CallbackQuery):
    data = load_data().get(str(cq.from_user.id), {}).get('mood_history', [])
    if not data:
        text = '📈 Среднее за 7 дней: 0/10'
    else:
        avg_mood = sum(int(h["mood"]) for h in data[-7:]) / len(data[-7:])
        text = f'📈 Среднее за 7 дней: {avg_mood:.1f}/10'
    await cq.message.edit_text(text, reply_markup=main_menu(cq.from_user.id in ADMIN_IDS))

@dp.callback_query(F.data == 'emergency')
async def cb_emergency(cq: types.CallbackQuery):
    await cq.message.edit_text('⚠️ *Экстренная помощь*', parse_mode='Markdown', reply_markup=crisis_kb)

@dp.callback_query(F.data.startswith('cr_'))
async def cb_crisis(cq: types.CallbackQuery):
    key = cq.data.split('_',1)[1]
    items = CRISIS_RESOURCES.get(key, [])
    text = f'*{key.title().replace("_", " ")}:*\n' + '\n'.join(f'- {i}' for i in items)
    await cq.message.edit_text(text, parse_mode='Markdown', reply_markup=crisis_kb)

@dp.callback_query(F.data == 'back')
async def cb_back(cq: types.CallbackQuery):
    await cq.message.edit_text('🏠 *Главное меню*', parse_mode='Markdown', reply_markup=main_menu(cq.from_user.id in ADMIN_IDS))

@dp.callback_query(F.data == 'checkin')
async def cb_checkin(cq: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущее сообщение и создаем новое
    await cq.message.delete()
    msg_obj = await cq.message.answer('📅 Оцените настроение сегодня (1–10):')
    # Сохраняем message_id для редактирования
    await state.set_data({'main_msg_id': msg_obj.message_id})
    await state.set_state(DailyCheckin.mood)

@dp.message(DailyCheckin.mood, F.text)
async def ai_mood(msg: Message, state: FSMContext):
    try:
        m = int(msg.text)
        assert 1 <= m <= 10
    except:
        return await msg.answer('Введите число 1–10')
    await state.update_data(mood=m)
    data = load_data()
    uid = str(msg.from_user.id)
    data.setdefault(uid, {}).setdefault('mood_history', []).append({'date': datetime.now().isoformat(), 'mood': m})
    save_data(data)
    # Обновляем сообщение, чтобы показать, что чек-ин завершен
    user_data = await state.get_data()
    msg_id = user_data.get('main_msg_id')
    if msg_id:
        # Редактируем сообщение, добавляя ответ и кнопки
        await msg.bot.edit_message_text(
            chat_id=msg.chat.id,
            message_id=msg_id,
            text=f'✔️ Настроение: {m}/10\nБеспокойства: (можете ввести)',
            reply_markup=main_menu(msg.from_user.id in ADMIN_IDS)
        )
    else:
        await msg.answer(f'✔️ Настроение: {m}/10', reply_markup=main_menu(msg.from_user.id in ADMIN_IDS))
    await state.clear()

@dp.message(F.text)
async def crisis_detection(msg: Message):
    """Проверка всех текстовых сообщений на кризисные ключевые слова"""
    text = msg.text.lower()
    detected = [kw for kw in CRISIS_KEYWORDS if kw in text]
    if detected:
        # Отправляем ресурсы помощи
        await msg.answer(
            "🚨 Замечены слова, которые могут указывать на кризисное состояние. "
            "Вот ресурсы, которые могут помочь:",
            reply_markup=crisis_kb
        )
        # Уведомление админов
        for admin_id in ADMIN_IDS:
            await bot.send_message(
                admin_id,
                f"⚠️ Кризисное сообщение от {msg.from_user.id}:\n"
                f"Текст: {msg.text}\n"
                f"Обнаружены ключи: {', '.join(detected)}"
            )

@dp.message(DailyCheckin.concerns)
async def ai_concerns(msg: Message, state: FSMContext):
    data = await state.get_data()
    concern = msg.text if msg.text.lower() != 'пропустить' else 'Пропущено'
    uid = str(msg.from_user.id)
    db = load_data()
    db.setdefault(uid, {})['last_checkin'] = datetime.now().isoformat()
    save_data(db)
    user_data = await state.get_data()
    msg_id = user_data.get('main_msg_id')
    if msg_id:
        await msg.bot.edit_message_text(
            chat_id=msg.chat.id,
            message_id=msg_id,
            text=f'✔️ Настроение: {user_data.get("mood")}/10\nБеспокойства: {concern}',
            reply_markup=main_menu(msg.from_user.id in ADMIN_IDS)
        )
    else:
        await msg.answer(f'✔️ Настроение: {user_data.get("mood")}/10\nБеспокойства: {concern}', reply_markup=main_menu(msg.from_user.id in ADMIN_IDS))
    await state.clear()

@dp.callback_query(F.data == 'breath')
async def cb_breath(cq: types.CallbackQuery):
    await cq.message.edit_text(random.choice(BREATHING), reply_markup=main_menu(cq.from_user.id in ADMIN_IDS))

@dp.callback_query(F.data == 'meditate')
async def cb_meditate(cq: types.CallbackQuery):
    await cq.message.edit_text(random.choice(MEDITATIONS), reply_markup=main_menu(cq.from_user.id in ADMIN_IDS))

@dp.callback_query(F.data == 'affirm')
async def cb_affirm(cq: types.CallbackQuery):
    await cq.message.edit_text(random.choice(AFFIRMATIONS), reply_markup=main_menu(cq.from_user.id in ADMIN_IDS))

@dp.callback_query(F.data == 'resources')
async def cb_resources(cq: types.CallbackQuery):
    text = '*Музыка:*\n' + '\n'.join(RESOURCES['music']) + \
          '\n\n*Подкасты:*\n' + '\n'.join(RESOURCES['podcasts']) + \
          '\n\n*Промпты:*\n' + '\n'.join(RESOURCES['prompts'])
    await cq.message.edit_text(text, parse_mode='Markdown', reply_markup=main_menu(cq.from_user.id in ADMIN_IDS))

@dp.callback_query(F.data == 'star')
async def cb_star(cq: types.CallbackQuery):
    await cq.message.edit_text(STAR, parse_mode='Markdown', reply_markup=main_menu(cq.from_user.id in ADMIN_IDS))

@dp.callback_query(F.data == 'theories')
async def cb_theories(cq: types.CallbackQuery):
    for name, desc in ETHICS.items():
        await cq.message.edit_text(f'*{name}* — {desc}', parse_mode='Markdown', reply_markup=main_menu(cq.from_user.id in ADMIN_IDS))

@dp.callback_query(F.data == 'values')
async def cb_values(cq: types.CallbackQuery, state: FSMContext):
    await cq.message.edit_text('🧠 Начинаем тест ценностей; ответьте на вопрос:')
    await state.set_state(ValuesTest.question)
    await state.update_data(idx=0, answers=[])

@dp.message(ValuesTest.question, F.text)
async def ai_values(msg: Message, state: FSMContext):
    data = await state.get_data()
    idx = data['idx']
    answers = data.get('answers', [])
    if idx > 0:
        answers.append(msg.text)
    if idx >= len(VALUES_Q):
        # Сохраняем результаты теста ценностей
        uid = str(msg.from_user.id)
        db = load_data()
        db.setdefault(uid, {})['values_answers'] = answers
        save_data(db)
        await msg.answer('✅ Тест завершён. Результаты сохранены.', reply_markup=main_menu(msg.from_user.id in ADMIN_IDS))
        await state.clear()
        return
    await msg.answer(VALUES_Q[idx])
    await state.update_data(idx=idx + 1, answers=answers)

@dp.callback_query(F.data == 'admin')
async def cb_admin(cq: types.CallbackQuery):
    if cq.from_user.id not in ADMIN_IDS:
        return await cq.answer("🚫 Доступ запрещен", show_alert=True)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📊 Список пользователей', callback_data='users_list')],
        [InlineKeyboardButton(text='📢 Рассылка', callback_data='start_broadcast')],
        [InlineKeyboardButton(text='🧹 Очистка данных', callback_data='start_cleanup')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back')]
    ])
    
    await cq.message.edit_text(
        "🔧 *Админ-панель:*\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.callback_query(F.data == 'users_list')
async def users_list(cq: types.CallbackQuery):
    if cq.from_user.id not in ADMIN_IDS:
        return
    
    data = load_data()
    text = f"👤 Всего пользователей: {len(data)}\n\n" + "\n".join(
        f"▫️ ID: {uid}\n"
        f"Последний чек-ин: {user.get('last_checkin', 'никогда')}\n"
        for uid, user in data.items()
    )
    await cq.message.edit_text(text[:4000] + "\n...")  # Обрезаем если слишком длинное

@dp.callback_query(F.data == 'start_broadcast')
async def start_broadcast(cq: types.CallbackQuery, state: FSMContext):
    if cq.from_user.id not in ADMIN_IDS:
        return
    
    await cq.message.answer("📝 Введите текст для рассылки:")
    await state.set_state(Broadcast.message)
    await cq.answer()

@dp.message(Broadcast.message)
async def process_broadcast(msg: Message, state: FSMContext):
    data = load_data()
    total = len(data)
    success = 0
    
    for uid in data:
        try:
            await bot.send_message(uid, msg.text)
            success += 1
        except Exception as e:
            print(f"Ошибка отправки {uid}: {str(e)}")
    
    await msg.answer(
        f"📤 Результат рассылки:\n"
        f"• Успешно: {success}\n"
        f"• Не удалось: {total - success}"
    )
    await state.clear()

@dp.callback_query(F.data == 'start_cleanup')
async def start_cleanup(cq: types.CallbackQuery, state: FSMContext):
    if cq.from_user.id not in ADMIN_IDS:
        return
    
    await cq.message.answer("🔎 Введите ID пользователя для очистки:")
    await state.set_state(Cleanup.user_id)
    await cq.answer()

@dp.message(Cleanup.user_id)
async def process_cleanup(msg: Message, state: FSMContext):
    uid = msg.text.strip()
    data = load_data()
    
    if uid in data:
        del data[uid]
        save_data(data)
        await msg.answer(f"✅ Данные пользователя {uid} удалены")
    else:
        await msg.answer("❌ Пользователь не найден")
    
    await state.clear()

async def main():
    print("🤖 Бот запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())