CREATE TABLE IF NOT EXISTS schedule (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    employee VARCHAR(50) NOT NULL,
    shift1_start TIME NOT NULL DEFAULT '09:00',
    shift1_end TIME NOT NULL DEFAULT '18:00',
    has_shift2 BOOLEAN NOT NULL DEFAULT false,
    shift2_start TIME DEFAULT '14:00',
    shift2_end TIME DEFAULT '18:00',
    orders INTEGER NOT NULL DEFAULT 0,
    bonus INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(date, employee)
);

CREATE INDEX idx_schedule_date ON schedule(date);
CREATE INDEX idx_schedule_employee ON schedule(employee);
CREATE INDEX idx_schedule_date_employee ON schedule(date, employee);