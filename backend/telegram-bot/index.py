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
    query_params = event.get('queryStringParameters', {})
    action = query_params.get('action', '') if query_params else ''
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }
    
    if method == 'GET' and action == 'daily':
        try:
            send_daily_summary()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'ok': True, 'message': 'Daily summary sent'})
            }
        except Exception as e:
            print(f"ERROR in daily summary: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'ok': False, 'error': str(e)})
            }
    
    try:
        body = json.loads(event.get('body', '{}'))
        print(f"Received update: {json.dumps(body, ensure_ascii=False)[:500]}")
        
        if not body:
            return {'statusCode': 200, 'body': json.dumps({'ok': True})}
        
        if 'message' in body:
            message = body['message']
            if 'new_chat_members' in message:
                handle_new_member(message)
            else:
                handle_message(message)
        elif 'callback_query' in body:
            handle_callback(body['callback_query'])
        elif 'my_chat_member' in body:
            handle_chat_member_update(body['my_chat_member'])
        
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


def handle_new_member(message: dict):
    '''Обработка добавления бота в группу'''
    chat_id = message['chat']['id']
    new_members = message.get('new_chat_members', [])
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    if not bot_token:
        return
    
    for member in new_members:
        if member.get('is_bot') and member.get('username') == 'couriers_helper_bot':
            show_group_welcome(chat_id)
            break


def handle_chat_member_update(update: dict):
    '''Обработка изменения статуса бота в чате'''
    new_status = update.get('new_chat_member', {}).get('status')
    old_status = update.get('old_chat_member', {}).get('status')
    chat_id = update['chat']['id']
    
    if old_status in ['left', 'kicked'] and new_status == 'member':
        show_group_welcome(chat_id)


def show_group_welcome(chat_id: int):
    '''Показать приветствие при добавлении в группу'''
    text = (
        "👋 <b>Всем привет! Я — Хелпер</b>\n\n"
        "Я — ваш умный помощник по расписанию и зарплатам. "
        "Буду помогать управлять сменами, считать заработки и отвечать на вопросы! 😊\n\n"
        "<b>🚀 Быстрый старт:</b>\n\n"
        "Чтобы обратиться ко мне в группе, упомяните меня @couriers_helper_bot\n\n"
        "Например:\n"
        "• <i>@couriers_helper_bot кто сегодня работает?</i>\n"
        "• <i>@couriers_helper_bot статистика</i>\n"
        "• <i>@couriers_helper_bot зарплаты</i>\n\n"
        "📆 <b>Каждое утро в 9:00</b> я буду присылать сводку кто работает сегодня!\n\n"
        "━━━━━━━━━━━━━━━\n"
        "💡 Нажмите кнопку ниже чтобы увидеть все мои возможности 👇"
    )
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '📖 Показать все функции', 'callback_data': 'cmd_fullinfo'}]
        ]
    }
    
    send_message(chat_id, text, keyboard)


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
    
    if not text:
        if is_group:
            show_group_info(chat_id)
        else:
            send_message(chat_id, 
                "👋 Привет! Я — Хелпер, твой помощник.\n\n"
                "Напиши мне что-нибудь, например:\n"
                "• «Поставь смену завтра с 10 до 18»\n"
                "• «Покажи моё расписание»\n"
                "• «Как дела?»")
        return
    
    if text.startswith('/start'):
        employee_name = get_employee_name(user)
        if is_group:
            show_group_info(chat_id)
        else:
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
    
    if text.startswith('/help') or text.startswith('/info'):
        if is_group:
            show_group_info(chat_id)
        else:
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
    is_group = message['chat']['type'] in ['group', 'supergroup']
    
    complex_result = parse_complex_command(text, user, chat_id)
    if complex_result:
        return
    
    shift_result = parse_shift_request(text, user)
    if shift_result:
        return
    
    if any(word in text_lower for word in ['расписание', 'график', 'смены', 'когда работ', 'мои смены', 'кто работает', 'кто сегодня', 'кто завтра']):
        if is_group:
            show_team_schedule(chat_id, text_lower)
        else:
            show_schedule_smart(chat_id, user)
        return
    
    if any(word in text_lower for word in ['статистика', 'рейтинг', 'лидер', 'кто больше', 'сравнение']):
        show_team_stats(chat_id)
        return
    
    employee_question_result = handle_employee_time_question(chat_id, text_lower, user)
    if employee_question_result:
        return
    
    if any(word in text_lower for word in ['зарплата', 'заработ', 'деньги', 'выплата']):
        if is_group:
            show_team_salary(chat_id)
        else:
            show_salary_smart(chat_id, user)
        return
    
    if any(word in text_lower for word in ['совет', 'рекоменд', 'персональн', 'как улучш', 'что делать']):
        if any(name in text_lower for name in ['никит', 'андр', 'денис']):
            show_personal_advice(chat_id, text_lower)
            return
    
    respond_with_ai(chat_id, text, user)


