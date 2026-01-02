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

  const hourOptions = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'));
  const minuteOptions = ['00', '15', '30', '45'];

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
        <div className="absolute z-50 mt-2 w-full bg-popover border border-border rounded-lg shadow-lg p-4">
          <div className="flex gap-3 mb-4">
            <div className="flex-1">
              <div className="text-xs text-muted-foreground mb-2 text-center">Часы</div>
              <div className="max-h-48 overflow-y-auto border border-border rounded-md">
                {hourOptions.map((h) => (
                  <button
                    key={h}
                    type="button"
                    onClick={() => setHours(h)}
                    className={`w-full px-3 py-2 text-sm text-left hover:bg-accent transition-colors ${
                      hours === h ? 'bg-primary text-primary-foreground font-semibold' : ''
                    }`}
                  >
                    {h}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex-1">
              <div className="text-xs text-muted-foreground mb-2 text-center">Минуты</div>
              <div className="border border-border rounded-md">
                {minuteOptions.map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setMinutes(m)}
                    className={`w-full px-3 py-2 text-sm text-left hover:bg-accent transition-colors ${
                      minutes === m ? 'bg-primary text-primary-foreground font-semibold' : ''
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleClear}
              className="flex-1"
            >
              Очистить
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={handleApply}
              className="flex-1"
            >
              Применить
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TimePicker;
