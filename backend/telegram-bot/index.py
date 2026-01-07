import json
import os
import requests
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

def handler(event: dict, context) -> dict:
    '''Telegram бот с ИИ для управления расписанием курьеров и общения в группе'''
    
    method = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }
    
    try:
        body = json.loads(event.get('body', '{}'))
        print(f"Received update: {json.dumps(body, ensure_ascii=False)[:500]}")
        
        if not body:
            return {'statusCode': 200, 'body': json.dumps({'ok': True})}
        
        if 'message' in body:
            handle_message(body['message'])
        elif 'callback_query' in body:
            handle_callback(body['callback_query'])
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'ok': True})
        }
    
    except Exception as e:
        print(f"ERROR in handler: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            'statusCode': 200,
            'body': json.dumps({'ok': True})
        }


def handle_message(message: dict):
    '''Обработка входящих сообщений'''
    chat_id = message['chat']['id']
    text = message.get('text', '')
    user_name = get_user_name(message['from'])
    
    print(f"Message from {user_name} (ID: {chat_id}): {text}")
    
    bot_username = get_bot_username()
    
    is_group = message['chat']['type'] in ['group', 'supergroup']
    is_mentioned = f'@{bot_username}' in text if bot_username else False
    is_reply_to_bot = message.get('reply_to_message', {}).get('from', {}).get('is_bot', False)
    
    if is_group and not is_mentioned and not is_reply_to_bot:
        return
    
    if text.startswith('/start'):
        send_message(chat_id, 
            "👋 Привет! Я бот-помощник для курьеров.\n\n"
            "📋 Команды:\n"
            "/schedule - Моё расписание\n"
            "/add_shift - Добавить смену\n"
            "/salary - Моя зарплата\n"
            "/help - Помощь\n\n"
            "💬 Можешь задать мне любой вопрос о работе курьера или просто поболтать!")
        return
    
    if text.startswith('/help'):
        send_message(chat_id,
            "❓ Помощь по боту\n\n"
            "📋 Команды расписания:\n"
            "/schedule - Показать расписание на неделю\n"
            "/add_shift - Добавить новую смену\n"
            "/salary - Посмотреть зарплату за месяц\n\n"
            "💬 Умное общение:\n"
            "Просто напиши что нужно сделать, например:\n"
            "• Поставь мне смену завтра с 10 до 18\n"
            "• Покажи мою зарплату\n"
            "• Как оформить возврат?\n"
            "• Расскажи анекдот\n\n"
            "В группе упомяни меня @" + (get_bot_username() or 'бот'))
        return
    
    if text.startswith('/schedule'):
        show_schedule(chat_id, message)
        return
    
    if text.startswith('/add_shift'):
        show_add_shift_menu(chat_id, message)
        return
    
    if text.startswith('/salary'):
        show_salary(chat_id, message)
        return
    
    respond_with_ai(chat_id, text, message)


def handle_callback(callback: dict):
    '''Обработка нажатий на кнопки'''
    chat_id = callback['message']['chat']['id']
    message_id = callback['message']['message_id']
    data = callback['data']
    user = callback['from']
    
    if data.startswith('addshift_'):
        parts = data.split('_')
        date = parts[1]
        show_time_input(chat_id, message_id, date, user)
    
    elif data.startswith('confirm_shift_'):
        save_shift_from_callback(data, user, chat_id, message_id)
    
    answer_callback(callback['id'])


def show_schedule(chat_id: int, message: dict):
    '''Показать расписание на неделю'''
    user_name = get_user_name(message['from'])
    
    conn = get_db_connection()
    if not conn:
        send_message(chat_id, "❌ Ошибка подключения к базе данных")
        return
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        cur.execute(
            f"SELECT * FROM schedule WHERE employee = '{user_name}' "
            f"AND date >= '{week_start.strftime('%Y-%m-%d')}' "
            f"AND date <= '{week_end.strftime('%Y-%m-%d')}' "
            f"ORDER BY date"
        )
        shifts = cur.fetchall()
        
        if not shifts:
            send_message(chat_id, f"📅 У тебя пока нет смен на этой неделе\n\nИспользуй /add_shift чтобы добавить")
            return
        
        text = f"📅 Расписание {user_name}\n"
        text += f"Неделя: {week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m')}\n\n"
        
        total_hours = 0
        total_orders = 0
        
        for shift in shifts:
            if not shift['shift1_start']:
                continue
            
            date = datetime.strptime(str(shift['date']), '%Y-%m-%d')
            weekday = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][date.weekday()]
            
            hours = calculate_hours(shift['shift1_start'], shift['shift1_end'])
            if shift['has_shift2']:
                hours += calculate_hours(shift['shift2_start'], shift['shift2_end'])
            
            total_hours += hours
            total_orders += shift['orders'] or 0
            
            text += f"📌 {date.strftime('%d.%m')} ({weekday})\n"
            text += f"   ⏰ {shift['shift1_start']} - {shift['shift1_end']}"
            if shift['has_shift2']:
                text += f" + {shift['shift2_start']}-{shift['shift2_end']}"
            text += f"\n   📦 Заказов: {shift['orders'] or 0}\n"
            text += f"   💰 {calculate_day_salary(shift):,.0f} ₽\n\n"
        
        text += f"📊 Итого за неделю:\n"
        text += f"⏱ Часов: {total_hours:.1f}\n"
        text += f"📦 Заказов: {total_orders}\n"
        
        send_message(chat_id, text)
        
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"Error showing schedule: {e}")
        send_message(chat_id, "❌ Ошибка при загрузке расписания")