def parse_complex_command(text: str, user: dict, chat_id: int) -> bool:
    '''Парсинг сложных команд с несколькими операциями'''
    text_lower = text.lower()
    
    keywords = ['постав', 'добав', 'запиш', 'смен', 'заказ', 'надбавк', 'доплат', 'удал']
    if not any(kw in text_lower for kw in keywords):
        return False
    
    target_employee = None
    if 'никит' in text_lower:
        target_employee = 'Никита'
    elif 'андр' in text_lower:
        target_employee = 'Андрей'
    elif 'денис' in text_lower:
        target_employee = 'Денис'
    
    if not target_employee:
        target_employee = get_employee_name(user)
    
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
    
    if not date_obj and 'удал' not in text_lower:
        return False
    
    if not date_obj:
        date_obj = datetime.now()
    
    date_str = date_obj.strftime('%Y-%m-%d')
    actions_performed = []
    
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*[-–—]\s*(\d{1,2}):(\d{2})',
        r'(\d{1,2})\s*[-–—до]\s*(\d{1,2})',
        r'с\s*(\d{1,2})\s*до\s*(\d{1,2})'
    ]
    
    shift_added = False
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
            else:
                continue
            
            if save_shift_to_db(target_employee, date_str, start_time, end_time):
                hours = calculate_hours(start_time, end_time)
                actions_performed.append(f"⏰ Смена: {start_time}-{end_time} ({hours:.1f}ч)")
                shift_added = True
            break
    
    orders_match = re.search(r'(\d+)\s*заказ', text_lower)
    if orders_match:
        orders = int(orders_match.group(1))
        if update_orders_in_db(target_employee, date_str, orders):
            actions_performed.append(f"📦 Заказов: {orders}")
    
    bonus_patterns = [
        r'надбавк[уа]?\s+(?:за\s+заказ\s+)?(?:сдела[йть]+\s+)?(\d+)',
        r'доплат[уа]?\s+(?:за\s+заказ\s+)?(?:сдела[йть]+\s+)?(\d+)',
        r'бонус\s+(\d+)'
    ]
    for pattern in bonus_patterns:
        bonus_match = re.search(pattern, text_lower)
        if bonus_match:
            bonus = int(bonus_match.group(1))
            if update_bonus_in_db(date_str, bonus):
                actions_performed.append(f"💰 Доплата за заказ: +{bonus}₽")
            break
    
    if 'удал' in text_lower and 'смен' in text_lower:
        if delete_shift_from_db(target_employee, date_str):
            actions_performed.append(f"🗑 Смена удалена")
    
    if actions_performed:
        weekday = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][date_obj.weekday()]
        
        response = f"✅ <b>Выполнено для {target_employee}!</b>\n\n"
        response += f"📅 {date_obj.strftime('%d.%m.%Y')} ({weekday})\n\n"
        response += "\n".join(actions_performed)
        
        conn = get_db_connection()
        if conn and shift_added:
            try:
                cur = conn.cursor()
                cur.execute(f"SELECT * FROM schedule WHERE employee = '{target_employee}' AND date = '{date_str}'")
                shift_data = cur.fetchone()
                if shift_data:
                    salary = calculate_day_salary_from_row(shift_data)
                    response += f"\n\n💵 <b>Итого заработок: {salary:,.0f} ₽</b>"
                cur.close()
                conn.close()
            except:
                pass
        
        send_message(chat_id, response)
        return True
    
    return False


def parse_shift_request(text: str, user: dict) -> bool:
    '''Парсинг запроса на добавление смены'''
    text_lower = text.lower()
    
    keywords = ['постав', 'добав', 'запиш', 'смен', 'работа', 'график']
    if not any(kw in text_lower for kw in keywords):
        return False
    
    target_employee = None
    if 'никит' in text_lower:
        target_employee = 'Никита'
    elif 'андр' in text_lower:
        target_employee = 'Андрей'
    elif 'денис' in text_lower:
        target_employee = 'Денис'
    
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
    
    employee_name = target_employee if target_employee else get_employee_name(user)
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


def update_orders_in_db(employee: str, date: str, orders: int) -> bool:
    '''Обновить количество заказов'''
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
                f"UPDATE schedule SET orders = {orders} "
                f"WHERE employee = '{employee}' AND date = '{date}'"
            )
        else:
            cur.execute(
                f"INSERT INTO schedule (date, employee, shift1_start, shift1_end, has_shift2, "
                f"shift2_start, shift2_end, orders, bonus) "
                f"VALUES ('{date}', '{employee}', '', '', false, '', '', {orders}, 0)"
            )
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"Updated orders: {employee} on {date} = {orders}")
        return True
    except Exception as e:
        print(f"Error updating orders: {e}")
        return False


