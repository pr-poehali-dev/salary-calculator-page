import json
import os
import requests
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import re

def handler(event: dict, context) -> dict:
    '''Умный Telegram ассистент для курьеров с ИИ и управлением расписанием'''
    
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
    user = message['from']
    user_name = get_user_name(user)
    
    print(f"Message from {user_name} (ID: {chat_id}): {text}")
    
    bot_username = get_bot_username()
    is_group = message['chat']['type'] in ['group', 'supergroup']
    is_mentioned = f'@{bot_username}' in text if bot_username else False
    is_reply_to_bot = message.get('reply_to_message', {}).get('from', {}).get('is_bot', False)
    
    if is_group and not is_mentioned and not is_reply_to_bot:
        return
    
    text = text.replace(f'@{bot_username}', '').strip() if bot_username else text
    
    if text.startswith('/start'):
        employee_name = get_employee_name(user)
        send_message(chat_id, 
            f"👋 Привет, {user_name}!\n"
            f"Я твой личный помощник. Определил тебя как: {employee_name}\n\n"
            "💬 Просто пиши мне что нужно:\n"
            "• «Поставь мне смену завтра с 10 до 18»\n"
            "• «Покажи моё расписание»\n"
            "• «Сколько я заработал?»\n"
            "• «Как оформить возврат?»\n"
            "• «Расскажи анекдот»\n\n"
            "Если определил неправильно - напиши /setname")
        return
    
    if text.startswith('/help'):
        send_message(chat_id,
            "❓ Я — твой умный помощник\n\n"
            "Просто говори что нужно, я пойму:\n\n"
            "📋 Расписание:\n"
            "• «Поставь смену завтра 10-18»\n"
            "• «Добавь мне послезавтра с 9 до 17»\n"
            "• «Моё расписание»\n"
            "• «Сколько я заработал?»\n\n"
            "💬 Общение:\n"
            "• «Как оформить возврат?»\n"
            "• «Что делать если клиента нет?»\n"
            "• «Расскажи что-нибудь»\n\n"
            "⚙️ Команды:\n"
            "/setname - изменить имя в системе")
        return
    
    if text.startswith('/setname'):
        show_name_menu(chat_id, user)
        return
    
    handle_smart_message(chat_id, text, user, message)


def handle_smart_message(chat_id: int, text: str, user: dict, message: dict):
    '''Умная обработка сообщений через ИИ'''
    text_lower = text.lower()
    
    shift_result = parse_shift_request(text, user)
    if shift_result:
        return
    
    if any(word in text_lower for word in ['расписание', 'график', 'смены', 'когда работ', 'мои смены']):
        show_schedule_smart(chat_id, user)
        return
    
    if any(word in text_lower for word in ['зарплата', 'заработ', 'сколько', 'деньги', 'выплата']):
        show_salary_smart(chat_id, user)
        return
    
    respond_with_ai(chat_id, text, user)


def parse_shift_request(text: str, user: dict) -> bool:
    '''Парсинг запроса на добавление смены'''
    text_lower = text.lower()
    
    keywords = ['постав', 'добав', 'запиш', 'смен', 'работа', 'график']
    if not any(kw in text_lower for kw in keywords):
        return False
    
    date_obj = None
    if 'сегодня' in text_lower:
        date_obj = datetime.now()
    elif 'завтра' in text_lower:
        date_obj = datetime.now() + timedelta(days=1)
    elif 'послезавтра' in text_lower:
        date_obj = datetime.now() + timedelta(days=2)
    else:
        date_match = re.search(r'(\d{1,2})[\./](\d{1,2})', text)
        if date_match:
            day, month = int(date_match.group(1)), int(date_match.group(2))
            year = datetime.now().year
            try:
                date_obj = datetime(year, month, day)
            except:
                pass
    
    if not date_obj:
        return False
    
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*[-–—]\s*(\d{1,2}):(\d{2})',
        r'(\d{1,2})\s*[-–—до]\s*(\d{1,2})',
        r'с\s*(\d{1,2})\s*до\s*(\d{1,2})'
    ]
    
    start_time = None
    end_time = None
    
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if len(groups) == 4:
                start_time = f"{groups[0].zfill(2)}:{groups[1]}"
                end_time = f"{groups[2].zfill(2)}:{groups[3]}"
            elif len(groups) == 2:
                start_time = f"{groups[0].zfill(2)}:00"
                end_time = f"{groups[1].zfill(2)}:00"
            break
    
    if not start_time or not end_time:
        return False
    
    employee_name = get_employee_name(user)
    success = save_shift_to_db(employee_name, date_obj.strftime('%Y-%m-%d'), start_time, end_time)
    
    if success:
        weekday = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][date_obj.weekday()]
        hours = calculate_hours(start_time, end_time)
        salary = hours * 250
        
        send_message(user['id'], 
            f"✅ Смена добавлена!\n\n"
            f"📅 {date_obj.strftime('%d.%m.%Y')} ({weekday})\n"
            f"⏰ {start_time} - {end_time}\n"
            f"⏱ Часов: {hours:.1f}\n"
            f"💰 Заработок: {salary:,.0f} ₽")
    else:
        send_message(user['id'], "❌ Не удалось добавить смену, попробуй ещё раз")
    
    return True


