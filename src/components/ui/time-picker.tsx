import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import Icon from './icon';

interface TimePickerProps {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export const TimePicker = ({ value, onChange, className = '' }: TimePickerProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0, width: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const hourOptions = [
    '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '00', '01'
  ];

  const updatePosition = () => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const isMobile = window.innerWidth < 768;
      
      if (isMobile) {
        setPosition({
          top: window.innerHeight / 2 - 200,
          left: window.innerWidth / 2 - 150,
          width: 300
        });
      } else {
        setPosition({
          top: rect.bottom + window.scrollY + 8,
          left: rect.left + window.scrollX,
          width: rect.width
        });
      }
    }
  };

  const handleToggle = () => {
    if (!isOpen) {
      updatePosition();
    }
    setIsOpen(!isOpen);
  };

  const handleSelect = (time: string) => {
    onChange(time);
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange('');
    setIsOpen(false);
  };

  useEffect(() => {
    if (!isOpen) return;

    const handleClick = (e: Event) => {
      const target = e.target as Node;
      
      if (
        dropdownRef.current?.contains(target) ||
        buttonRef.current?.contains(target)
      ) {
        return;
      }

      setIsOpen(false);
    };

    document.addEventListener('click', handleClick, true);
    document.addEventListener('touchend', handleClick, true);

    return () => {
      document.removeEventListener('click', handleClick, true);
      document.removeEventListener('touchend', handleClick, true);
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const handleScroll = () => updatePosition();
    const handleResize = () => updatePosition();

    window.addEventListener('scroll', handleScroll, true);
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('scroll', handleScroll, true);
      window.removeEventListener('resize', handleResize);
    };
  }, [isOpen]);

  return (
    <>
      <div className={className}>
        <button
          ref={buttonRef}
          type="button"
          onClick={handleToggle}
          className="w-full h-10 px-3 py-2 text-sm rounded-xl border border-gray-200 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 hover:bg-white dark:hover:bg-slate-800 hover:border-gray-300 dark:hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-left flex items-center justify-between backdrop-blur-sm"
        >
          <span className={value ? 'text-gray-900 dark:text-gray-100 font-medium' : 'text-gray-400 dark:text-slate-500'}>
            {value || 'Выбрать время'}
          </span>
          <Icon name="Clock" size={16} className="text-gray-400 dark:text-slate-500" />
        </button>
      </div>

      {isOpen && createPortal(
        <>
          <div 
            className="fixed inset-0 z-[99998] bg-black/20"
            onClick={() => setIsOpen(false)}
          />
          <div
            ref={dropdownRef}
            className="fixed z-[99999] bg-white dark:bg-slate-800 border-2 border-gray-300 dark:border-slate-600 rounded-2xl shadow-2xl p-4"
            style={{
              top: `${position.top}px`,
              left: `${position.left}px`,
              width: `${position.width}px`,
              minWidth: '200px',
              maxHeight: '400px',
              transform: window.innerWidth < 768 ? 'translate(-50%, -50%)' : 'none'
            }}
          >
          <div className="mb-3">
            <div className="text-xs text-gray-500 dark:text-slate-400 mb-2 text-center font-semibold uppercase tracking-wide">
              Выберите время
            </div>
            <div className="max-h-72 overflow-y-auto border border-gray-200 dark:border-slate-700 rounded-xl bg-white/50 dark:bg-slate-900/50">
              {hourOptions.map((h) => (
                <button
                  key={h}
                  type="button"
                  onClick={() => handleSelect(`${h}:00`)}
                  className={`w-full px-4 py-3 text-lg font-semibold text-center transition-all border-b border-gray-100 dark:border-slate-700 last:border-0 ${
                    value === `${h}:00`
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-900 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-slate-700 active:bg-blue-100 dark:active:bg-slate-600'
                  }`}
                >
                  {h}:00
                </button>
              ))}
            </div>
          </div>

          <button
            type="button"
            onClick={handleClear}
            className="w-full px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 rounded-xl transition-all"
          >
            Очистить
          </button>
        </div>
        </>,
        document.body
      )}
    </>
  );
};

export default TimePicker;