def update_bonus_in_db(date: str, bonus: int) -> bool:
    '''Обновить доплату за заказ для всей даты'''
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute(f"UPDATE schedule SET bonus = {bonus} WHERE date = '{date}'")
        
        if cur.rowcount == 0:
            for emp in ['Никита', 'Андрей', 'Денис']:
                cur.execute(
                    f"INSERT INTO schedule (date, employee, shift1_start, shift1_end, has_shift2, "
                    f"shift2_start, shift2_end, orders, bonus) "
                    f"VALUES ('{date}', '{emp}', '', '', false, '', '', 0, {bonus})"
                )
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"Updated bonus for {date} = {bonus}")
        return True
    except Exception as e:
        print(f"Error updating bonus: {e}")
        return False


def delete_shift_from_db(employee: str, date: str) -> bool:
    '''Удалить смену'''
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute(
            f"DELETE FROM schedule WHERE employee = '{employee}' AND date = '{date}'"
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"Deleted shift: {employee} on {date}")
        return True
    except Exception as e:
        print(f"Error deleting shift: {e}")
        return False


def calculate_day_salary_from_row(row) -> float:
    '''Расчёт зарплаты за день из строки БД'''
    shift1_start = row[2] if len(row) > 2 else ''
    shift1_end = row[3] if len(row) > 3 else ''
    has_shift2 = row[4] if len(row) > 4 else False
    shift2_start = row[5] if len(row) > 5 else ''
    shift2_end = row[6] if len(row) > 6 else ''
    orders = row[7] if len(row) > 7 else 0
    bonus = row[8] if len(row) > 8 else 0
    
    hours1 = calculate_hours(shift1_start, shift1_end)
    hours2 = calculate_hours(shift2_start, shift2_end) if has_shift2 else 0
    total_hours = hours1 + hours2
    return (total_hours * 250) + (orders * (50 + bonus))


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
        days_worked = 0
        
        for shift in shifts:
            if not shift['shift1_start']:
                continue
            
            days_worked += 1
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
        
        text += f"📊 Итого: {total_hours:.1f}ч • {total_salary:,.0f} ₽\n\n"
        
        badge = get_employee_badge(days_worked, total_hours, total_salary)
        text += f"🏆 Статус: {badge}"
        
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
    
    system_prompt = f"""Ты — Хелпер, личный помощник курьеров доставки. Дружелюбный, полезный, прикольный.

Твои возможности (ВАЖНО — упоминай их в ответах):
• Управление расписанием: "поставь смену завтра с 10 до 18"
• Статистика: "кто сегодня работает?", "статистика команды"
• Зарплаты: "сколько я заработал?", "зарплаты всех"
• Консультации по работе курьера (возвраты, клиенты, документы)
• Творческий контент: песни, стихи, анекдоты, истории про курьеров
• Просто поболтать и поддержать 😊

Когда тебя спрашивают "что ты умеешь?" — покажи КОНКРЕТНЫЕ примеры команд!

Пользователь: {employee_name} (Telegram: {user_name})

Стиль: короткие ответы (2-4 предложения), дружелюбно, по-русски, со смайликами. 
Если вопрос про функции — перечисли примеры команд.
Если просят песню, стихи, анекдот — сочиняй креативно и весело! 🎵"""

    try:
        api_key = os.environ.get('YANDEX_API_KEY')
        folder_id = 'b1gtukkj95lucj7u4je6'
        
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
    
    elif data == 'cmd_today':
        answer_callback(callback['id'], "Смотрю кто сегодня работает...")
        show_team_schedule(chat_id, 'кто сегодня')
    
    elif data == 'cmd_tomorrow':
        answer_callback(callback['id'], "Смотрю на завтра...")
        show_team_schedule(chat_id, 'кто завтра')
    
    elif data == 'cmd_stats':
        answer_callback(callback['id'], "Считаю статистику...")
        show_team_stats(chat_id)
    
    elif data == 'cmd_salary':
        answer_callback(callback['id'], "Смотрю зарплаты...")
        show_team_salary(chat_id)
    
    elif data == 'cmd_faq':
        answer_callback(callback['id'])
        send_message(chat_id,
            "<b>❓ Частые вопросы</b>\n\n"
            "<b>Q: Как добавить смену?</b>\n"
            "A: Напиши мне в личку: «Поставь смену завтра с 10 до 18»\n\n"
            "<b>Q: Как посмотреть моё расписание?</b>\n"
            "A: В личке напиши: «Моё расписание»\n\n"
            "<b>Q: Как узнать зарплату?</b>\n"
            "A: В личке: «Сколько я заработал?»\n\n"
            "<b>Q: Что делать если клиент не отвечает?</b>\n"
            "A: Просто спроси меня — я подскажу! 😊")
    
    elif data == 'cmd_fullinfo':
        answer_callback(callback['id'])
        show_group_info(chat_id)
    
    else:
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
        start_parts = start.split(':')
        end_parts = end.split(':')
        start_h, start_m = int(start_parts[0]), int(start_parts[1])
        end_h, end_m = int(end_parts[0]), int(end_parts[1])
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m
        return (end_minutes - start_minutes) / 60
    except Exception as e:
        print(f"Error calculating hours: start={start}, end={end}, error={e}")
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


