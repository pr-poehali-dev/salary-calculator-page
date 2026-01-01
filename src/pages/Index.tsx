import { useState, useMemo } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
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
  shift2Start: string;
  shift2End: string;
  orders: number;
  bonus: number;
}

const EMPLOYEES = ['Никита', 'Андрей', 'Денис'];
const COLORS = {
  'Никита': 'from-purple-500 to-pink-500',
  'Андрей': 'from-blue-500 to-cyan-500',
  'Денис': 'from-orange-500 to-red-500'
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

  const [scheduleData, setScheduleData] = useState<DayData[]>(() => {
    const data: DayData[] = [];
    const [year, month] = currentMonth.split('-').map(Number);
    
    for (let day = 1; day <= daysInMonth; day++) {
      EMPLOYEES.forEach(employee => {
        data.push({
          date: `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
          employee,
          shift1Start: '09:00',
          shift1End: '13:00',
          shift2Start: '14:00',
          shift2End: '18:00',
          orders: 0,
          bonus: 0
        });
      });
    }
    return data;
  });

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
    const hours2 = calculateHours(day.shift2Start, day.shift2End);
    const totalHours = hours1 + hours2;
    return (totalHours * 250) + (day.orders * (50 + day.bonus));
  };

  const updateSchedule = (date: string, employee: string, field: keyof DayData, value: any) => {
    setScheduleData(prev => prev.map(item => 
      item.date === date && item.employee === employee
        ? { ...item, [field]: value }
        : item
    ));
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
    setCurrentMonth(`${newDate.getFullYear()}-${String(newDate.getMonth() + 1).padStart(2, '0')}`);
    
    const newDaysInMonth = new Date(newDate.getFullYear(), newDate.getMonth() + 1, 0).getDate();
    const data: DayData[] = [];
    
    for (let day = 1; day <= newDaysInMonth; day++) {
      EMPLOYEES.forEach(employee => {
        data.push({
          date: `${newDate.getFullYear()}-${String(newDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
          employee,
          shift1Start: '09:00',
          shift1End: '13:00',
          shift2Start: '14:00',
          shift2End: '18:00',
          orders: 0,
          bonus: 0
        });
      });
    }
    setScheduleData(data);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted p-4 md:p-8">
      <div className="max-w-[1800px] mx-auto">
        <div className="text-center mb-8 animate-fade-in">
          <h1 className="text-4xl md:text-5xl font-bold font-heading mb-4 bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent animate-gradient bg-gradient">
            💰 Калькулятор зарплаты
          </h1>
          <p className="text-muted-foreground text-lg">
            Планирование расписания и расчёт зарплаты на месяц вперёд
          </p>
        </div>

        <Card className="p-6 mb-6 bg-gradient-to-br from-card to-muted/50 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-6">
            <Button
              onClick={() => changeMonth(-1)}
              variant="outline"
              className="hover:scale-105 transition-transform"
            >
              <Icon name="ChevronLeft" size={20} />
              Предыдущий
            </Button>
            <h2 className="text-2xl font-heading font-bold">
              {new Date(currentMonth + '-01').toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}
            </h2>
            <Button
              onClick={() => changeMonth(1)}
              variant="outline"
              className="hover:scale-105 transition-transform"
            >
              Следующий
              <Icon name="ChevronRight" size={20} />
            </Button>
          </div>

          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="font-bold text-center">Дата</TableHead>
                  <TableHead className="font-bold text-center">Имя</TableHead>
                  <TableHead className="font-bold text-center">Смена 1</TableHead>
                  <TableHead className="font-bold text-center">Смена 2</TableHead>
                  <TableHead className="font-bold text-center">Часы</TableHead>
                  <TableHead className="font-bold text-center">Заказы</TableHead>
                  <TableHead className="font-bold text-center">Доплата</TableHead>
                  <TableHead className="font-bold text-center">Итого за день</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.keys(groupedData).sort().map(date => (
                  groupedData[date].map((dayData, idx) => (
                    <TableRow 
                      key={`${date}-${dayData.employee}`}
                      className="hover:bg-muted/30 transition-colors"
                    >
                      {idx === 0 && (
                        <TableCell 
                          rowSpan={EMPLOYEES.length} 
                          className="font-semibold text-center align-middle bg-muted/20"
                        >
                          {formatDate(date)}
                        </TableCell>
                      )}
                      <TableCell className="text-center">
                        <div className="flex items-center justify-center gap-2">
                          <div className={`w-6 h-6 rounded-full bg-gradient-to-br ${COLORS[dayData.employee]} flex items-center justify-center text-xs font-bold text-white`}>
                            {dayData.employee[0]}
                          </div>
                          <span className="font-medium">{dayData.employee}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1 items-center justify-center">
                          <Input
                            type="time"
                            value={dayData.shift1Start}
                            onChange={(e) => updateSchedule(date, dayData.employee, 'shift1Start', e.target.value)}
                            className="w-24 h-8 text-xs"
                          />
                          <span>–</span>
                          <Input
                            type="time"
                            value={dayData.shift1End}
                            onChange={(e) => updateSchedule(date, dayData.employee, 'shift1End', e.target.value)}
                            className="w-24 h-8 text-xs"
                          />
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1 items-center justify-center">
                          <Input
                            type="time"
                            value={dayData.shift2Start}
                            onChange={(e) => updateSchedule(date, dayData.employee, 'shift2Start', e.target.value)}
                            className="w-24 h-8 text-xs"
                          />
                          <span>–</span>
                          <Input
                            type="time"
                            value={dayData.shift2End}
                            onChange={(e) => updateSchedule(date, dayData.employee, 'shift2End', e.target.value)}
                            className="w-24 h-8 text-xs"
                          />
                        </div>
                      </TableCell>
                      <TableCell className="text-center font-semibold">
                        {(calculateHours(dayData.shift1Start, dayData.shift1End) + 
                          calculateHours(dayData.shift2Start, dayData.shift2End)).toFixed(1)} ч
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          min="0"
                          value={dayData.orders}
                          onChange={(e) => updateSchedule(date, dayData.employee, 'orders', Number(e.target.value))}
                          className="w-20 h-8 text-center mx-auto"
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          min="0"
                          value={dayData.bonus}
                          onChange={(e) => updateSchedule(date, dayData.employee, 'bonus', Number(e.target.value))}
                          className="w-20 h-8 text-center mx-auto"
                        />
                      </TableCell>
                      <TableCell className="text-center">
                        <span className={`font-bold text-lg bg-gradient-to-r ${COLORS[dayData.employee]} bg-clip-text text-transparent`}>
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

        <Card className="p-8 bg-gradient-to-br from-card to-muted/50 backdrop-blur-sm animate-fade-in border-primary/20">
          <h3 className="text-3xl font-heading font-bold mb-6 flex items-center gap-3">
            <Icon name="TrendingUp" size={32} className="text-primary" />
            Итого за месяц
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {EMPLOYEES.map((emp, index) => (
              <div
                key={index}
                className="p-6 rounded-lg bg-gradient-to-br from-background to-muted/30 border border-border hover:scale-105 transition-transform duration-300"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${COLORS[emp]} flex items-center justify-center text-lg font-bold text-white`}>
                    {emp[0]}
                  </div>
                  <span className="font-semibold">{emp}</span>
                </div>
                <div className={`text-3xl font-heading font-bold bg-gradient-to-r ${COLORS[emp]} bg-clip-text text-transparent`}>
                  {getMonthTotal(emp).toLocaleString()}₽
                </div>
                <div className="text-sm text-muted-foreground mt-1">за весь месяц</div>
              </div>
            ))}
            <div className="p-6 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 border-2 border-primary hover:scale-105 transition-transform duration-300">
              <div className="flex items-center gap-2 mb-3">
                <Icon name="Wallet" size={24} className="text-primary" />
                <span className="font-semibold">Всего</span>
              </div>
              <div className="text-3xl font-heading font-bold bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
                {EMPLOYEES.reduce((sum, emp) => sum + getMonthTotal(emp), 0).toLocaleString()}₽
              </div>
              <div className="text-sm text-muted-foreground mt-1">месячный фонд</div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Index;
