
CREATE TABLE IF NOT EXISTS schedule (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  employee VARCHAR(100) NOT NULL,
  shift1_start TIME,
  shift1_end TIME,
  has_shift2 BOOLEAN DEFAULT FALSE,
  shift2_start TIME,
  shift2_end TIME,
  orders INTEGER DEFAULT 0,
  bonus INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(date, employee)
);

CREATE INDEX IF NOT EXISTS idx_schedule_date ON schedule(date);
CREATE INDEX IF NOT EXISTS idx_schedule_employee ON schedule(employee);