def handle_employee_time_question(chat_id: int, text_lower: str, user: dict) -> bool:
    '''Обрабатывает вопросы о времени работы сотрудников'''
    
    time_keywords = [
        'сколько', 'как долго', 'во сколько', 'до скольки', 'когда',
        'приедет', 'вернется', 'закончит', 'начнет', 'работает',
        'смен', 'домой', 'в курсе'
    ]
    
    if not any(keyword in text_lower for keyword in time_keywords):
        return False
    
    target_employee = extract_employee_name(text_lower, user)
    if not target_employee:
        return False
    
    show_employee_day_info(chat_id, text_lower, target_employee)
    return True


def extract_employee_name(text_lower: str, user: dict) -> str:
    '''Извлекает имя сотрудника из текста или контекста'''
    
    if 'никит' in text_lower:
        return 'Никита'
    elif 'андр' in text_lower:
        return 'Андрей'
    elif 'денис' in text_lower:
        return 'Денис'
    
    pronoun_keywords = ['он', 'его', 'ему', 'им', 'она', 'её', 'ей']
    if any(pronoun in text_lower for pronoun in pronoun_keywords):
        conn = get_db_connection()
        if not conn:
            return None
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            today = datetime.now().strftime('%Y-%m-%d')
            cur.execute(f"SELECT employee FROM schedule WHERE date = '{today}' AND shift1_start IS NOT NULL AND shift1_start != '' ORDER BY employee")
            working_today = [row['employee'] for row in cur.fetchall()]
            cur.close()
            conn.close()
            
            if len(working_today) == 1:
                return working_today[0]
            elif len(working_today) > 1:
                return working_today[0]
        except:
            pass
    
    return None


def show_employee_day_info(chat_id: int, text_lower: str, target_employee: str = None):
    '''Показать информацию про конкретного сотрудника на день'''
    conn = get_db_connection()
    if not conn:
        send_message(chat_id, "❌ Не могу подключиться к базе")
        return
    
    if not target_employee:
        target_employee = None
        if 'никит' in text_lower:
            target_employee = 'Никита'
        elif 'андр' in text_lower:
            target_employee = 'Андрей'
        elif 'денис' in text_lower:
            target_employee = 'Денис'
    
    if not target_employee:
        send_message(chat_id, "Не понял, про кого ты спрашиваешь? 🤔")
        return
    
    try:
        target_date = datetime.now()
        if 'завтра' in text_lower:
            target_date += timedelta(days=1)
        
        date_str = target_date.strftime('%Y-%m-%d')
        weekday = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][target_date.weekday()]
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(f"SELECT * FROM schedule WHERE date = '{date_str}' AND employee = '{target_employee}'")
        shift = cur.fetchone()
        
        if not shift or not shift['shift1_start']:
            send_message(chat_id, f"📅 {target_date.strftime('%d.%m.%Y')} ({weekday})\n\n{target_employee} не работает 🏖")
            cur.close()
            conn.close()
            return
        
        hours = calculate_hours(shift['shift1_start'], shift['shift1_end'])
        if shift['has_shift2']:
            hours += calculate_hours(shift['shift2_start'], shift['shift2_end'])
        
        salary = calculate_day_salary(shift)
        
        emoji = {'Никита': '👨‍💼', 'Андрей': '🧑‍💻', 'Денис': '👨‍🔧'}.get(target_employee, '👤')
        
        is_question_about_end = any(word in text_lower for word in ['до скольки', 'когда приедет', 'когда закончит', 'вернется', 'домой'])
        
        text = f"{emoji} <b>{target_employee}</b>\n"
        text += f"📅 {target_date.strftime('%d.%m.%Y')} ({weekday})\n\n"
        
        if is_question_about_end:
            end_time = shift['shift2_end'] if shift['has_shift2'] else shift['shift1_end']
            text += f"🏁 Работает <b>до {end_time}</b>\n\n"
        
        text += f"⏰ {shift['shift1_start']} - {shift['shift1_end']}"
        if shift['has_shift2']:
            text += f" + {shift['shift2_start']}-{shift['shift2_end']}"
        text += f"\n⏱ Часов: {hours:.1f}ч\n"
        text += f"📦 Заказов: {shift['orders'] or 0}\n"
        text += f"💰 Заработок: {salary:,.0f} ₽"
        
        send_message(chat_id, text)
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"Error showing employee day info: {e}")
        import traceback
        print(traceback.format_exc())
        send_message(chat_id, "❌ Ошибка при загрузке информации")


