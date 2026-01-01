import { useState, useMemo, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import Icon from '@/components/ui/icon';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

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

const Index = () => {
  const [currentMonth, setCurrentMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });

  const daysInMonth = useMemo(() => {
    const [year, month] = currentMonth.split('-').map(Number);
    return new Date(year, month, 0).getDate();
  }, [currentMonth]);

  const loadFromStorage = (month: string): DayData[] => {
    const saved = localStorage.getItem(`schedule_${month}`);
    if (saved) {
      return JSON.parse(saved);
    }
    
    const data: DayData[] = [];
    const [year, m] = month.split('-').map(Number);
    const days = new Date(year, m, 0).getDate();
    
    for (let day = 1; day <= days; day++) {
      EMPLOYEES.forEach(employee => {
        data.push({
          date: `${year}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
          employee,
          shift1Start: '09:00',
          shift1End: '18:00',
          hasShift2: false,
          shift2Start: '14:00',
          shift2End: '18:00',
          orders: 0,
          bonus: 0
        });
      });
    }
    return data;
  };

  const [scheduleData, setScheduleData] = useState<DayData[]>(() => loadFromStorage(currentMonth));

  useEffect(() => {
    localStorage.setItem(`schedule_${currentMonth}`, JSON.stringify(scheduleData));
  }, [scheduleData, currentMonth]);

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

  const updateSchedule = (date: string, employee: string, field: keyof DayData, value: any) => {
    setScheduleData(prev => {
      const updated = prev.map(item => 
        item.date === date && item.employee === employee
          ? { ...item, [field]: value }
          : item
      );
      return updated;
    });
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
    return `${String(date.getDate()).padStart(2, '0')}.${String(date.getMonth() + 1).padStart(2, '0')}`;
  };

  const changeMonth = (direction: number) => {
    const [year, month] = currentMonth.split('-').map(Number);
    const newDate = new Date(year, month - 1 + direction, 1);
    const newMonth = `${newDate.getFullYear()}-${String(newDate.getMonth() + 1).padStart(2, '0')}`;
    setCurrentMonth(newMonth);
    setScheduleData(loadFromStorage(newMonth));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted p-2 md:p-4">
      <div className="max-w-[1600px] mx-auto">
        <div className="text-center mb-4 animate-fade-in">
          <h1 className="text-3xl md:text-4xl font-bold font-heading mb-2 bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
            💰 Калькулятор зарплаты
          </h1>
        </div>

        <Card className="p-3 mb-4 bg-card/95 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-3">
            <Button
              onClick={() => changeMonth(-1)}
              variant="outline"
              size="sm"
            >
              <Icon name="ChevronLeft" size={16} />
            </Button>
            <h2 className="text-lg font-heading font-bold">
              {new Date(currentMonth + '-01').toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}
            </h2>
            <Button
              onClick={() => changeMonth(1)}
              variant="outline"
              size="sm"
            >
              <Icon name="ChevronRight" size={16} />
            </Button>
          </div>

          <div className="overflow-x-auto -mx-3">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="font-bold text-xs p-2 text-center sticky left-0 bg-muted/50 z-10">Дата</TableHead>
                  <TableHead className="font-bold text-xs p-2 text-center">Имя</TableHead>
                  <TableHead className="font-bold text-xs p-2 text-center">Время работы</TableHead>
                  <TableHead className="font-bold text-xs p-2 text-center">+Смена</TableHead>
                  <TableHead className="font-bold text-xs p-2 text-center">Час.</TableHead>
                  <TableHead className="font-bold text-xs p-2 text-center">Зак.</TableHead>
                  <TableHead className="font-bold text-xs p-2 text-center">Допл.</TableHead>
                  <TableHead className="font-bold text-xs p-2 text-center">Итого</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.keys(groupedData).sort().map(date => (
                  groupedData[date].map((dayData, idx) => (
                    <TableRow 
                      key={`${date}-${dayData.employee}`}
                      className="hover:bg-muted/20 transition-colors"
                    >
                      {idx === 0 && (
                        <TableCell 
                          rowSpan={EMPLOYEES.length} 
                          className="font-semibold text-xs p-2 text-center align-middle bg-muted/20 sticky left-0 z-10"
                        >
                          {formatDate(date)}
                        </TableCell>
                      )}
                      <TableCell className="p-2">
                        <div className="flex items-center gap-1">
                          <div className={`w-4 h-4 rounded-full ${COLORS[dayData.employee]}`} />
                          <span className="text-xs font-medium">{dayData.employee}</span>
                        </div>
                      </TableCell>
                      <TableCell className="p-2">
                        <div className="flex flex-col gap-1">
                          <div className="flex gap-1 items-center">
                            <Input
                              type="time"
                              value={dayData.shift1Start}
                              onChange={(e) => updateSchedule(date, dayData.employee, 'shift1Start', e.target.value)}
                              className="w-20 h-7 text-xs p-1"
                            />
                            <span className="text-xs">–</span>
                            <Input
                              type="time"
                              value={dayData.shift1End}
                              onChange={(e) => updateSchedule(date, dayData.employee, 'shift1End', e.target.value)}
                              className="w-20 h-7 text-xs p-1"
                            />
                          </div>
                          {dayData.hasShift2 && (
                            <div className="flex gap-1 items-center">
                              <Input
                                type="time"
                                value={dayData.shift2Start}
                                onChange={(e) => updateSchedule(date, dayData.employee, 'shift2Start', e.target.value)}
                                className="w-20 h-7 text-xs p-1"
                              />
                              <span className="text-xs">–</span>
                              <Input
                                type="time"
                                value={dayData.shift2End}
                                onChange={(e) => updateSchedule(date, dayData.employee, 'shift2End', e.target.value)}
                                className="w-20 h-7 text-xs p-1"
                              />
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="p-2 text-center">
                        <Checkbox
                          checked={dayData.hasShift2}
                          onCheckedChange={(checked) => updateSchedule(date, dayData.employee, 'hasShift2', checked)}
                        />
                      </TableCell>
                      <TableCell className="text-center font-semibold text-xs p-2">
                        {(calculateHours(dayData.shift1Start, dayData.shift1End) + 
                          (dayData.hasShift2 ? calculateHours(dayData.shift2Start, dayData.shift2End) : 0)).toFixed(1)}
                      </TableCell>
                      <TableCell className="p-2">
                        <Input
                          type="number"
                          min="0"
                          value={dayData.orders}
                          onChange={(e) => updateSchedule(date, dayData.employee, 'orders', Number(e.target.value))}
                          className="w-14 h-7 text-xs text-center p-1"
                        />
                      </TableCell>
                      <TableCell className="p-2">
                        <Input
                          type="number"
                          min="0"
                          value={dayData.bonus}
                          onChange={(e) => updateSchedule(date, dayData.employee, 'bonus', Number(e.target.value))}
                          className="w-14 h-7 text-xs text-center p-1"
                        />
                      </TableCell>
                      <TableCell className="text-center p-2">
                        <span className="font-bold text-sm text-primary">
                          {calculateDaySalary(dayData).toFixed(0)}₽
                        </span>
                      </TableCell>
                    </TableRow>
                  ))
                ))}
              </TableBody>
            </Table>
          </div>
        </Card>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {EMPLOYEES.map((emp) => (
            <Card
              key={emp}
              className="p-4 bg-card/95 backdrop-blur-sm hover:scale-105 transition-transform"
            >
              <div className="flex items-center gap-2 mb-2">
                <div className={`w-8 h-8 rounded-full ${COLORS[emp]}`} />
                <span className="font-semibold text-sm">{emp}</span>
              </div>
              <div className="text-2xl font-heading font-bold text-primary">
                {getMonthTotal(emp).toLocaleString()}₽
              </div>
              <div className="text-xs text-muted-foreground">за месяц</div>
            </Card>
          ))}
          <Card className="p-4 bg-gradient-to-br from-primary/20 to-accent/20 border-2 border-primary hover:scale-105 transition-transform">
            <div className="flex items-center gap-2 mb-2">
              <Icon name="Wallet" size={20} className="text-primary" />
              <span className="font-semibold text-sm">Всего</span>
            </div>
            <div className="text-2xl font-heading font-bold text-primary">
              {EMPLOYEES.reduce((sum, emp) => sum + getMonthTotal(emp), 0).toLocaleString()}₽
            </div>
            <div className="text-xs text-muted-foreground">общий фонд</div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Index;