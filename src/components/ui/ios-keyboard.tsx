import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';

interface IOSKeyboardProps {
  value: string;
  onChange: (value: string) => void;
  onClose: () => void;
  placeholder?: string;
}

export const IOSKeyboard = ({ value, onChange, onClose, placeholder = '0' }: IOSKeyboardProps) => {
  const [localValue, setLocalValue] = useState(value);
  const audioContextRef = useRef<AudioContext | null>(null);

  const playClickSound = () => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioContextRef.current;
      const now = ctx.currentTime;
      
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.frequency.value = 1200;
      osc.type = 'sine';
      
      gain.gain.setValueAtTime(0.1, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.05);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      osc.start(now);
      osc.stop(now + 0.05);
    } catch (error) {
      console.log('Звук недоступен');
    }
  };

  const playDeleteSound = () => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioContextRef.current;
      const now = ctx.currentTime;
      
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.frequency.value = 800;
      osc.type = 'sine';
      
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.04);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      osc.start(now);
      osc.stop(now + 0.04);
    } catch (error) {
      console.log('Звук недоступен');
    }
  };

  const handleNumberClick = (num: string) => {
    playClickSound();
    const newValue = localValue === '0' ? num : localValue + num;
    setLocalValue(newValue);
    onChange(newValue);
  };

  const handleDelete = () => {
    playDeleteSound();
    const newValue = localValue.slice(0, -1) || '0';
    setLocalValue(newValue);
    onChange(newValue);
  };

  const handleClear = () => {
    playDeleteSound();
    setLocalValue('0');
    onChange('0');
  };

  useEffect(() => {
    setLocalValue(value || '0');
  }, [value]);

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  return createPortal(
    <div className="fixed inset-0 z-[100000] flex flex-col justify-end animate-in slide-in-from-bottom duration-300">
      <div 
        className="flex-1 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />
      
      <div className="bg-gray-100 dark:bg-slate-900 border-t-2 border-gray-300 dark:border-slate-700 pb-safe">
        <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl px-4 py-3 border-b border-gray-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <button
              onClick={handleClear}
              className="text-blue-500 dark:text-blue-400 font-semibold text-lg active:scale-95 transition-transform"
            >
              Очистить
            </button>
            <button
              onClick={onClose}
              className="text-blue-500 dark:text-blue-400 font-semibold text-lg active:scale-95 transition-transform"
            >
              Готово
            </button>
          </div>
          <div className="text-4xl font-light text-right text-gray-900 dark:text-gray-100 min-h-[48px] flex items-center justify-end">
            {localValue || placeholder}
          </div>
        </div>

        <div className="p-2 grid grid-cols-3 gap-2">
          {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map((num) => (
            <button
              key={num}
              onClick={() => handleNumberClick(num)}
              className="bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100 text-3xl font-light h-16 rounded-xl active:scale-95 active:bg-gray-100 dark:active:bg-slate-700 transition-all duration-150 shadow-sm"
            >
              {num}
            </button>
          ))}
          
          <button
            onClick={handleClear}
            className="bg-gray-300 dark:bg-slate-700 text-gray-900 dark:text-gray-100 text-2xl font-medium h-16 rounded-xl active:scale-95 active:bg-gray-400 dark:active:bg-slate-600 transition-all duration-150 shadow-sm"
          >
            C
          </button>
          
          <button
            onClick={() => handleNumberClick('0')}
            className="bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100 text-3xl font-light h-16 rounded-xl active:scale-95 active:bg-gray-100 dark:active:bg-slate-700 transition-all duration-150 shadow-sm"
          >
            0
          </button>
          
          <button
            onClick={handleDelete}
            className="bg-gray-300 dark:bg-slate-700 text-gray-900 dark:text-gray-100 text-2xl font-medium h-16 rounded-xl active:scale-95 active:bg-gray-400 dark:active:bg-slate-600 transition-all duration-150 shadow-sm flex items-center justify-center"
          >
            ⌫
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default IOSKeyboard;