def show_personal_advice(chat_id: int, text_lower: str):
    '''Показать персональные советы сотруднику'''
    conn = get_db_connection()
    if not conn:
        send_message(chat_id, "❌ Не могу подключиться к базе")
        return
    
    target_employee = None
    if 'никит' in text_lower:
        target_employee = 'Никита'
    elif 'андр' in text_lower:
        target_employee = 'Андрей'
    elif 'денис' in text_lower:
        target_employee = 'Денис'
    
    if not target_employee:
        send_message(chat_id, "Не понял, кому дать советы? 🤔")
        return
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        today = datetime.now()
        month_start = today.replace(day=1).strftime('%Y-%m-%d')
        today_str = today.strftime('%Y-%m-%d')
        
        cur.execute(
            f"SELECT * FROM schedule WHERE employee = '{target_employee}' "
            f"AND date >= '{month_start}' "
            f"ORDER BY date"
        )
        shifts = cur.fetchall()
        
        work_shifts = [
            s for s in shifts 
            if s['shift1_start'] 
            and str(s['shift1_start']) != '00:00:00'
            and str(s['date']) <= today_str
        ]
        
        if not work_shifts:
            emoji = {'Никита': '👨‍💼', 'Андрей': '🧑‍💻', 'Денис': '👨‍🔧'}.get(target_employee, '👤')
            text = f"{emoji} <b>Персональные советы для {target_employee}</b>\n\n"
            text += "📊 <b>Анализ активности:</b>\n"
            text += f"❌ В этом месяце пока нет отработанных смен\n\n"
            text += "💡 <b>Рекомендации:</b>\n\n"
            text += "🔥 <b>Возьми больше смен!</b>\n"
            text += "   Сейчас у тебя 0 часов. Чтобы зарабатывать, нужно брать смены.\n\n"
            text += "📅 <b>План действий:</b>\n"
            text += "   1. Напиши мне: «Поставь смену завтра с 10 до 18»\n"
            text += "   2. Работай стабильно 5-6 дней в неделю\n"
            text += "   3. Следи за заказами — они дают бонусы!\n\n"
            text += "💰 <b>Потенциал:</b>\n"
            text += f"   Если будешь работать 8ч × 20 дней:\n"
            text += f"   {20 * 8 * 250:,.0f}₽ почасовая + бонусы за заказы\n\n"
            text += "💪 Начни сегодня — стань лидером команды!"
            
            send_message(chat_id, text)
            cur.close()
            conn.close()
            return
        
        total_hours = sum(
            calculate_hours(s['shift1_start'], s['shift1_end']) +
            (calculate_hours(s['shift2_start'], s['shift2_end']) if s['has_shift2'] else 0)
            for s in work_shifts
        )
        total_salary = sum(calculate_day_salary(s) for s in work_shifts)
        total_orders = sum(s['orders'] or 0 for s in work_shifts)
        days_worked = len(work_shifts)
        
        cur.execute(f"SELECT * FROM schedule WHERE date >= '{month_start}' ORDER BY employee")
        all_shifts = cur.fetchall()
        
        team_stats = {}
        for emp in ['Никита', 'Андрей', 'Денис']:
            emp_shifts = [s for s in all_shifts if s['employee'] == emp and s['shift1_start'] and str(s['shift1_start']) != '00:00:00']
            team_hours = sum(
                calculate_hours(s['shift1_start'], s['shift1_end']) +
                (calculate_hours(s['shift2_start'], s['shift2_end']) if s['has_shift2'] else 0)
                for s in emp_shifts
            )
            team_stats[emp] = {
                'hours': team_hours,
                'days': len(emp_shifts),
                'salary': sum(calculate_day_salary(s) for s in emp_shifts)
            }
        
        sorted_by_hours = sorted(team_stats.items(), key=lambda x: x[1]['hours'], reverse=True)
        position = [i for i, (emp, _) in enumerate(sorted_by_hours) if emp == target_employee][0] + 1
        
        emoji = {'Никита': '👨‍💼', 'Андрей': '🧑‍💻', 'Денис': '👨‍🔧'}.get(target_employee, '👤')
        
        text = f"{emoji} <b>Персональные советы для {target_employee}</b>\n\n"
        text += f"📊 <b>Твоя статистика за {today.strftime('%B')}:</b>\n"
        text += f"   💼 Смен: {days_worked}\n"
        text += f"   ⏱ Часов: {total_hours:.1f}ч\n"
        text += f"   📦 Заказов: {total_orders}\n"
        text += f"   💰 Заработано: {total_salary:,.0f}₽\n\n"
        
        text += f"🏆 <b>Позиция в команде:</b> {position}-е место\n\n"
        
        text += "💡 <b>Персональные рекомендации:</b>\n\n"
        
        avg_hours_per_day = total_hours / days_worked if days_worked > 0 else 0
        
        if total_hours < 40:
            text += "🔥 <b>Возьми больше смен!</b>\n"
            text += f"   У тебя всего {total_hours:.1f}ч. Для хорошего заработка нужно минимум 120ч в месяц.\n\n"
        elif total_hours < 120:
            text += "📈 <b>Увеличь рабочую нагрузку</b>\n"
            text += f"   {total_hours:.1f}ч — это хорошо, но можно больше! Цель: 160ч/месяц.\n\n"
        else:
            text += "🌟 <b>Отличная активность!</b>\n"
            text += f"   {total_hours:.1f}ч — ты работаешь стабильно. Так держать!\n\n"
        
        if avg_hours_per_day < 6:
            text += "⏰ <b>Удлини смены</b>\n"
            text += f"   Средняя смена: {avg_hours_per_day:.1f}ч. Лучше брать 8-часовые смены.\n\n"
        
        if total_orders < total_hours * 5:
            text += "📦 <b>Работай над заказами</b>\n"
            text += f"   {total_orders} заказов за {total_hours:.1f}ч. Цель: минимум 5 заказов в час.\n\n"
        else:
            text += "🎯 <b>Отличная работа с заказами!</b>\n"
            text += f"   {total_orders} заказов — продолжай в том же духе!\n\n"
        
        if position == 1:
            text += "👑 <b>Ты лидер команды!</b>\n"
            text += "   Продолжай держать планку высоко — остальные равняются на тебя!\n\n"
        else:
            leader = sorted_by_hours[0]
            gap = leader[1]['hours'] - total_hours
            text += f"🎯 <b>До 1-го места осталось {gap:.1f}ч</b>\n"
            text += f"   Сейчас лидирует {leader[0]}. Поработай усерднее!\n\n"
        
        potential_salary = (160 * 250) + (160 * 5 * 50)
        text += f"💰 <b>Твой потенциал:</b>\n"
        text += f"   При 160ч/месяц + 800 заказов = {potential_salary:,.0f}₽\n\n"
        text += "💪 <b>Ты можешь больше — дерзай!</b>"
        
        send_message(chat_id, text)
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"Error showing personal advice: {e}")
        import traceback
        print(traceback.format_exc())
        send_message(chat_id, "❌ Ошибка при анализе данных")