def save_shift_to_db(employee: str, date: str, start: str, end: str) -> bool:
    '''Сохранить смену в базу данных'''
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        cur.execute(
            f"SELECT * FROM schedule WHERE employee = '{employee}' AND date = '{date}'"
        )
        existing = cur.fetchone()
        
        if existing:
            cur.execute(
                f"UPDATE schedule SET shift1_start = '{start}', shift1_end = '{end}' "
                f"WHERE employee = '{employee}' AND date = '{date}'"
            )
        else:
            cur.execute(
                f"INSERT INTO schedule (date, employee, shift1_start, shift1_end, has_shift2, "
                f"shift2_start, shift2_end, orders, bonus) "
                f"VALUES ('{date}', '{employee}', '{start}', '{end}', false, '', '', 0, 0)"
            )
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"Saved shift: {employee} on {date} {start}-{end}")
        return True
    
    except Exception as e:
        print(f"Error saving shift: {e}")
        return False


def show_schedule_smart(chat_id: int, user: dict):
    '''Показать расписание умно'''
    employee_name = get_employee_name(user)
    conn = get_db_connection()
    
    if not conn:
        send_message(chat_id, "❌ Не могу подключиться к базе данных")
        return
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        cur.execute(
            f"SELECT * FROM schedule WHERE employee = '{employee_name}' "
            f"AND date >= '{week_start.strftime('%Y-%m-%d')}' "
            f"AND date <= '{week_end.strftime('%Y-%m-%d')}' "
            f"ORDER BY date"
        )
        shifts = cur.fetchall()
        
        if not shifts or not any(s['shift1_start'] for s in shifts):
            send_message(chat_id, f"📅 {employee_name}, у тебя пока нет смен на этой неделе\n\nПросто напиши: «Поставь смену завтра с 10 до 18»")
            return
        
        text = f"📅 Расписание {employee_name}\n"
        text += f"{week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m')}\n\n"
        
        total_hours = 0
        total_salary = 0
        
        for shift in shifts:
            if not shift['shift1_start']:
                continue
            
            date = datetime.strptime(str(shift['date']), '%Y-%m-%d')
            weekday = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][date.weekday()]
            
            hours = calculate_hours(shift['shift1_start'], shift['shift1_end'])
            if shift['has_shift2']:
                hours += calculate_hours(shift['shift2_start'], shift['shift2_end'])
            
            salary = calculate_day_salary(shift)
            total_hours += hours
            total_salary += salary
            
            text += f"📌 {date.strftime('%d.%m')} ({weekday})\n"
            text += f"   ⏰ {shift['shift1_start']} - {shift['shift1_end']}"
            if shift['has_shift2']:
                text += f" + {shift['shift2_start']}-{shift['shift2_end']}"
            text += f"\n   💰 {salary:,.0f} ₽\n\n"
        
        text += f"📊 Итого: {total_hours:.1f}ч • {total_salary:,.0f} ₽"
        send_message(chat_id, text)
        
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"Error showing schedule: {e}")
        send_message(chat_id, "❌ Ошибка при загрузке расписания")


