import { useState, useRef, useEffect } from 'react';
import { Button } from './button';
import Icon from './icon';

interface TimePickerProps {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export const TimePicker = ({ value, onChange, className = '' }: TimePickerProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [hours, setHours] = useState('09');
  const [minutes, setMinutes] = useState('00');
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (value) {
      const [h, m] = value.split(':');
      setHours(h || '09');
      setMinutes(m || '00');
    }
  }, [value]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleApply = () => {
    onChange(`${hours}:${minutes}`);
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange('');
    setHours('09');
    setMinutes('00');
    setIsOpen(false);
  };

  const hourOptions = [
    '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '00', '01'
  ];
  const minuteOptions = ['00'];

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full h-10 px-3 py-2 text-sm rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-colors text-left flex items-center justify-between"
      >
        <span className={value ? 'text-foreground' : 'text-muted-foreground'}>
          {value || 'Выбрать время'}
        </span>
        <Icon name="Clock" size={16} className="text-muted-foreground" />
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-2 w-full bg-card border border-border rounded-lg shadow-lg p-4">
          <div className="mb-4">
            <div className="text-xs text-muted-foreground mb-2 text-center">Часы (07:00 - 01:00)</div>
            <div className="max-h-64 overflow-y-auto border border-border rounded-md bg-background">
              {hourOptions.map((h) => (
                <button
                  key={h}
                  type="button"
                  onClick={() => {
                    onChange(`${h}:00`);
                    setIsOpen(false);
                  }}
                  className={`w-full px-4 py-3 text-lg font-medium text-center hover:bg-accent hover:text-accent-foreground transition-colors ${
                    value === `${h}:00` ? 'bg-primary text-primary-foreground' : 'text-foreground'
                  }`}
                >
                  {h}:00
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleClear}
              className="w-full"
            >
              Очистить
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TimePicker;