def show_team_schedule(chat_id: int, text_lower: str):
    '''Показать расписание команды на сегодня/завтра'''
    conn = get_db_connection()
    if not conn:
        send_message(chat_id, "❌ Не могу подключиться к базе")
        return
    
    try:
        target_date = datetime.now()
        if 'завтра' in text_lower:
            target_date += timedelta(days=1)
        
        date_str = target_date.strftime('%Y-%m-%d')
        weekday = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][target_date.weekday()]
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(f"SELECT * FROM schedule WHERE date = '{date_str}' ORDER BY employee")
        shifts = cur.fetchall()
        
        working = [s for s in shifts if s['shift1_start']]
        
        if not working:
            send_message(chat_id, f"📅 {target_date.strftime('%d.%m.%Y')} ({weekday})\n\nНикто не работает — выходной! 🎉")
            return
        
        text = f"📅 Расписание на {target_date.strftime('%d.%m.%Y')}\n{weekday}\n\n"
        
        for shift in working:
            emoji = {'Никита': '👨‍💼', 'Андрей': '🧑‍💻', 'Денис': '👨‍🔧'}.get(shift['employee'], '👤')
            text += f"{emoji} <b>{shift['employee']}</b>\n"
            text += f"   ⏰ {shift['shift1_start']} - {shift['shift1_end']}"
            if shift['has_shift2']:
                text += f" + {shift['shift2_start']}-{shift['shift2_end']}"
            
            hours = calculate_hours(shift['shift1_start'], shift['shift1_end'])
            if shift['has_shift2']:
                hours += calculate_hours(shift['shift2_start'], shift['shift2_end'])
            text += f" ({hours:.1f}ч)\n\n"
        
        send_message(chat_id, text)
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"Error showing team schedule: {e}")
        send_message(chat_id, "❌ Ошибка при загрузке расписания")


