import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import Icon from '@/components/ui/icon';
import { Badge } from '@/components/ui/badge';

interface Employee {
  id: number;
  full_name: string;
  telegram_id: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const API_URL = 'https://functions.poehali.dev/0247f5a1-41c0-407e-9948-e4860da84bbe';

export default function Employees() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [formData, setFormData] = useState({ full_name: '', password: '' });
  const [editFormData, setEditFormData] = useState({ full_name: '', password: '' });
  const [deletePassword, setDeletePassword] = useState('');
  const { toast } = useToast();

  const loadEmployees = async () => {
    try {
      setLoading(true);
      const response = await fetch(API_URL);
      const data = await response.json();
      setEmployees(data.employees || []);
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось загрузить список сотрудников',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEmployees();
  }, []);

  const handleAddEmployee = async () => {
    if (!formData.full_name.trim()) {
      toast({
        title: 'Ошибка',
        description: 'Введите ФИО сотрудника',
        variant: 'destructive',
      });
      return;
    }

    if (!formData.password) {
      toast({
        title: 'Ошибка',
        description: 'Введите пароль администратора',
        variant: 'destructive',
      });
      return;
    }

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: formData.full_name,
          password: formData.password,
        }),
      });

      const data = await response.json();

      if (response.status === 403) {
        toast({
          title: 'Доступ запрещён',
          description: 'Неверный пароль администратора',
          variant: 'destructive',
        });
        return;
      }

      if (response.status === 400) {
        toast({
          title: 'Ошибка',
          description: data.error || 'Ошибка валидации',
          variant: 'destructive',
        });
        return;
      }

      if (response.status === 201) {
        toast({
          title: 'Успешно',
          description: `Сотрудник ${data.employee.full_name} добавлен`,
        });
        setDialogOpen(false);
        setFormData({ full_name: '', password: '' });
        loadEmployees();
        return;
      }

      toast({
        title: 'Ошибка',
        description: 'Не удалось добавить сотрудника',
        variant: 'destructive',
      });
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось добавить сотрудника',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteEmployee = async () => {
    if (!selectedEmployee) return;

    if (!deletePassword) {
      toast({
        title: 'Ошибка',
        description: 'Введите пароль администратора',
        variant: 'destructive',
      });
      return;
    }

    try {
      const response = await fetch(API_URL, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: selectedEmployee.id,
          password: deletePassword,
        }),
      });

      const data = await response.json();

      if (response.status === 403) {
        toast({
          title: 'Доступ запрещён',
          description: 'Неверный пароль администратора',
          variant: 'destructive',
        });
        return;
      }

      if (response.status === 200) {
        toast({
          title: 'Успешно',
          description: `Сотрудник ${selectedEmployee.full_name} удалён`,
        });
        setDeleteDialogOpen(false);
        setSelectedEmployee(null);
        setDeletePassword('');
        loadEmployees();
        return;
      }

      toast({
        title: 'Ошибка',
        description: data.error || 'Не удалось удалить сотрудника',
        variant: 'destructive',
      });
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось удалить сотрудника',
        variant: 'destructive',
      });
    }
  };

  const handleEditEmployee = async () => {
    if (!selectedEmployee) return;

    if (!editFormData.full_name.trim()) {
      toast({
        title: 'Ошибка',
        description: 'Введите новое ФИО',
        variant: 'destructive',
      });
      return;
    }

    if (!editFormData.password) {
      toast({
        title: 'Ошибка',
        description: 'Введите пароль администратора',
        variant: 'destructive',
      });
      return;
    }

    try {
      const response = await fetch(API_URL, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: selectedEmployee.id,
          full_name: editFormData.full_name,
          password: editFormData.password,
        }),
      });

      const data = await response.json();

      if (response.status === 403) {
        toast({
          title: 'Доступ запрещён',
          description: 'Неверный пароль администратора',
          variant: 'destructive',
        });
        return;
      }

      if (response.status === 400) {
        toast({
          title: 'Ошибка',
          description: data.error || 'Ошибка валидации',
          variant: 'destructive',
        });
        return;
      }

      if (response.status === 200) {
        toast({
          title: 'Успешно',
          description: `ФИО изменено на ${editFormData.full_name}`,
        });
        setEditDialogOpen(false);
        setSelectedEmployee(null);
        setEditFormData({ full_name: '', password: '' });
        loadEmployees();
        return;
      }

      toast({
        title: 'Ошибка',
        description: data.error || 'Не удалось изменить ФИО',
        variant: 'destructive',
      });
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось изменить ФИО',
        variant: 'destructive',
      });
    }
  };

  const activeEmployees = employees.filter(e => e.is_active);
  const inactiveEmployees = employees.filter(e => !e.is_active);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Управление сотрудниками</h1>
            <p className="text-gray-600">Добавляйте, редактируйте и удаляйте до 15 сотрудников</p>
          </div>
          <Button onClick={() => setDialogOpen(true)} size="lg" disabled={activeEmployees.length >= 15}>
            <Icon name="UserPlus" className="mr-2" size={20} />
            Добавить сотрудника
          </Button>
        </div>

        <Card className="shadow-lg mb-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Активные сотрудники</span>
              <Badge variant={activeEmployees.length >= 15 ? 'destructive' : 'default'}>
                {activeEmployees.length}/15
              </Badge>
            </CardTitle>
            <CardDescription>
              {activeEmployees.length === 0 && 'Нет активных сотрудников'}
              {activeEmployees.length >= 15 && 'Достигнут лимит — максимум 15 сотрудников'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Icon name="Loader2" className="animate-spin" size={32} />
              </div>
            ) : activeEmployees.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Icon name="Users" size={48} className="mx-auto mb-4 opacity-50" />
                <p>Добавьте первого сотрудника</p>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {activeEmployees.map((employee) => (
                  <Card key={employee.id} className="border-2 hover:border-blue-500 transition-colors">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg">
                            {employee.full_name.charAt(0)}
                          </div>
                          <div>
                            <h3 className="font-semibold text-gray-900">{employee.full_name}</h3>
                            {employee.telegram_id && (
                              <p className="text-sm text-gray-500 flex items-center gap-1">
                                <Icon name="MessageCircle" size={14} />
                                TG: {employee.telegram_id}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2 mt-3">
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1"
                          onClick={() => {
                            setSelectedEmployee(employee);
                            setEditFormData({ full_name: employee.full_name, password: '' });
                            setEditDialogOpen(true);
                          }}
                        >
                          <Icon name="Edit" className="mr-2" size={16} />
                          Изменить
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          className="flex-1"
                          onClick={() => {
                            setSelectedEmployee(employee);
                            setDeleteDialogOpen(true);
                          }}
                        >
                          <Icon name="Trash2" className="mr-2" size={16} />
                          Удалить
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {inactiveEmployees.length > 0 && (
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Удалённые сотрудники</CardTitle>
              <CardDescription>Архив ({inactiveEmployees.length})</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {inactiveEmployees.slice(0, 10).map((employee) => (
                  <div key={employee.id} className="flex items-center gap-3 py-2 px-3 bg-gray-100 rounded-lg">
                    <Icon name="UserX" size={18} className="text-gray-400" />
                    <span className="text-gray-600">{employee.full_name}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Добавить нового сотрудника</DialogTitle>
              <DialogDescription>
                Введите ФИО и пароль администратора для добавления
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="full_name">ФИО сотрудника</Label>
                <Input
                  id="full_name"
                  placeholder="Иванов Иван Иванович"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="password">Пароль администратора</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Введите пароль"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                />
                <p className="text-sm text-gray-500 mt-1">Дефолтный пароль: admin123</p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Отмена
              </Button>
              <Button onClick={handleAddEmployee}>Добавить</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Изменить ФИО сотрудника</DialogTitle>
              <DialogDescription>
                Редактирование: {selectedEmployee?.full_name}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit_full_name">Новое ФИО</Label>
                <Input
                  id="edit_full_name"
                  placeholder="Иванов Иван Иванович"
                  value={editFormData.full_name}
                  onChange={(e) => setEditFormData({ ...editFormData, full_name: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit_password">Пароль администратора</Label>
                <Input
                  id="edit_password"
                  type="password"
                  placeholder="Введите пароль"
                  value={editFormData.password}
                  onChange={(e) => setEditFormData({ ...editFormData, password: e.target.value })}
                />
                <p className="text-sm text-gray-500 mt-1">Дефолтный пароль: admin123</p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
                Отмена
              </Button>
              <Button onClick={handleEditEmployee}>Сохранить</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Удалить сотрудника</DialogTitle>
              <DialogDescription>
                Вы уверены что хотите удалить {selectedEmployee?.full_name}?
              </DialogDescription>
            </DialogHeader>
            <div>
              <Label htmlFor="delete_password">Пароль администратора</Label>
              <Input
                id="delete_password"
                type="password"
                placeholder="Введите пароль для подтверждения"
                value={deletePassword}
                onChange={(e) => setDeletePassword(e.target.value)}
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                Отмена
              </Button>
              <Button variant="destructive" onClick={handleDeleteEmployee}>
                Удалить
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}