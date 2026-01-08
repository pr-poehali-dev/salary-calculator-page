-- Таблица сотрудников (до 15 человек)
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL UNIQUE,
    telegram_id BIGINT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица паролей администратора
CREATE TABLE IF NOT EXISTS admin_passwords (
    id SERIAL PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Вставляем дефолтный пароль "admin123"
INSERT INTO admin_passwords (password_hash) 
VALUES ('admin123')
ON CONFLICT DO NOTHING;

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_employees_active ON employees(is_active);
CREATE INDEX IF NOT EXISTS idx_employees_telegram ON employees(telegram_id);