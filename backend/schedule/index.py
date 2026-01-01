import json
import os
import psycopg2
from datetime import datetime

def handler(event: dict, context) -> dict:
    """
    API для управления расписанием сотрудников.
    Сохраняет и загружает данные о сменах, заказах и доплатах.
    """
    method = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    db_url = os.environ.get('DATABASE_URL')
    schema = os.environ.get('MAIN_DB_SCHEMA')
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute(f"SET search_path TO {schema}")
        
        if method == 'GET':
            month = event.get('queryStringParameters', {}).get('month')
            
            if month:
                cur.execute(
                    f"SELECT date, employee, shift1_start, shift1_end, has_shift2, shift2_start, shift2_end, orders, bonus FROM schedule WHERE TO_CHAR(date, 'YYYY-MM') = '{month}' ORDER BY date, employee"
                )
            else:
                cur.execute(
                    f"SELECT date, employee, shift1_start, shift1_end, has_shift2, shift2_start, shift2_end, orders, bonus FROM schedule ORDER BY date DESC LIMIT 100"
                )
            
            rows = cur.fetchall()
            data = []
            for row in rows:
                data.append({
                    'date': str(row[0]),
                    'employee': row[1],
                    'shift1Start': str(row[2]),
                    'shift1End': str(row[3]),
                    'hasShift2': row[4],
                    'shift2Start': str(row[5]) if row[5] else '14:00',
                    'shift2End': str(row[6]) if row[6] else '18:00',
                    'orders': row[7],
                    'bonus': row[8]
                })
            
            cur.close()
            conn.close()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(data),
                'isBase64Encoded': False
            }
        
        elif method == 'POST' or method == 'PUT':
            body = json.loads(event.get('body', '{}'))
            date = body.get('date')
            employee = body.get('employee')
            shift1_start = body.get('shift1Start', '09:00')
            shift1_end = body.get('shift1End', '18:00')
            has_shift2 = body.get('hasShift2', False)
            shift2_start = body.get('shift2Start', '14:00')
            shift2_end = body.get('shift2End', '18:00')
            orders = body.get('orders', 0)
            bonus = body.get('bonus', 0)
            
            cur.execute(
                f"""
                INSERT INTO schedule (date, employee, shift1_start, shift1_end, has_shift2, shift2_start, shift2_end, orders, bonus, updated_at)
                VALUES ('{date}', '{employee}', '{shift1_start}', '{shift1_end}', {has_shift2}, '{shift2_start}', '{shift2_end}', {orders}, {bonus}, NOW())
                ON CONFLICT (date, employee) 
                DO UPDATE SET 
                    shift1_start = '{shift1_start}',
                    shift1_end = '{shift1_end}',
                    has_shift2 = {has_shift2},
                    shift2_start = '{shift2_start}',
                    shift2_end = '{shift2_end}',
                    orders = {orders},
                    bonus = {bonus},
                    updated_at = NOW()
                """
            )
            conn.commit()
            cur.close()
            conn.close()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'success': True}),
                'isBase64Encoded': False
            }
        
        elif method == 'DELETE':
            body = json.loads(event.get('body', '{}'))
            date = body.get('date')
            employee = body.get('employee')
            
            cur.execute(
                f"DELETE FROM schedule WHERE date = '{date}' AND employee = '{employee}'"
            )
            conn.commit()
            cur.close()
            conn.close()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'success': True}),
                'isBase64Encoded': False
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Method not allowed'}),
                'isBase64Encoded': False
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }
