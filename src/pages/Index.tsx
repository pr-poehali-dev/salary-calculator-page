import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';

interface WorkShift {
  startTime: string;
  endTime: string;
}

interface EmployeeData {
  name: string;
  color: string;
  shifts: [WorkShift, WorkShift];
  orders: number;
  bonus: number;
}

const Index = () => {
  const [employees, setEmployees] = useState<EmployeeData[]>([
    {
      name: 'Никита',
      color: 'from-purple-500 to-pink-500',
      shifts: [
        { startTime: '09:00', endTime: '13:00' },
        { startTime: '14:00', endTime: '18:00' }
      ],
      orders: 0,
      bonus: 0
    },
    {
      name: 'Андрей',
      color: 'from-blue-500 to-cyan-500',
      shifts: [
        { startTime: '09:00', endTime: '13:00' },
        { startTime: '14:00', endTime: '18:00' }
      ],
      orders: 0,
      bonus: 0
    },
    {
      name: 'Денис',
      color: 'from-orange-500 to-red-500',
      shifts: [
        { startTime: '09:00', endTime: '13:00' },
        { startTime: '14:00', endTime: '18:00' }
      ],
      orders: 0,
      bonus: 0
    }
  ]);

  const calculateHours = (shift: WorkShift): number => {
    if (!shift.startTime || !shift.endTime) return 0;
    const [startHour, startMin] = shift.startTime.split(':').map(Number);
    const [endHour, endMin] = shift.endTime.split(':').map(Number);
    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;
    return (endMinutes - startMinutes) / 60;
  };

  const calculateSalary = (emp: EmployeeData): number => {
    const totalHours = emp.shifts.reduce((sum, shift) => sum + calculateHours(shift), 0);
    return (totalHours * 250) + (emp.orders * (50 + emp.bonus));
  };

  const updateEmployee = (index: number, field: keyof EmployeeData | string, value: any) => {
    setEmployees(prev => {
      const newEmployees = [...prev];
      if (field.includes('.')) {
        const [mainField, shiftIndex, subField] = field.split('.');
        if (mainField === 'shifts') {
          newEmployees[index].shifts[Number(shiftIndex)] = {
            ...newEmployees[index].shifts[Number(shiftIndex)],
            [subField]: value
          };
        }
      } else {
        newEmployees[index] = { ...newEmployees[index], [field]: value };
      }
      return newEmployees;
    });
  };

  const resetEmployee = (index: number) => {
    setEmployees(prev => {
      const newEmployees = [...prev];
      newEmployees[index] = {
        ...newEmployees[index],
        shifts: [
          { startTime: '09:00', endTime: '13:00' },
          { startTime: '14:00', endTime: '18:00' }
        ],
        orders: 0,
        bonus: 0
      };
      return newEmployees;
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12 animate-fade-in">
          <h1 className="text-5xl md:text-6xl font-bold font-heading mb-4 bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent animate-gradient bg-gradient">
            💰 Калькулятор зарплаты
          </h1>
          <p className="text-muted-foreground text-lg">
            Рассчитывайте зарплату для команды в режиме реального времени
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {employees.map((emp, empIndex) => {
            const totalHours = emp.shifts.reduce((sum, shift) => sum + calculateHours(shift), 0);
            const salary = calculateSalary(emp);

            return (
              <Card
                key={empIndex}
                className="relative overflow-hidden animate-scale-in hover:scale-105 transition-transform duration-300"
                style={{ animationDelay: `${empIndex * 0.1}s` }}
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${emp.color} opacity-10`} />
                
                <div className="relative p-6 space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${emp.color} flex items-center justify-center text-2xl font-bold text-white shadow-lg`}>
                        {emp.name[0]}
                      </div>
                      <h2 className="text-2xl font-heading font-bold">{emp.name}</h2>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => resetEmployee(empIndex)}
                      className="hover:bg-destructive/10 hover:text-destructive"
                    >
                      <Icon name="RotateCcw" size={20} />
                    </Button>
                  </div>

                  <div className="space-y-4">
                    {emp.shifts.map((shift, shiftIndex) => (
                      <div key={shiftIndex} className="space-y-2">
                        <Label className="text-sm font-semibold flex items-center gap-2">
                          <Icon name="Clock" size={16} />
                          Смена {shiftIndex + 1}
                        </Label>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <Label className="text-xs text-muted-foreground">С</Label>
                            <Input
                              type="time"
                              value={shift.startTime}
                              onChange={(e) => updateEmployee(empIndex, `shifts.${shiftIndex}.startTime`, e.target.value)}
                              className="bg-background/50 border-border"
                            />
                          </div>
                          <div>
                            <Label className="text-xs text-muted-foreground">До</Label>
                            <Input
                              type="time"
                              value={shift.endTime}
                              onChange={(e) => updateEmployee(empIndex, `shifts.${shiftIndex}.endTime`, e.target.value)}
                              className="bg-background/50 border-border"
                            />
                          </div>
                        </div>
                      </div>
                    ))}

                    <div className="space-y-2">
                      <Label className="text-sm font-semibold flex items-center gap-2">
                        <Icon name="Package" size={16} />
                        Количество заказов
                      </Label>
                      <Input
                        type="number"
                        min="0"
                        value={emp.orders}
                        onChange={(e) => updateEmployee(empIndex, 'orders', Number(e.target.value))}
                        className="bg-background/50 border-border"
                        placeholder="0"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label className="text-sm font-semibold flex items-center gap-2">
                        <Icon name="Plus" size={16} />
                        Доплата за заказ (₽)
                      </Label>
                      <Input
                        type="number"
                        min="0"
                        value={emp.bonus}
                        onChange={(e) => updateEmployee(empIndex, 'bonus', Number(e.target.value))}
                        className="bg-background/50 border-border"
                        placeholder="0"
                      />
                    </div>
                  </div>

                  <div className={`p-4 rounded-lg bg-gradient-to-br ${emp.color} bg-opacity-20 backdrop-blur-sm border border-white/10`}>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground flex items-center gap-1">
                          <Icon name="Clock" size={14} />
                          Часы:
                        </span>
                        <span className="font-semibold">{totalHours.toFixed(1)} ч × 250₽</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground flex items-center gap-1">
                          <Icon name="Package" size={14} />
                          Заказы:
                        </span>
                        <span className="font-semibold">{emp.orders} × {50 + emp.bonus}₽</span>
                      </div>
                      <div className="h-px bg-gradient-to-r from-transparent via-white/20 to-transparent my-2" />
                      <div className="flex justify-between items-center">
                        <span className="font-heading font-bold text-lg">Итого:</span>
                        <span className="font-heading font-bold text-3xl bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                          {salary.toFixed(0)}₽
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>

        <Card className="p-8 bg-gradient-to-br from-card to-muted/50 backdrop-blur-sm animate-fade-in border-primary/20">
          <h3 className="text-3xl font-heading font-bold mb-6 flex items-center gap-3">
            <Icon name="TrendingUp" size={32} className="text-primary" />
            Общая статистика за месяц
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {employees.map((emp, index) => (
              <div
                key={index}
                className="p-6 rounded-lg bg-gradient-to-br from-background to-muted/30 border border-border hover:scale-105 transition-transform duration-300"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${emp.color} flex items-center justify-center text-lg font-bold text-white`}>
                    {emp.name[0]}
                  </div>
                  <span className="font-semibold">{emp.name}</span>
                </div>
                <div className="text-3xl font-heading font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                  {(calculateSalary(emp) * 30).toLocaleString()}₽
                </div>
                <div className="text-sm text-muted-foreground mt-1">за 30 дней</div>
              </div>
            ))}
            <div className="p-6 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 border-2 border-primary hover:scale-105 transition-transform duration-300">
              <div className="flex items-center gap-2 mb-3">
                <Icon name="Wallet" size={24} className="text-primary" />
                <span className="font-semibold">Всего</span>
              </div>
              <div className="text-3xl font-heading font-bold bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
                {(employees.reduce((sum, emp) => sum + calculateSalary(emp), 0) * 30).toLocaleString()}₽
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