def show_team_stats(chat_id: int):
    '''Показать статистику и рейтинг команды'''
    conn = get_db_connection()
    if not conn:
        send_message(chat_id, "❌ Не могу подключиться к базе")
        return
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        today = datetime.now()
        month_start = today.replace(day=1).strftime('%Y-%m-%d')
        
        cur.execute(f"SELECT * FROM schedule WHERE date >= '{month_start}' ORDER BY employee, date")
        all_shifts = cur.fetchall()
        
        stats = {}
        for emp in ['Никита', 'Андрей', 'Денис']:
            emp_shifts = [s for s in all_shifts if s['employee'] == emp and s['shift1_start'] and str(s['shift1_start']) != '00:00:00']
            
            total_hours = sum(
                calculate_hours(s['shift1_start'], s['shift1_end']) +
                (calculate_hours(s['shift2_start'], s['shift2_end']) if s['has_shift2'] else 0)
                for s in emp_shifts
            )
            total_salary = sum(calculate_day_salary(s) for s in emp_shifts)
            
            stats[emp] = {
                'days': len(emp_shifts),
                'hours': total_hours,
                'salary': total_salary
            }
        
        sorted_by_salary = sorted(stats.items(), key=lambda x: x[1]['salary'], reverse=True)
        
        text = f"📊 <b>Статистика команды за {today.strftime('%B %Y')}</b>\n\n"
        
        medals = ['🥇', '🥈', '🥉']
        for i, (emp, data) in enumerate(sorted_by_salary):
            emoji = {'Никита': '👨‍💼', 'Андрей': '🧑‍💻', 'Денис': '👨‍🔧'}.get(emp, '👤')
            medal = medals[i] if i < 3 else '  '
            
            text += f"{medal} {emoji} <b>{emp}</b>\n"
            text += f"   💰 {data['salary']:,.0f} ₽\n"
            text += f"   ⏱ {data['hours']:.1f} часов • {data['days']} дней\n"
            
            badge = get_employee_badge(data['days'], data['hours'], data['salary'])
            text += f"   🏆 {badge}\n\n"
        
        leader = sorted_by_salary[0]
        if leader[1]['salary'] > 0:
            text += f"🔥 <b>Лидер месяца: {leader[0]}</b>\n"
            text += f"Так держать! 💪"
        
        send_message(chat_id, text)
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"Error showing team stats: {e}")
        send_message(chat_id, "❌ Ошибка при загрузке статистики")


def show_team_salary(chat_id: int):
    '''Показать зарплаты всей команды'''
    conn = get_db_connection()
    if not conn:
        send_message(chat_id, "❌ Не могу подключиться к базе")
        return
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        today = datetime.now()
        month_start = today.replace(day=1).strftime('%Y-%m-%d')
        
        cur.execute(f"SELECT * FROM schedule WHERE date >= '{month_start}' ORDER BY employee")
        all_shifts = cur.fetchall()
        
        text = f"💰 <b>Зарплаты за {today.strftime('%B %Y')}</b>\n\n"
        
        total_all = 0
        for emp in ['Никита', 'Андрей', 'Денис']:
            emp_shifts = [s for s in all_shifts if s['employee'] == emp and s['shift1_start'] and str(s['shift1_start']) != '00:00:00']
            
            total_salary = sum(calculate_day_salary(s) for s in emp_shifts)
            total_hours = sum(
                calculate_hours(s['shift1_start'], s['shift1_end']) +
                (calculate_hours(s['shift2_start'], s['shift2_end']) if s['has_shift2'] else 0)
                for s in emp_shifts
            )
            total_orders = sum(s['orders'] or 0 for s in emp_shifts)
            
            emoji = {'Никита': '👨‍💼', 'Андрей': '🧑‍💻', 'Денис': '👨‍🔧'}.get(emp, '👤')
            
            text += f"{emoji} <b>{emp}</b>\n"
            text += f"   💵 {total_salary:,.0f} ₽\n"
            text += f"   ⏱ {total_hours:.1f}ч • 📦 {total_orders} зак.\n\n"
            
            total_all += total_salary
        
        text += f"━━━━━━━━━━━━━━━\n"
        text += f"<b>Общий фонд: {total_all:,.0f} ₽</b>"
        
        send_message(chat_id, text)
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"Error showing team salary: {e}")
        send_message(chat_id, "❌ Ошибка при загрузке зарплат")


def get_employee_badge(days: int, hours: float, salary: float) -> str:
    '''Получить бейдж сотрудника по статистике'''
    if days == 0:
        return "Новичок 🐣"
    
    if salary >= 50000:
        return "Стахановец 💎"
    elif salary >= 30000:
        return "Трудяга 🔥"
    elif salary >= 15000:
        return "Работяга 💪"
    elif salary >= 5000:
        return "Начинающий ⭐"
    else:
        return "Стартовал 🚀"


