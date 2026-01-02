import json
import os
import psycopg2
from datetime import datetime

def handler(event: dict, context) -> dict:
    """API для управления графиком смен сотрудников"""
    method = event.get('httpMethod', 'GET')

    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }

    dsn = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()

    try:
        if method == 'GET':
            month = event.get('queryStringParameters', {}).get('month', '')
            
            if month:
                year, m = month.split('-')
                cur.execute(f"""
                    SELECT date, employee, shift1_start, shift1_end, 
                           has_shift2, shift2_start, shift2_end, orders, bonus
                    FROM schedule 
                    WHERE EXTRACT(YEAR FROM date) = {int(year)} 
                    AND EXTRACT(MONTH FROM date) = {int(m)}
                    ORDER BY date, employee
                """)
            else:
                cur.execute("""
                    SELECT date, employee, shift1_start, shift1_end, 
                           has_shift2, shift2_start, shift2_end, orders, bonus
                    FROM schedule 
                    ORDER BY date DESC, employee
                    LIMIT 100
                """)
            
            rows = cur.fetchall()
            result = []
            for row in rows:
                result.append({
                    'date': row[0].strftime('%Y-%m-%d'),
                    'employee': row[1],
                    'shift1Start': str(row[2]) if row[2] else '',
                    'shift1End': str(row[3]) if row[3] else '',
                    'hasShift2': row[4],
                    'shift2Start': str(row[5]) if row[5] else '',
                    'shift2End': str(row[6]) if row[6] else '',
                    'orders': row[7],
                    'bonus': row[8]
                })
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result)
            }

        elif method == 'POST':
            body = json.loads(event.get('body', '{}'))
            items = body.get('items', [body])
            
            for data in items:
                date = data['date']
                employee = data['employee'].replace("'", "''")
                shift1_start = data.get('shift1Start') or 'NULL'
                shift1_end = data.get('shift1End') or 'NULL'
                has_shift2 = 'TRUE' if data.get('hasShift2', False) else 'FALSE'
                shift2_start = data.get('shift2Start') or 'NULL'
                shift2_end = data.get('shift2End') or 'NULL'
                orders = data.get('orders', 0)
                bonus = data.get('bonus', 0)
                
                if shift1_start != 'NULL':
                    shift1_start = f"'{shift1_start}'"
                if shift1_end != 'NULL':
                    shift1_end = f"'{shift1_end}'"
                if shift2_start != 'NULL':
                    shift2_start = f"'{shift2_start}'"
                if shift2_end != 'NULL':
                    shift2_end = f"'{shift2_end}'"
                
                cur.execute(f"""
                    INSERT INTO schedule 
                    (date, employee, shift1_start, shift1_end, has_shift2, shift2_start, shift2_end, orders, bonus)
                    VALUES ('{date}', '{employee}', {shift1_start}, {shift1_end}, {has_shift2}, {shift2_start}, {shift2_end}, {orders}, {bonus})
                    ON CONFLICT (date, employee) 
                    DO UPDATE SET 
                        shift1_start = EXCLUDED.shift1_start,
                        shift1_end = EXCLUDED.shift1_end,
                        has_shift2 = EXCLUDED.has_shift2,
                        shift2_start = EXCLUDED.shift2_start,
                        shift2_end = EXCLUDED.shift2_end,
                        orders = EXCLUDED.orders,
                        bonus = EXCLUDED.bonus,
                        updated_at = CURRENT_TIMESTAMP
                """)
            conn.commit()
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'saved': len(items)})
            }

    finally:
        cur.close()
        conn.close()

    return {
        'statusCode': 405,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': 'Method not allowed'})
    }