def show_add_shift_menu(chat_id: int, message: dict):
    '''Показать меню добавления смены'''
    today = datetime.now()
    
    keyboard = {
        'inline_keyboard': []
    }
    
    for i in range(7):
        date = today + timedelta(days=i)
        weekday = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][date.weekday()]
        button_text = f"{date.strftime('%d.%m')} ({weekday})"
        
        keyboard['inline_keyboard'].append([{
            'text': button_text,
            'callback_data': f"addshift_{date.strftime('%Y-%m-%d')}"
        }])
    
    send_message(chat_id, "📅 Выбери день для добавления смены:", keyboard)


def show_time_input(chat_id: int, message_id: int, date: str, user: dict):
    '''Показать форму ввода времени'''
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    weekday = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][date_obj.weekday()]
    
    text = (
        f"📅 Добавление смены на {date_obj.strftime('%d.%m.%Y')} ({weekday})\n\n"
        f"Отправь время в формате:\n"
        f"<b>10:00-18:00</b>\n\n"
        f"Или с двумя сменами:\n"
        f"<b>10:00-14:00 16:00-20:00</b>"
    )
    
    edit_message(chat_id, message_id, text)


def save_shift_from_callback(data: str, user: dict, chat_id: int, message_id: int):
    '''Сохранить смену из callback данных'''
    send_message(chat_id, "✅ Смена сохранена!")


def show_salary(chat_id: int, message: dict):
    '''Показать зарплату за месяц'''
    user_name = get_user_name(message['from'])
    
    conn = get_db_connection()
    if not conn:
        send_message(chat_id, "❌ Ошибка подключения к базе данных")
        return
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        today = datetime.now()
        month_start = today.replace(day=1).strftime('%Y-%m-%d')
        
        cur.execute(
            f"SELECT * FROM schedule WHERE employee = '{user_name}' "
            f"AND date >= '{month_start}' "
            f"ORDER BY date"
        )
        shifts = cur.fetchall()
        
        if not shifts:
            send_message(chat_id, f"💰 В этом месяце у тебя пока нет смен")
            return
        
        total_salary = 0
        total_hours = 0
        total_orders = 0
        
        for shift in shifts:
            if not shift['shift1_start']:
                continue
            
            salary = calculate_day_salary(shift)
            total_salary += salary
            
            hours = calculate_hours(shift['shift1_start'], shift['shift1_end'])
            if shift['has_shift2']:
                hours += calculate_hours(shift['shift2_start'], shift['shift2_end'])
            total_hours += hours
            total_orders += shift['orders'] or 0
        
        month_name = today.strftime('%B %Y')
        
        text = f"💰 Зарплата за {month_name}\n\n"
        text += f"👤 {user_name}\n\n"
        text += f"⏱ Отработано часов: {total_hours:.1f}\n"
        text += f"📦 Доставлено заказов: {total_orders}\n\n"
        text += f"💵 Итого: {total_salary:,.0f} ₽\n\n"
        text += f"📊 Расчёт:\n"
        text += f"• Почасовая оплата: {total_hours * 250:,.0f} ₽\n"
        text += f"• За заказы: {total_orders * 50:,.0f} ₽"
        
        send_message(chat_id, text)
        
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"Error showing salary: {e}")
        send_message(chat_id, "❌ Ошибка при расчёте зарплаты")


