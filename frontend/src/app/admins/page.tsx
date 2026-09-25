'use client';

import { AdminLayout } from '@/components/layout/AdminLayout';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAdmins, createAdmin, deleteAdmin } from '@/services/api';
import { useState } from 'react';
import { Shield, Plus, Trash2, KeyRound } from 'lucide-react';
import { format } from 'date-fns';

export default function AdminsPage() {
  const queryClient = useQueryClient();
  const { data: admins, isLoading } = useQuery({ queryKey: ['admins'], queryFn: getAdmins });
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ username: '', password: '', role: 'admin' });
  const [err, setErr] = useState('');

  const createMut = useMutation({
    mutationFn: createAdmin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admins'] });
      setShowForm(false);
      setForm({ username: '', password: '', role: 'admin' });
      setErr('');
    },
    onError: (e: any) => setErr(e.response?.data?.detail || "Admin yaratishda xatolik yuz berdi"),
  });

  const deleteMut = useMutation({
    mutationFn: deleteAdmin,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admins'] }),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.username || !form.password) {
      setErr("Username va parolni kiriting");
      return;
    }
    createMut.mutate(form);
  };

  return (
    <AdminLayout>
      <div className="max-w-3xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Shield className="w-6 h-6 text-indigo-500" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Adminlar Boshqaruvi</h1>
              <p className="text-gray-500 text-sm">Dashboardga kirish huquqiga ega adminlar ro'yxati</p>
            </div>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="btn-primary flex items-center justify-center gap-2 text-sm"
          >
            <Plus className="w-4 h-4" /> Yangi admin qo'shish
          </button>
        </div>

        {showForm && (
          <form onSubmit={handleSubmit} className="card space-y-4">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <KeyRound className="w-4 h-4 text-indigo-500" /> Yangi administrator
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Username</label>
                <input
                  placeholder="admin_login"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  className="input text-xs"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Parol</label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className="input text-xs"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Rol</label>
                <select
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                  className="input text-xs font-medium"
                >
                  <option value="admin">Administrator</option>
                  <option value="moderator">Moderator</option>
                  <option value="superadmin">Superadmin</option>
                </select>
              </div>
            </div>

            {err && <p className="text-red-500 text-xs font-semibold">{err}</p>}

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="btn-secondary text-xs py-1.5"
              >
                Bekor qilish
              </button>
              <button
                type="submit"
                disabled={createMut.isPending}
                className="btn-primary text-xs py-1.5"
              >
                {createMut.isPending ? 'Saqlanmoqda...' : 'Saqlash'}
              </button>
            </div>
          </form>
        )}

        <div className="card space-y-4">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-100 dark:border-gray-800">
                  <th className="pb-3 font-semibold">Username</th>
                  <th className="pb-3 font-semibold">Rol</th>
                  <th className="pb-3 font-semibold">Holat</th>
                  <th className="pb-3 font-semibold">Oxirgi kirish</th>
                  <th className="pb-3 font-semibold text-right">Amal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {isLoading ? (
                  [...Array(3)].map((_, i) => (
                    <tr key={i}>
                      <td colSpan={5} className="py-4">
                        <div className="h-6 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
                      </td>
                    </tr>
                  ))
                ) : admins && admins.length > 0 ? (
                  admins.map((a: any) => (
                    <tr key={a.id} className="table-row">
                      <td className="py-3.5 font-semibold text-gray-900 dark:text-white">
                        {a.username}
                      </td>
                      <td className="py-3.5">
                        <span className="text-xs bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-semibold px-2 py-0.5 rounded-full capitalize">
                          {a.role}
                        </span>
                      </td>
                      <td className="py-3.5">
                        <span className={a.is_active ? 'badge-published' : 'badge-hidden'}>
                          {a.is_active ? 'Faol' : 'Nofaol'}
                        </span>
                      </td>
                      <td className="py-3.5 text-gray-400 text-xs">
                        {a.last_login ? format(new Date(a.last_login), 'dd.MM.yyyy HH:mm') : 'Hali kirmagan'}
                      </td>
                      <td className="py-3.5 text-right">
                        <button
                          onClick={() => {
                            if (confirm(`"${a.username}" adminini o'chirishni xohlaysizmi?`)) {
                              deleteMut.mutate(a.id);
                            }
                          }}
                          className="p-1.5 text-red-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                          title="O'chirish"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-gray-400">
                      Adminlar yo'q
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
