'use client';

import { AdminLayout } from '@/components/layout/AdminLayout';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAdmins, createAdmin, updateAdmin, deleteAdmin } from '@/services/api';
import { useState } from 'react';
import { Shield, Plus, Trash2, KeyRound, X, Check } from 'lucide-react';
import { format } from 'date-fns';

export default function AdminsPage() {
  const queryClient = useQueryClient();
  const { data: admins, isLoading } = useQuery({ queryKey: ['admins'], queryFn: getAdmins });
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ username: '', password: '', role: 'admin', telegram_id: '' });
  const [err, setErr] = useState('');

  // Password / Data Edit Modal State
  const [editAdmin, setEditAdmin] = useState<any | null>(null);
  const [editPassword, setEditPassword] = useState('');
  const [editTelegramId, setEditTelegramId] = useState('');
  const [editRole, setEditRole] = useState('admin');
  const [editErr, setEditErr] = useState('');
  const [editSuccess, setEditSuccess] = useState('');

  const createMut = useMutation({
    mutationFn: (data: any) =>
      createAdmin({
        ...data,
        telegram_id: data.telegram_id ? Number(data.telegram_id) : null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admins'] });
      setShowForm(false);
      setForm({ username: '', password: '', role: 'admin', telegram_id: '' });
      setErr('');
    },
    onError: (e: any) => setErr(e.response?.data?.detail || "Admin yaratishda xatolik yuz berdi"),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateAdmin(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admins'] });
      setEditSuccess('Admin ma\'lumotlari muvaffaqiyatli saqlandi!');
      setTimeout(() => {
        setEditAdmin(null);
        setEditSuccess('');
      }, 1500);
    },
    onError: (e: any) => setEditErr(e.response?.data?.detail || "Tahrirlashda xatolik yuz berdi"),
  });

  const deleteMut = useMutation({
    mutationFn: deleteAdmin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admins'] });
    },
    onError: (e: any) => {
      alert(e.response?.data?.detail || "Adminni o'chirishda xatolik yuz berdi");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.username || !form.password) {
      setErr("Username va parolni kiriting");
      return;
    }
    createMut.mutate(form);
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editAdmin) return;
    const payload: any = {
      role: editRole,
      telegram_id: editTelegramId ? Number(editTelegramId) : null,
    };
    if (editPassword.trim()) {
      payload.password = editPassword.trim();
    }
    updateMut.mutate({ id: editAdmin.id, data: payload });
  };

  return (
    <AdminLayout>
      <div className="max-w-4xl space-y-6">
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

        {/* Create Form */}
        {showForm && (
          <form onSubmit={handleSubmit} className="card space-y-4">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <KeyRound className="w-4 h-4 text-indigo-500" /> Yangi administrator
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Username *</label>
                <input
                  placeholder="admin_login"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  className="input text-xs"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Parol *</label>
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
                <label className="block text-xs font-semibold text-gray-500 mb-1">Telegram ID</label>
                <input
                  type="number"
                  placeholder="8327580188"
                  value={form.telegram_id}
                  onChange={(e) => setForm({ ...form, telegram_id: e.target.value })}
                  className="input text-xs"
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

        {/* Admins Table */}
        <div className="card space-y-4">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-100 dark:border-gray-800">
                  <th className="pb-3 font-semibold">Username</th>
                  <th className="pb-3 font-semibold">Rol</th>
                  <th className="pb-3 font-semibold">Telegram ID</th>
                  <th className="pb-3 font-semibold">Holat</th>
                  <th className="pb-3 font-semibold">Oxirgi kirish</th>
                  <th className="pb-3 font-semibold text-right">Amal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {isLoading ? (
                  [...Array(3)].map((_, i) => (
                    <tr key={i}>
                      <td colSpan={6} className="py-4">
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
                      <td className="py-3.5 text-xs font-mono">
                        {a.telegram_id ? (
                          <span className="text-indigo-600 dark:text-indigo-400 font-medium">
                            {a.telegram_id}
                          </span>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td className="py-3.5">
                        <span className={a.is_active ? 'badge-published' : 'badge-hidden'}>
                          {a.is_active ? 'Faol' : 'Nofaol'}
                        </span>
                      </td>
                      <td className="py-3.5 text-gray-400 text-xs">
                        {a.last_login ? format(new Date(a.last_login), 'dd.MM.yyyy HH:mm') : 'Hali kirmagan'}
                      </td>
                      <td className="py-3.5 text-right space-x-1">
                        {/* Edit password / details button */}
                        <button
                          onClick={() => {
                            setEditAdmin(a);
                            setEditPassword('');
                            setEditTelegramId(a.telegram_id ? String(a.telegram_id) : '');
                            setEditRole(a.role);
                            setEditErr('');
                            setEditSuccess('');
                          }}
                          className="p-1.5 text-indigo-500 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-colors inline-block"
                          title="Parol va ma'lumotlarni tahrirlash"
                        >
                          <KeyRound className="w-4 h-4" />
                        </button>

                        {/* Delete button */}
                        <button
                          onClick={() => {
                            if (confirm(`"${a.username}" adminini ro'yxatdan o'chirishni tasdiqlaysizmi?`)) {
                              deleteMut.mutate(a.id);
                            }
                          }}
                          disabled={deleteMut.isPending}
                          className="p-1.5 text-red-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors inline-block"
                          title="O'chirish"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-gray-400">
                      Adminlar yo'q
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Edit Password & Details Modal */}
        {editAdmin && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-100 dark:border-gray-800 w-full max-w-md p-6 space-y-5 animate-in fade-in zoom-in duration-150">
              <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-3">
                <div className="flex items-center gap-2">
                  <KeyRound className="w-5 h-5 text-indigo-500" />
                  <h3 className="font-bold text-gray-900 dark:text-white">
                    "{editAdmin.username}" adminini tahrirlash
                  </h3>
                </div>
                <button
                  onClick={() => setEditAdmin(null)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleEditSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 mb-1">
                    Yangi Parol (agar o'zgartirmoqchi bo'lsangiz)
                  </label>
                  <input
                    type="password"
                    placeholder="Yangi parol kiriting (bo'sh qolsa o'zgarmaydi)"
                    value={editPassword}
                    onChange={(e) => setEditPassword(e.target.value)}
                    className="input text-xs w-full"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-500 mb-1">
                    Telegram ID (Botda adminlik huquqini berish uchun)
                  </label>
                  <input
                    type="number"
                    placeholder="Masalan: 8327580188"
                    value={editTelegramId}
                    onChange={(e) => setEditTelegramId(e.target.value)}
                    className="input text-xs w-full"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-500 mb-1">Rol</label>
                  <select
                    value={editRole}
                    onChange={(e) => setEditRole(e.target.value)}
                    className="input text-xs font-medium w-full"
                  >
                    <option value="admin">Administrator</option>
                    <option value="moderator">Moderator</option>
                    <option value="superadmin">Superadmin</option>
                  </select>
                </div>

                {editErr && (
                  <p className="text-red-500 text-xs font-semibold bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
                    {editErr}
                  </p>
                )}

                {editSuccess && (
                  <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-xs font-semibold bg-emerald-50 dark:bg-emerald-900/20 p-2 rounded-lg">
                    <Check className="w-4 h-4" />
                    <span>{editSuccess}</span>
                  </div>
                )}

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setEditAdmin(null)}
                    className="btn-secondary text-xs py-2 px-4"
                  >
                    Bekor qilish
                  </button>
                  <button
                    type="submit"
                    disabled={updateMut.isPending}
                    className="btn-primary text-xs py-2 px-4"
                  >
                    {updateMut.isPending ? 'Saqlanmoqda...' : 'Saqlash'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
