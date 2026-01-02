import { useState, useRef, useEffect, useId } from 'react';
import { createPortal } from 'react-dom';
import { Button } from './button';
import Icon from './icon';

interface TimePickerProps {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export const TimePicker = ({ value, onChange, className = '' }: TimePickerProps) => {
  const pickerId = useId();
  const [isOpen, setIsOpen] = useState(false);
  const [hours, setHours] = useState('09');
  const [minutes, setMinutes] = useState('00');
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const isOpeningRef = useRef(false);

  useEffect(() => {
    if (value) {
      const [h, m] = value.split(':');
      setHours(h || '09');
      setMinutes(m || '00');
    }
  }, [value]);

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      // Игнорируем если это клик открытия
      if (isOpeningRef.current) {
        isOpeningRef.current = false;
        return;
      }

      const target = event.target as HTMLElement;
      
      // Проверяем, что клик не внутри кнопки или dropdown
      const isInsideButton = buttonRef.current?.contains(target);
      const isInsideDropdown = dropdownRef.current?.contains(target);
      
      // Закрываем только если клик вне обоих элементов
      if (!isInsideButton && !isInsideDropdown) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const updatePosition = () => {
        if (buttonRef.current) {
          const rect = buttonRef.current.getBoundingClientRect();
          setDropdownPosition({
            top: rect.bottom + window.scrollY + 8,
            left: rect.left + window.scrollX,
            width: rect.width
          });
        }
      };
      
      updatePosition();
      window.addEventListener('scroll', updatePosition, true);
      window.addEventListener('resize', updatePosition);
      
      return () => {
        window.removeEventListener('scroll', updatePosition, true);
        window.removeEventListener('resize', updatePosition);
      };
    }
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
    <>
      <div className={`relative ${className}`}>
        <button
          ref={buttonRef}
          type="button"
          data-picker-id={pickerId}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            isOpeningRef.current = true;
            setIsOpen(!isOpen);
          }}
          className="w-full h-10 px-3 py-2 text-sm rounded-xl border border-gray-200 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 hover:bg-white dark:hover:bg-slate-800 hover:border-gray-300 dark:hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-left flex items-center justify-between backdrop-blur-sm"
        >
          <span className={value ? 'text-gray-900 dark:text-gray-100 font-medium' : 'text-gray-400 dark:text-slate-500'}>
            {value || 'Выбрать время'}
          </span>
          <Icon name="Clock" size={16} className="text-gray-400 dark:text-slate-500" />
        </button>
      </div>

      {isOpen && createPortal(
        <div 
          ref={dropdownRef}
          data-picker-id={pickerId}
          onMouseDown={(e) => e.stopPropagation()}
          onTouchStart={(e) => e.stopPropagation()}
          onClick={(e) => e.stopPropagation()}
          className="fixed z-[99999] bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-gray-200/60 dark:border-slate-700/60 rounded-2xl shadow-2xl p-4"
          style={{
            top: `${dropdownPosition.top}px`,
            left: `${dropdownPosition.left}px`,
            width: `${dropdownPosition.width}px`,
            minWidth: '200px'
          }}
        >
          <div className="mb-4">
            <div className="text-xs text-gray-500 dark:text-slate-400 mb-2 text-center font-semibold uppercase tracking-wide">Выберите время</div>
            <div className="max-h-64 overflow-y-auto border border-gray-200 dark:border-slate-700 rounded-xl bg-white/50 dark:bg-slate-900/50 scrollbar-thin">
              {hourOptions.map((h) => (
                <button
                  key={h}
                  type="button"
                  onMouseDown={(e) => e.stopPropagation()}
                  onTouchStart={(e) => e.stopPropagation()}
                  onClick={(e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    onChange(`${h}:00`);
                    setIsOpen(false);
                  }}
                  className={`w-full px-4 py-3 text-lg font-semibold text-center transition-all border-b border-gray-100 dark:border-slate-700 last:border-0 ${
                    value === `${h}:00` 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-900 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-slate-700 active:scale-95'
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
              onMouseDown={(e) => e.stopPropagation()}
              onTouchStart={(e) => e.stopPropagation()}
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                handleClear();
              }}
              className="w-full"
            >
              Очистить
            </Button>
          </div>
        </div>,
        document.body
      )}
    </>
  );
};

export default TimePicker;