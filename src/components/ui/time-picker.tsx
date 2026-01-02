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
      
      setPosition({
        top: rect.top + window.scrollY - 360,
        left: rect.left + window.scrollX,
        width: rect.width
      });
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
            className="fixed inset-0 z-[99998] bg-black/20 backdrop-blur-sm animate-in fade-in duration-200"
            onClick={() => setIsOpen(false)}
          />
          <div
            ref={dropdownRef}
            className="absolute z-[99999] bg-white/98 dark:bg-slate-900/98 backdrop-blur-2xl border border-gray-200/50 dark:border-slate-700/50 rounded-3xl shadow-[0_20px_60px_-15px_rgba(0,0,0,0.4)] p-4 animate-in fade-in zoom-in-95 slide-in-from-top-2 duration-300"
            style={{
              top: `${position.top}px`,
              left: `${position.left}px`,
              width: `${position.width}px`,
              minWidth: '280px',
              maxHeight: '380px'
            }}
          >
          <div className="mb-3">
            <div className="text-xs font-semibold text-gray-400 dark:text-slate-500 mb-3 text-center uppercase tracking-wider">
              Выберите время
            </div>
            <div className="max-h-64 overflow-y-auto rounded-2xl bg-gray-50/80 dark:bg-slate-950/50 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-slate-700">
              {hourOptions.map((h) => (
                <button
                  key={h}
                  type="button"
                  onClick={() => handleSelect(`${h}:00`)}
                  className={`w-full px-5 py-3.5 text-xl font-semibold text-center transition-all duration-200 border-b border-gray-200/50 dark:border-slate-800/50 last:border-0 ${
                    value === `${h}:00`
                      ? 'bg-blue-500 text-white scale-[1.02]'
                      : 'text-gray-900 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-slate-800/70 active:scale-95'
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
            className="w-full px-5 py-3 text-base font-semibold text-gray-600 dark:text-gray-400 bg-gray-100/80 dark:bg-slate-800/80 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-2xl transition-all duration-200 active:scale-95"
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