def show_group_info(chat_id: int):
    '''Показать инструкцию для группы'''
    text = (
        "👋 <b>Привет! Я — Хелпер, ваш умный помощник</b>\n\n"
        "Работаю в группе — упомяните меня @couriers_helper_bot\n\n"
        "<b>📅 Расписание команды:</b>\n"
        "• <i>кто сегодня работает?</i>\n"
        "• <i>кто завтра?</i>\n"
        "• <i>расписание на неделю</i>\n\n"
        "<b>📊 Статистика:</b>\n"
        "• <i>статистика</i> — рейтинг команды 🥇\n"
        "• <i>зарплаты</i> — все заработки\n\n"
        "<b>✏️ Добавить смену (личка):</b>\n"
        "• <i>поставь смену завтра с 10 до 18</i>\n"
        "• <i>добавь послезавтра 9-17</i>\n\n"
        "<b>💬 Общение:</b>\n"
        "Задавайте любые вопросы — я помогу! 😊\n\n"
        "📆 <b>Каждое утро в 9:00</b> я присылаю сводку дня\n\n"
        "━━━━━━━━━━━━━━━\n"
        "💡 <b>Команды:</b> /info — показать эту справку"
    )
    
    keyboard = {
        'inline_keyboard': [
            [
                {'text': '👥 Кто сегодня?', 'callback_data': 'cmd_today'},
                {'text': '📅 Кто завтра?', 'callback_data': 'cmd_tomorrow'}
            ],
            [
                {'text': '📊 Статистика', 'callback_data': 'cmd_stats'},
                {'text': '💰 Зарплаты', 'callback_data': 'cmd_salary'}
            ],
            [
                {'text': '❓ Частые вопросы', 'callback_data': 'cmd_faq'}
            ]
        ]
    }
    
    send_message(chat_id, text, keyboard)


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


def answer_callback(callback_id: str, text: str = None):
    '''Ответить на callback query'''
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        return
    
    data = {'callback_query_id': callback_id}
    if text:
        data['text'] = text
        data['show_alert'] = False
    
    requests.post(
        f'https://api.telegram.org/bot{token}/answerCallbackQuery',
        json=data
    )


def send_daily_summary():
    '''Отправить ежедневную сводку в группу'''
    chat_id = os.environ.get('TELEGRAM_GROUP_CHAT_ID')
    if not chat_id:
        print("ERROR: TELEGRAM_GROUP_CHAT_ID not set")
        return
    
    try:
        chat_id = int(chat_id)
    except:
        print(f"ERROR: Invalid TELEGRAM_GROUP_CHAT_ID: {chat_id}")
        return
    
    conn = get_db_connection()
    if not conn:
        send_message(chat_id, "❌ Не могу подключиться к базе для утренней сводки")
        return
    
    try:
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        weekday = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][today.weekday()]
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(f"SELECT * FROM schedule WHERE date = '{date_str}' ORDER BY employee")
        shifts = cur.fetchall()
        
        working = [s for s in shifts if s['shift1_start']]
        
        text = f"☀️ <b>Доброе утро!</b>\n\n"
        text += f"📅 <b>{today.strftime('%d.%m.%Y')} — {weekday}</b>\n\n"
        
        if not working:
            text += "🎉 <b>Сегодня выходной — никто не работает!</b>\n\n"
            text += "Отдыхайте и набирайтесь сил! 💪"
        else:
            text += "<b>👥 Кто выходит на смену:</b>\n\n"
            
            for shift in working:
                emoji = {'Никита': '👨‍💼', 'Андрей': '🧑‍💻', 'Денис': '👨‍🔧'}.get(shift['employee'], '👤')
                text += f"{emoji} <b>{shift['employee']}</b>\n"
                text += f"   ⏰ {shift['shift1_start']} - {shift['shift1_end']}"
                
                if shift['has_shift2']:
                    text += f" + {shift['shift2_start']}-{shift['shift2_end']}"
                
                hours = calculate_hours(shift['shift1_start'], shift['shift1_end'])
                if shift['has_shift2']:
                    hours += calculate_hours(shift['shift2_start'], shift['shift2_end'])
                text += f" ({hours:.1f}ч)\n\n"
            
            text += "━━━━━━━━━━━━━━━\n"
            text += "💪 <b>Удачной смены, команда!</b>"
        
        send_message(chat_id, text)
        cur.close()
        conn.close()
        print(f"Daily summary sent successfully to chat {chat_id}")
    
    except Exception as e:
        print(f"Error sending daily summary: {e}")
        import traceback
        print(traceback.format_exc())