def show_salary_smart(chat_id: int, user: dict):
    '''Показать зарплату умно'''
    employee_name = get_employee_name(user)
    conn = get_db_connection()
    
    if not conn:
        send_message(chat_id, "❌ Не могу подключиться к базе")
        return
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        today = datetime.now()
        month_start = today.replace(day=1).strftime('%Y-%m-%d')
        
        cur.execute(
            f"SELECT * FROM schedule WHERE employee = '{employee_name}' "
            f"AND date >= '{month_start}' "
            f"ORDER BY date"
        )
        shifts = cur.fetchall()
        
        if not shifts or not any(s['shift1_start'] for s in shifts):
            send_message(chat_id, f"💰 {employee_name}, в этом месяце у тебя пока нет смен")
            return
        
        total_salary = 0
        total_hours = 0
        total_orders = 0
        days_worked = 0
        
        for shift in shifts:
            if not shift['shift1_start']:
                continue
            
            days_worked += 1
            salary = calculate_day_salary(shift)
            total_salary += salary
            
            hours = calculate_hours(shift['shift1_start'], shift['shift1_end'])
            if shift['has_shift2']:
                hours += calculate_hours(shift['shift2_start'], shift['shift2_end'])
            total_hours += hours
            total_orders += shift['orders'] or 0
        
        month_name = today.strftime('%B')
        
        text = f"💰 Зарплата за {month_name}\n\n"
        text += f"👤 {employee_name}\n\n"
        text += f"📅 Отработано дней: {days_worked}\n"
        text += f"⏱ Часов: {total_hours:.1f}\n"
        text += f"📦 Заказов: {total_orders}\n\n"
        text += f"💵 Итого: {total_salary:,.0f} ₽\n\n"
        text += f"📊 Расчёт:\n"
        text += f"• Почасовая: {total_hours * 250:,.0f} ₽\n"
        text += f"• За заказы: {total_orders * 50:,.0f} ₽"
        
        send_message(chat_id, text)
        
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"Error showing salary: {e}")
        send_message(chat_id, "❌ Ошибка при расчёте зарплаты")


def respond_with_ai(chat_id: int, text: str, user: dict):
    '''Ответить с помощью YandexGPT'''
    user_name = get_user_name(user)
    employee_name = get_employee_name(user)
    
    system_prompt = f"""Ты — личный помощник и друг для курьеров службы доставки. Твоё имя — Юра.

Твои задачи:
1. Отвечать на вопросы о работе курьера (правила доставки, документы, клиенты, возвраты)
2. Давать полезные советы и поддержку
3. Быть приятным собеседником на любые темы
4. Поддерживать дружеский неформальный стиль

Пользователь: {employee_name} (в Telegram: {user_name})

Отвечай кратко (2-4 предложения), дружелюбно, по-простому. Используй смайлики где уместно."""

    try:
        api_key = os.environ.get('YANDEX_API_KEY')
        folder_id = os.environ.get('YANDEX_FOLDER_ID', 'b1gtukkj95lucj7u4je6')
        
        print(f"AI request from {user_name}: {text[:100]}")
        print(f"Using folder_id: {folder_id}")
        
        if not api_key:
            print(f"Missing API key: api_key={bool(api_key)}")
            send_message(chat_id, "Извини, у меня проблемы с подключением 😔")
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


def show_name_menu(chat_id: int, user: dict):
    '''Показать меню выбора имени'''
    keyboard = {
        'inline_keyboard': [
            [{'text': '👤 Никита', 'callback_data': 'setname_Никита'}],
            [{'text': '👤 Андрей', 'callback_data': 'setname_Андрей'}],
            [{'text': '👤 Денис', 'callback_data': 'setname_Денис'}]
        ]
    }
    send_message(chat_id, "Выбери своё имя в системе:", keyboard)


def handle_callback(callback: dict):
    '''Обработка нажатий на кнопки'''
    chat_id = callback['message']['chat']['id']
    message_id = callback['message']['message_id']
    data = callback['data']
    user = callback['from']
    
    if data.startswith('setname_'):
        employee_name = data.replace('setname_', '')
        save_user_name(user['id'], employee_name)
        edit_message(chat_id, message_id, f"✅ Отлично! Теперь ты — {employee_name}")
    
    answer_callback(callback['id'])


def save_user_name(telegram_id: int, employee_name: str):
    '''Сохранить привязку Telegram ID к имени сотрудника'''
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO telegram_users (telegram_id, employee_name) "
            f"VALUES ({telegram_id}, '{employee_name}') "
            f"ON CONFLICT (telegram_id) DO UPDATE SET employee_name = '{employee_name}'"
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"Saved mapping: {telegram_id} -> {employee_name}")
    except Exception as e:
        print(f"Error saving user name: {e}")


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
    '''Получить имя пользователя из Telegram'''
    return user.get('first_name', 'Пользователь')


def get_employee_name(user: dict) -> str:
    '''Получить имя сотрудника для базы данных'''
    telegram_id = user.get('id')
    first_name = user.get('first_name', '').lower()
    username = user.get('username', '').lower()
    
    name_mapping = {
        'никита': 'Никита',
        'nikita': 'Никита',
        'андрей': 'Андрей',
        'andrey': 'Андрей',
        'andrei': 'Андрей',
        'денис': 'Денис',
        'denis': 'Денис'
    }
    
    if first_name in name_mapping:
        return name_mapping[first_name]
    if username in name_mapping:
        return name_mapping[username]
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT employee_name FROM telegram_users WHERE telegram_id = {telegram_id}")
            result = cur.fetchone()
            if result:
                return result[0]
            cur.close()
            conn.close()
        except:
            pass
    
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