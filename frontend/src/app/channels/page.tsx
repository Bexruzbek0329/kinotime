'use client';

import { AdminLayout } from '@/components/layout/AdminLayout';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getChannels, createChannel, updateChannel, deleteChannel } from '@/services/api';
import { useState } from 'react';
import { Plus, Radio, Trash2, ToggleLeft, ToggleRight, ExternalLink, ShieldAlert } from 'lucide-react';

export default function ChannelsPage() {
  const queryClient = useQueryClient();
  const { data: channels, isLoading } = useQuery({ queryKey: ['channels'], queryFn: getChannels });
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ channel_id: '', username: '', title: '' });
  const [error, setError] = useState('');

  const createMut = useMutation({
    mutationFn: createChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      setShowForm(false);
      setForm({ channel_id: '', username: '', title: '' });
      setError('');
    },
    onError: (e: any) => setError(e.response?.data?.detail || "Kanal qo'shishda xatolik"),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateChannel(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['channels'] }),
  });

  const deleteMut = useMutation({
    mutationFn: deleteChannel,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['channels'] }),
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.channel_id || !form.username || !form.title) {
      setError("Barcha maydonlarni to'ldiring");
      return;
    }
    createMut.mutate({
      channel_id: parseInt(form.channel_id),
      username: form.username.replace('@', ''),
      title: form.title.trim(),
    });
  };

  return (
    <AdminLayout>
      <div className="max-w-3xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Radio className="w-6 h-6 text-indigo-500" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Majburiy obuna kanallari</h1>
              <p className="text-gray-500 text-sm">Botdan foydalanishdan oldin obuna tekshiriladigan kanallar</p>
            </div>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="btn-primary flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" /> Yangi kanal qo'shish
          </button>
        </div>

        <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-500 flex items-start gap-2.5">
          <ShieldAlert className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>
            <b>MUHIM:</b> Bot ushbu kanalda <b>Admin</b> bo'lishi va "Foydalanuvchilarni ko'rish" (Invite users / member check) huquqiga ega bo'lishi lozim!
          </span>
        </div>

        {showForm && (
          <form onSubmit={handleCreate} className="card space-y-4">
            <h3 className="font-semibold text-gray-900 dark:text-white">Yangi majburiy kanal</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Kanal ID (masalan: -100...)</label>
                <input
                  placeholder="-1001234567890"
                  value={form.channel_id}
                  onChange={(e) => setForm({ ...form, channel_id: e.target.value })}
                  className="input font-mono text-xs"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Username (belgisiz)</label>
                <input
                  placeholder="mening_kanalim"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  className="input text-xs"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Kanal ko'rinadigan nomi</label>
                <input
                  placeholder="Kino Premyeralar"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="input text-xs"
                  required
                />
              </div>
            </div>

            {error && <p className="text-red-500 text-xs font-semibold">{error}</p>}

            <div className="flex gap-2 justify-end">
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
                {createMut.isPending ? 'Qo\'shilmoqda...' : 'Kanalni qo\'shish'}
              </button>
            </div>
          </form>
        )}

        <div className="space-y-3">
          {isLoading ? (
            <div className="card animate-pulse h-24" />
          ) : channels && channels.length > 0 ? (
            channels.map((ch: any) => (
              <div
                key={ch.id}
                className="card flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-500 font-bold">
                    📢
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-gray-900 dark:text-white">{ch.title}</p>
                      <a
                        href={`https://t.me/${ch.username}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-gray-400 hover:text-indigo-400"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">
                      @{ch.username} · ID: <code className="font-mono">{ch.channel_id}</code>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span
                    className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                      ch.is_active ? 'badge-published' : 'badge-hidden'
                    }`}
                  >
                    {ch.is_active ? 'Faol tekshiruvda' : 'O\'chirilgan'}
                  </span>

                  <button
                    onClick={() => updateMut.mutate({ id: ch.id, data: { is_active: !ch.is_active } })}
                    className="p-1 text-gray-400 hover:text-indigo-500 rounded"
                    title={ch.is_active ? "O'chirish" : "Yoqish"}
                  >
                    {ch.is_active ? (
                      <ToggleRight className="w-7 h-7 text-green-500" />
                    ) : (
                      <ToggleLeft className="w-7 h-7 text-gray-400" />
                    )}
                  </button>

                  <button
                    onClick={() => {
                      if (confirm(`"${ch.title}" kanalini o'chirib tashlaysizmi?`)) {
                        deleteMut.mutate(ch.id);
                      }
                    }}
                    className="p-2 text-red-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="card text-center py-10 text-gray-400">
              Hozircha majburiy kanallar qo'shilmagan. Bot barcha foydalanuvchilar uchun ochiq ishlaydi.
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}
