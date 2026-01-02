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
                cur.execute("""
                    SELECT date, employee, shift1_start, shift1_end, 
                           has_shift2, shift2_start, shift2_end, orders, bonus
                    FROM schedule 
                    WHERE EXTRACT(YEAR FROM date) = %s 
                    AND EXTRACT(MONTH FROM date) = %s
                    ORDER BY date, employee
                """, (int(year), int(m)))
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
                cur.execute("""
                    INSERT INTO schedule 
                    (date, employee, shift1_start, shift1_end, has_shift2, shift2_start, shift2_end, orders, bonus)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                """, (
                    data['date'],
                    data['employee'],
                    data.get('shift1Start') or None,
                    data.get('shift1End') or None,
                    data.get('hasShift2', False),
                    data.get('shift2Start') or None,
                    data.get('shift2End') or None,
                    data.get('orders', 0),
                    data.get('bonus', 0)
                ))
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