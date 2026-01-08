import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def handler(event: dict, context) -> dict:
    '''API для управления сотрудниками (добавление, удаление, список) с проверкой пароля администратора'''
    
    method = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Admin-Password'
            },
            'body': ''
        }
    
    try:
        if method == 'GET':
            return get_employees()
        
        if method == 'POST':
            body = json.loads(event.get('body', '{}'))
            password = body.get('password', '')
            
            if not verify_password(password):
                return {
                    'statusCode': 403,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Неверный пароль администратора'}, ensure_ascii=False)
                }
            
            full_name = body.get('full_name', '').strip()
            telegram_id = body.get('telegram_id', None)
            
            if not full_name:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'ФИО обязательно'}, ensure_ascii=False)
                }
            
            return add_employee(full_name, telegram_id)
        
        if method == 'DELETE':
            body = json.loads(event.get('body', '{}'))
            password = body.get('password', '')
            
            if not verify_password(password):
                return {
                    'statusCode': 403,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Неверный пароль администратора'}, ensure_ascii=False)
                }
            
            employee_id = body.get('id')
            
            if not employee_id:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'ID сотрудника обязательно'}, ensure_ascii=False)
                }
            
            return delete_employee(employee_id)
        
        if method == 'PUT':
            body = json.loads(event.get('body', '{}'))
            password = body.get('password', '')
            
            if not verify_password(password):
                return {
                    'statusCode': 403,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Неверный пароль администратора'}, ensure_ascii=False)
                }
            
            employee_id = body.get('id')
            full_name = body.get('full_name', '').strip()
            telegram_id = body.get('telegram_id', None)
            is_active = body.get('is_active', True)
            
            if not employee_id:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'ID сотрудника обязательно'}, ensure_ascii=False)
                }
            
            return update_employee(employee_id, full_name, telegram_id, is_active)
        
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Метод не поддерживается'}, ensure_ascii=False)
        }
    
    except Exception as e:
        print(f"ERROR in employees handler: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}, ensure_ascii=False)
        }


def get_db_connection():
    '''Подключение к PostgreSQL'''
    dsn = os.environ.get('DATABASE_URL', '')
    return psycopg2.connect(dsn)


def verify_password(password: str) -> bool:
    '''Проверка пароля администратора'''
    if not password:
        return False
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM admin_passwords ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            return False
        
        stored_password = row[0]
        return password == stored_password
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False


def get_employees():
    '''Получить список всех активных сотрудников'''
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, full_name, telegram_id, is_active, created_at, updated_at
            FROM employees
            ORDER BY created_at DESC
        """)
        employees = cur.fetchall()
        cur.close()
        conn.close()
        
        result = []
        for emp in employees:
            result.append({
                'id': emp['id'],
                'full_name': emp['full_name'],
                'telegram_id': emp['telegram_id'],
                'is_active': emp['is_active'],
                'created_at': emp['created_at'].isoformat() if emp['created_at'] else None,
                'updated_at': emp['updated_at'].isoformat() if emp['updated_at'] else None
            })
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'employees': result, 'count': len(result)}, ensure_ascii=False)
        }
    except Exception as e:
        print(f"Error getting employees: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}, ensure_ascii=False)
        }


def add_employee(full_name: str, telegram_id: int = None):
    '''Добавить нового сотрудника'''
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM employees WHERE is_active = true")
        count = cur.fetchone()[0]
        
        if count >= 15:
            cur.close()
            conn.close()
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Достигнут лимит: максимум 15 активных сотрудников'}, ensure_ascii=False)
            }
        
        cur.execute("""
            INSERT INTO employees (full_name, telegram_id, is_active)
            VALUES (%s, %s, true)
            RETURNING id, full_name, telegram_id, is_active, created_at
        """, (full_name, telegram_id))
        
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': 'Сотрудник успешно добавлен',
                'employee': {
                    'id': row[0],
                    'full_name': row[1],
                    'telegram_id': row[2],
                    'is_active': row[3],
                    'created_at': row[4].isoformat() if row[4] else None
                }
            }, ensure_ascii=False)
        }
    except psycopg2.IntegrityError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Сотрудник с таким ФИО уже существует'}, ensure_ascii=False)
        }
    except Exception as e:
        print(f"Error adding employee: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}, ensure_ascii=False)
        }


def update_employee(employee_id: int, full_name: str = None, telegram_id: int = None, is_active: bool = True):
    '''Обновить данные сотрудника'''
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        updates = []
        params = []
        
        if full_name:
            updates.append("full_name = %s")
            params.append(full_name)
        
        if telegram_id is not None:
            updates.append("telegram_id = %s")
            params.append(telegram_id)
        
        updates.append("is_active = %s")
        params.append(is_active)
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        
        params.append(employee_id)
        
        query = f"UPDATE employees SET {', '.join(updates)} WHERE id = %s RETURNING id, full_name, telegram_id, is_active"
        cur.execute(query, params)
        
        row = cur.fetchone()
        
        if not row:
            cur.close()
            conn.close()
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Сотрудник не найден'}, ensure_ascii=False)
            }
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': 'Сотрудник успешно обновлен',
                'employee': {
                    'id': row[0],
                    'full_name': row[1],
                    'telegram_id': row[2],
                    'is_active': row[3]
                }
            }, ensure_ascii=False)
        }
    except Exception as e:
        print(f"Error updating employee: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}, ensure_ascii=False)
        }


def delete_employee(employee_id: int):
    '''Удалить сотрудника (мягкое удаление - is_active = false)'''
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE employees 
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, full_name
        """, (employee_id,))
        
        row = cur.fetchone()
        
        if not row:
            cur.close()
            conn.close()
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Сотрудник не найден'}, ensure_ascii=False)
            }
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': f'Сотрудник {row[1]} успешно удален',
                'id': row[0]
            }, ensure_ascii=False)
        }
    except Exception as e:
        print(f"Error deleting employee: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}, ensure_ascii=False)
        }