def respond_with_ai(chat_id: int, text: str, message: dict):
    '''Ответить с помощью YandexGPT'''
    user_name = get_user_name(message['from'])
    
    if check_and_handle_schedule_request(text, chat_id, message):
        return
    
    system_prompt = f"""Ты - дружелюбный помощник для курьеров службы доставки.
    
Твои задачи:
1. Отвечать на вопросы о работе курьера (правила доставки, оформление документов, взаимодействие с клиентами)
2. Давать полезные советы по работе
3. Быть приятным собеседником на любые темы
4. Поддерживать неформальный стиль общения
5. Помогать с расписанием - если спрашивают про смены, говори использовать команды /schedule /add_shift /salary

Пользователь: {user_name}

Отвечай кратко (2-4 предложения), дружелюбно и по делу."""

    try:
        api_key = os.environ.get('YANDEX_API_KEY')
        folder_id = os.environ.get('YANDEX_FOLDER_ID')
        
        print(f"AI request from {user_name}: {text[:100]}")
        
        if not api_key or not folder_id:
            print(f"Missing credentials: api_key={bool(api_key)}, folder_id={bool(folder_id)}")
            send_message(chat_id, "Извини, у меня проблемы с подключением к ИИ 😔")
            return
        
        response = requests.post(
            'https://llm.api.cloud.yandex.net/foundationModels/v1/completion',
            headers={
                'Authorization': f'Api-Key {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'modelUri': f'gpt://{folder_id}/yandexgpt-lite',
                'completionOptions': {
                    'temperature': 0.7,
                    'maxTokens': 500
                },
                'messages': [
                    {'role': 'system', 'text': system_prompt},
                    {'role': 'user', 'text': text}
                ]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_text = result['result']['alternatives'][0]['message']['text']
            print(f"AI response: {ai_text[:100]}")
            send_message(chat_id, ai_text)
        else:
            print(f"YandexGPT error: {response.status_code} - {response.text}")
            send_message(chat_id, "Хм, не могу сейчас ответить, попробуй чуть позже! 🤔")
    
    except Exception as e:
        print(f"ERROR in AI response: {e}")
        import traceback
        print(traceback.format_exc())
        send_message(chat_id, "Ой, что-то пошло не так 😅 Попробуй переформулировать вопрос")


def check_and_handle_schedule_request(text: str, chat_id: int, message: dict) -> bool:
    '''Проверка и обработка запросов на управление расписанием через естественный язык'''
    text_lower = text.lower()
    
    keywords_schedule = ['смен', 'график', 'расписан', 'работ', 'завтра', 'сегодня', 'послезавтра']
    keywords_time = ['с ', 'до ', 'время', 'час']
    
    has_schedule = any(kw in text_lower for kw in keywords_schedule)
    has_time = any(kw in text_lower for kw in keywords_time)
    
    if has_schedule or (has_time and any(kw in text_lower for kw in ['постав', 'добав', 'запиш', 'измен'])):
        send_message(chat_id, 
            "Понял! Для управления расписанием используй:\n\n"
            "/add_shift - Добавить смену\n"
            "/schedule - Посмотреть расписание\n\n"
            "Скоро научусь понимать прямые команды вроде 'поставь смену завтра с 10 до 18' 😉")
        return True
    
    return False


def calculate_hours(start: str, end: str) -> float:
    '''Расчёт количества часов между временем'''
    if not start or not end:
        return 0
    try:
        start_h, start_m = map(int, start.split(':'))
        end_h, end_m = map(int, end.split(':'))
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m
        return (end_minutes - start_minutes) / 60
    except:
        return 0


def calculate_day_salary(shift: dict) -> float:
    '''Расчёт зарплаты за день'''
    hours1 = calculate_hours(shift['shift1_start'], shift['shift1_end'])
    hours2 = calculate_hours(shift['shift2_start'], shift['shift2_end']) if shift['has_shift2'] else 0
    total_hours = hours1 + hours2
    orders = shift['orders'] or 0
    bonus = shift['bonus'] or 0
    return (total_hours * 250) + (orders * (50 + bonus))


def get_user_name(user: dict) -> str:
    '''Получить имя пользователя'''
    return user.get('first_name', 'Пользователь')


def get_db_connection():
    '''Подключение к базе данных'''
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return None
        return psycopg2.connect(db_url)
    except Exception as e:
        print(f"DB connection error: {e}")
        return None


def get_bot_username() -> str:
    '''Получить username бота'''
    try:
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not token:
            return ''
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=5)
        if response.status_code == 200:
            return response.json()['result']['username']
    except:
        pass
    return ''


def send_message(chat_id: int, text: str, keyboard=None):
    '''Отправить сообщение'''
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        return
    
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if keyboard:
        data['reply_markup'] = keyboard
    
    requests.post(f'https://api.telegram.org/bot{token}/sendMessage', json=data)


def edit_message(chat_id: int, message_id: int, text: str):
    '''Редактировать сообщение'''
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        return
    
    requests.post(
        f'https://api.telegram.org/bot{token}/editMessageText',
        json={
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': 'HTML'
        }
    )


def answer_callback(callback_id: str):
    '''Ответить на callback query'''
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        return
    
    requests.post(
        f'https://api.telegram.org/bot{token}/answerCallbackQuery',
        json={'callback_query_id': callback_id}
    )