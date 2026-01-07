-- Таблица для привязки Telegram пользователей к именам сотрудников
CREATE TABLE IF NOT EXISTS telegram_users (
    telegram_id BIGINT PRIMARY KEY,
    employee_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска по имени сотрудника
CREATE INDEX IF NOT EXISTS idx_telegram_users_employee ON telegram_users(employee_name);

COMMENT ON TABLE telegram_users IS 'Привязка Telegram пользователей к именам сотрудников в расписании';
COMMENT ON COLUMN telegram_users.telegram_id IS 'ID пользователя в Telegram';
COMMENT ON COLUMN telegram_users.employee_name IS 'Имя сотрудника в системе (Никита, Андрей, Денис)';
