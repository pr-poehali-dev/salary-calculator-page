import { useState, useMemo, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import Icon from '@/components/ui/icon';
import TimePicker from '@/components/ui/time-picker';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { toast } from 'sonner';

interface DayData {
  date: string;
  employee: string;
  shift1Start: string;
  shift1End: string;
  hasShift2: boolean;
  shift2Start: string;
  shift2End: string;
  orders: number;
  bonus: number;
}

const EMPLOYEES = ['Никита', 'Андрей', 'Денис'];
const COLORS = {
  'Никита': 'bg-purple-500',
  'Андрей': 'bg-blue-500',
  'Денис': 'bg-orange-500'
};

const API_URL = 'https://functions.poehali.dev/5a203b28-37f5-4d7d-b66f-147c4de8c7c0';

const Index = () => {
  const [currentMonth, setCurrentMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });

  const [scheduleData, setScheduleData] = useState<DayData[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'edit' | 'view'>('view');
  const [menuOpen, setMenuOpen] = useState(false);
  const [savedCards, setSavedCards] = useState<Set<string>>(new Set());
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isSavingRef = useRef(false);
  const pendingChangesRef = useRef<Set<string>>(new Set());
  const audioContextRef = useRef<AudioContext | null>(null);

  const daysInMonth = useMemo(() => {
    const [year, month] = currentMonth.split('-').map(Number);
    return new Date(year, month, 0).getDate();
  }, [currentMonth]);

  const loadSchedule = async (month: string, silent = false) => {
    try {
      if (!silent) setLoading(true);
      const response = await fetch(`${API_URL}?month=${month}`);
      const data = await response.json();
      
      // ВСЕГДА создаем полное расписание на весь месяц
      const [year, m] = month.split('-').map(Number);
      const days = new Date(year, m, 0).getDate();
      const fullSchedule: DayData[] = [];
      
      for (let day = 1; day <= days; day++) {
        const dateStr = `${year}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        
        EMPLOYEES.forEach((employee) => {
          // Ищем существующие данные из базы
          const existing = data?.find((d: DayData) => d.date === dateStr && d.employee === employee);
          
          fullSchedule.push(existing || {
            date: dateStr,
            employee,
            shift1Start: '',
            shift1End: '',
            hasShift2: false,
            shift2Start: '',
            shift2End: '',
            orders: 0,
            bonus: 0
          });
        });
      }
      
      // При тихом обновлении сохраняем изменения которые сейчас редактируются
      if (silent) {
        setScheduleData(prev => {
          return fullSchedule.map(newItem => {
            const key = `${newItem.date}-${newItem.employee}`;
            // Если это поле сейчас редактируется - не перезаписываем
            if (pendingChangesRef.current.has(key)) {
              const oldItem = prev.find(p => p.date === newItem.date && p.employee === newItem.employee);
              return oldItem || newItem;
            }
            return newItem;
          });
        });
      } else {
        setScheduleData(fullSchedule);
      }
      
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Ошибка загрузки:', error);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    loadSchedule(currentMonth, false);
  }, [currentMonth]);

  useEffect(() => {
    const interval = setInterval(() => {
      // Тихое обновление без перезагрузки UI
      if (!isSavingRef.current) {
        loadSchedule(currentMonth, true);
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [currentMonth]);

  const playSuccessSound = () => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioContextRef.current;
      const now = ctx.currentTime;
      
      // Создаем звук как у Apple Pay - два тона
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc1.frequency.value = 1000; // Первый тон
      osc2.frequency.value = 1200; // Второй тон выше
      osc1.type = 'sine';
      osc2.type = 'sine';
      
      gain.gain.setValueAtTime(0.3, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
      
      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);
      
      osc1.start(now);
      osc2.start(now + 0.05); // Второй тон чуть позже
      osc1.stop(now + 0.1);
      osc2.stop(now + 0.15);
    } catch (error) {
      console.log('Звук недоступен');
    }
  };

  const saveToDatabase = async (items: DayData[]) => {
    try {
      isSavingRef.current = true;
      setSaving(true);
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items })
      });
      
      if (response.ok) {
        playSuccessSound();
        toast.success('Сохранено');
      }
      
      pendingChangesRef.current.clear();
    } catch (error) {
      console.error('Ошибка сохранения:', error);
      toast.error('Ошибка сохранения');
    } finally {
      setSaving(false);
      isSavingRef.current = false;
    }
  };

  const updateSchedule = (date: string, employee: string, field: keyof DayData, value: any) => {
    // Помечаем что это поле редактируется
    const key = `${date}-${employee}`;
    pendingChangesRef.current.add(key);
    
    setScheduleData(prev => {
      let updated = [...prev];
      
      if (field === 'bonus') {
        updated = updated.map(item => 
          item.date === date
            ? { ...item, bonus: value }
            : item
        );
      } else {
        updated = updated.map(item => 
          item.date === date && item.employee === employee
            ? { ...item, [field]: value }
            : item
        );
      }
      
      // Сохраняем с задержкой, чтобы не перегружать сервер
      if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
      saveTimeoutRef.current = setTimeout(() => {
        saveToDatabase(updated);
      }, 500);
      
      return updated;
    });
  };

  const calculateHours = (start: string, end: string): number => {
    if (!start || !end) return 0;
    const [startHour, startMin] = start.split(':').map(Number);
    const [endHour, endMin] = end.split(':').map(Number);
    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;
    return (endMinutes - startMinutes) / 60;
  };

  const calculateDaySalary = (day: DayData): number => {
    const hours1 = calculateHours(day.shift1Start, day.shift1End);
    const hours2 = day.hasShift2 ? calculateHours(day.shift2Start, day.shift2End) : 0;
    const totalHours = hours1 + hours2;
    return (totalHours * 250) + (day.orders * (50 + day.bonus));
  };

  const getMonthTotal = (employee: string): number => {
    return scheduleData
      .filter(d => d.employee === employee)
      .reduce((sum, day) => sum + calculateDaySalary(day), 0);
  };

  const groupedData = useMemo(() => {
    const grouped: { [key: string]: DayData[] } = {};
    scheduleData.forEach(item => {
      if (!grouped[item.date]) grouped[item.date] = [];
      grouped[item.date].push(item);
    });
    return grouped;
  }, [scheduleData]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const day = date.getDate();
    const weekday = date.toLocaleDateString('ru-RU', { weekday: 'short' });
    return { day, weekday };
  };

  const changeMonth = (direction: number) => {
    const [year, month] = currentMonth.split('-').map(Number);
    const newDate = new Date(year, month - 1 + direction, 1);
    const newMonth = `${newDate.getFullYear()}-${String(newDate.getMonth() + 1).padStart(2, '0')}`;
    setCurrentMonth(newMonth);
  };

  const clearAllData = async () => {
    if (!confirm('Удалить все данные за текущий месяц?')) return;
    
    const emptyData: DayData[] = [];
    const [year, m] = currentMonth.split('-').map(Number);
    const days = new Date(year, m, 0).getDate();
    
    for (let day = 1; day <= days; day++) {
      const dateStr = `${year}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      EMPLOYEES.forEach((employee) => {
        emptyData.push({
          date: dateStr,
          employee,
          shift1Start: '',
          shift1End: '',
          hasShift2: false,
          shift2Start: '',
          shift2End: '',
          orders: 0,
          bonus: 0
        });
      });
    }
    
    setScheduleData(emptyData);
    await saveToDatabase(emptyData);
  };

  const filteredData = useMemo(() => {
    if (viewMode === 'view') {
      // В режиме просмотра показываем только заполненные дни
      const withData: { [key: string]: DayData[] } = {};
      Object.keys(groupedData).forEach(date => {
        const dayData = selectedEmployee 
          ? groupedData[date].filter(d => d.employee === selectedEmployee)
          : groupedData[date];
        
        const hasData = dayData.some(d => d.shift1Start || d.shift1End || d.orders > 0);
        if (hasData) {
          withData[date] = dayData;
        }
      });
      return withData;
    } else {
      // В режиме редактора показываем ВСЕ дни месяца
      if (!selectedEmployee) return groupedData;
      
      const filtered: { [key: string]: DayData[] } = {};
      Object.keys(groupedData).forEach(date => {
        const employeeData = groupedData[date].filter(d => d.employee === selectedEmployee);
        if (employeeData.length > 0) {
          filtered[date] = employeeData;
        }
      });
      return filtered;
    }
  }, [groupedData, selectedEmployee, viewMode]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted flex items-center justify-center">
        <div className="text-center">
          <Icon name="Loader2" className="animate-spin mx-auto mb-4" size={48} />
          <p className="text-muted-foreground">Загрузка...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted">
      <div className="sticky top-0 z-20 bg-background/95 backdrop-blur-sm border-b border-border shadow-sm">
        <div className="max-w-7xl mx-auto px-3 py-2">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
                <SheetTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Icon name="Menu" size={18} />
                  </Button>
                </SheetTrigger>
                <SheetContent side="left">
                  <SheetHeader>
                    <SheetTitle>Меню</SheetTitle>
                  </SheetHeader>
                  <div className="mt-6 space-y-4">
                    {viewMode === 'view' && (
                      <Button
                        onClick={() => {
                          setViewMode('edit');
                          setMenuOpen(false);
                        }}
                        className="w-full"
                        size="sm"
                      >
                        <Icon name="Edit" size={16} className="mr-2" />
                        Редактировать расписание
                      </Button>
                    )}

                    {viewMode === 'edit' && (
                      <>
                        <Button
                          onClick={() => {
                            setViewMode('view');
                            setMenuOpen(false);
                          }}
                          variant="outline"
                          className="w-full"
                          size="sm"
                        >
                          <Icon name="Eye" size={16} className="mr-2" />
                          Вернуться к просмотру
                        </Button>
                        <Button
                          onClick={() => {
                            clearAllData();
                            setMenuOpen(false);
                          }}
                          variant="outline"
                          className="w-full text-destructive hover:text-destructive"
                          size="sm"
                        >
                          <Icon name="Trash2" size={16} className="mr-2" />
                          Очистить все данные
                        </Button>
                      </>
                    )}

                    <div className="pt-4 border-t">
                      <p className="text-sm font-semibold mb-3">Фильтр по сотруднику</p>
                      <div className="space-y-2">
                        <Button
                          variant={selectedEmployee === null ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => {
                            setSelectedEmployee(null);
                            setMenuOpen(false);
                          }}
                          className="w-full justify-start"
                        >
                          Все сотрудники
                        </Button>
                        {EMPLOYEES.map(emp => (
                          <Button
                            key={emp}
                            variant={selectedEmployee === emp ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => {
                              setSelectedEmployee(emp);
                              setMenuOpen(false);
                            }}
                            className="w-full justify-start"
                          >
                            <div className={`w-3 h-3 rounded-full ${COLORS[emp]} mr-2`} />
                            {emp}
                          </Button>
                        ))}
                      </div>
                    </div>
                  </div>
                </SheetContent>
              </Sheet>

              <Button onClick={() => changeMonth(-1)} variant="outline" size="sm">
                <Icon name="ChevronLeft" size={16} />
              </Button>
            </div>

            <div className="flex-1 text-center font-semibold text-sm">
              {new Date(currentMonth + '-01').toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}
            </div>

            <div className="flex items-center gap-2">
              <Button onClick={() => changeMonth(1)} variant="outline" size="sm">
                <Icon name="ChevronRight" size={16} />
              </Button>
              {saving && (
                <Icon name="Cloud" size={16} className="animate-pulse text-muted-foreground" />
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-3 pb-32 overflow-visible">
        {viewMode === 'edit' ? (
          <div className="space-y-2 overflow-visible">
            {Object.keys(filteredData).sort().map(date => {
              const { day, weekday } = formatDate(date);
              const dayBonus = filteredData[date][0]?.bonus || 0;
            
            return (
              <Card key={date} className="overflow-visible">
                <div className="bg-muted/30 px-2 py-1.5 border-b border-border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="text-lg font-bold">{day}</div>
                      <div className="text-xs text-muted-foreground uppercase">{weekday}</div>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-muted-foreground">Доплата:</span>
                      <Input
                        type="number"
                        min="0"
                        value={dayBonus || ''}
                        onChange={(e) => updateSchedule(date, '', 'bonus', parseInt(e.target.value) || 0)}
                        className="w-14 h-7 text-xs"
                      />
                    </div>
                  </div>
                </div>

                <div className="p-2 space-y-2">
                  {filteredData[date].map((dayData) => {
                    const salary = calculateDaySalary(dayData);
                    const hours1 = calculateHours(dayData.shift1Start, dayData.shift1End);
                    const hours2 = dayData.hasShift2 ? calculateHours(dayData.shift2Start, dayData.shift2End) : 0;
                    
                    return (
                      <div key={`${date}-${dayData.employee}`} className="border border-border rounded-lg p-2">
                        <div className="flex items-center gap-2 mb-2">
                          <div className={`w-3 h-3 rounded-full ${COLORS[dayData.employee]}`} />
                          <span className="font-semibold text-sm">{dayData.employee}</span>
                          {salary > 0 && (
                            <span className="ml-auto text-sm font-bold text-primary">
                              {salary.toLocaleString('ru-RU')} ₽
                            </span>
                          )}
                        </div>

                        <div className="space-y-2">
                          <div>
                            <div className="text-xs text-muted-foreground mb-0.5">Смена 1 {hours1 > 0 && <span className="font-medium text-foreground">({hours1.toFixed(1)}ч)</span>}</div>
                            <div className="flex gap-1 items-center">
                              <TimePicker
                                value={dayData.shift1Start}
                                onChange={(val) => updateSchedule(date, dayData.employee, 'shift1Start', val)}
                                className="flex-1"
                              />
                              <span className="text-muted-foreground text-xs">—</span>
                              <TimePicker
                                value={dayData.shift1End}
                                onChange={(val) => updateSchedule(date, dayData.employee, 'shift1End', val)}
                                className="flex-1"
                              />
                            </div>
                          </div>

                          <div className="flex items-center gap-1.5">
                            <Checkbox
                              checked={dayData.hasShift2}
                              onCheckedChange={(checked) => 
                                updateSchedule(date, dayData.employee, 'hasShift2', checked)
                              }
                              className="h-4 w-4"
                            />
                            <span className="text-xs">Вторая смена</span>
                          </div>

                          {dayData.hasShift2 && (
                            <div>
                              <div className="text-xs text-muted-foreground mb-0.5">Смена 2 {hours2 > 0 && <span className="font-medium text-foreground">({hours2.toFixed(1)}ч)</span>}</div>
                              <div className="flex gap-1 items-center">
                                <TimePicker
                                  value={dayData.shift2Start}
                                  onChange={(val) => updateSchedule(date, dayData.employee, 'shift2Start', val)}
                                  className="flex-1"
                                />
                                <span className="text-muted-foreground text-xs">—</span>
                                <TimePicker
                                  value={dayData.shift2End}
                                  onChange={(val) => updateSchedule(date, dayData.employee, 'shift2End', val)}
                                  className="flex-1"
                                />
                              </div>
                            </div>
                          )}

                          <div>
                            <label className="text-xs text-muted-foreground block mb-0.5">Заказов {dayData.orders > 0 && <span className="font-medium text-foreground">({(dayData.orders * (50 + dayData.bonus))}₽)</span>}</label>
                            <Input
                              type="number"
                              min="0"
                              value={dayData.orders || ''}
                              onChange={(e) => updateSchedule(date, dayData.employee, 'orders', parseInt(e.target.value) || 0)}
                              className="h-8 text-sm"
                            />
                          </div>

                          <Button 
                            variant={savedCards.has(`${date}-${dayData.employee}`) ? 'default' : 'outline'}
                            size="sm" 
                            className="w-full h-7 text-xs transition-all"
                            onClick={() => {
                              const cardId = `${date}-${dayData.employee}`;
                              setSavedCards(prev => new Set(prev).add(cardId));
                              
                              toast.success('Данные сохранены', {
                                description: `${dayData.employee} • ${formatDate(date).day} ${formatDate(date).weekday}`,
                                duration: 2000,
                                icon: '💾',
                                style: {
                                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                  border: 'none',
                                  color: 'white',
                                },
                              });
                              
                              setTimeout(() => {
                                setSavedCards(prev => {
                                  const next = new Set(prev);
                                  next.delete(cardId);
                                  return next;
                                });
                              }, 2000);
                            }}
                          >
                            <Icon name={savedCards.has(`${date}-${dayData.employee}`) ? 'Check' : 'Save'} size={14} className="mr-1" />
                            {savedCards.has(`${date}-${dayData.employee}`) ? 'Сохранено' : 'Сохранить'}
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>
            );
          })}
          </div>
        ) : (
          <div className="space-y-2">
            {Object.keys(filteredData).sort().map(date => {
              const { day, weekday } = formatDate(date);
              const dayData = filteredData[date];
              const dayBonus = dayData[0]?.bonus || 0;
              
              const hasAnyData = dayData.some(d => 
                d.shift1Start || d.shift1End || d.orders > 0 || d.hasShift2
              );

              if (!hasAnyData) return null;
              
              return (
                <Card key={date} className="overflow-hidden">
                  <div className="bg-muted/30 px-2 py-1 border-b border-border">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <div className="text-base font-bold">{day}</div>
                        <div className="text-xs text-muted-foreground uppercase">{weekday}</div>
                      </div>
                      {dayBonus > 0 && (
                        <div className="text-xs text-muted-foreground">
                          +{dayBonus}₽
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="p-2">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      {dayData.map((data) => {
                        const salary = calculateDaySalary(data);
                        const hours1 = calculateHours(data.shift1Start, data.shift1End);
                        const hours2 = data.hasShift2 ? calculateHours(data.shift2Start, data.shift2End) : 0;
                        const totalHours = hours1 + hours2;
                        
                        if (!data.shift1Start && !data.orders) return null;
                        
                        return (
                          <div key={`${date}-${data.employee}`} 
                               className="border border-border rounded-lg p-2 space-y-1">
                            <div className="flex items-center justify-between mb-1">
                              <div className="flex items-center gap-1.5">
                                <div className={`w-2.5 h-2.5 rounded-full ${COLORS[data.employee]}`} />
                                <span className="font-semibold text-xs">{data.employee}</span>
                              </div>
                              {salary > 0 && (
                                <div className="text-sm font-bold text-primary">
                                  {salary.toLocaleString('ru-RU')} ₽
                                </div>
                              )}
                            </div>

                            {(data.shift1Start || data.shift1End) && (
                              <div className="text-xs">
                                <div className="font-medium">
                                  {data.shift1Start || '—'} – {data.shift1End || '—'}
                                </div>
                                {data.hasShift2 && (
                                  <div className="font-medium">
                                    {data.shift2Start || '—'} – {data.shift2End || '—'}
                                  </div>
                                )}
                              </div>
                            )}

                            <div className="flex items-center justify-between text-xs text-muted-foreground">
                              {totalHours > 0 && <span>{totalHours.toFixed(1)}ч</span>}
                              {data.orders > 0 && <span>{data.orders} зак.</span>}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      <div className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur-sm border-t border-border p-3 shadow-lg">
        <div className="max-w-7xl mx-auto">
          <div className="text-xs md:text-sm text-muted-foreground mb-2">Итого за месяц:</div>
          <div className="space-y-1 md:space-y-2">
            {EMPLOYEES.map(emp => {
              const total = getMonthTotal(emp);
              if (selectedEmployee && selectedEmployee !== emp) return null;
              
              return (
                <div key={emp} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${COLORS[emp]}`} />
                    <span className="font-medium text-sm md:text-base">{emp}</span>
                  </div>
                  <span className="text-base md:text-lg font-bold">
                    {total.toLocaleString('ru-RU')} ₽
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;