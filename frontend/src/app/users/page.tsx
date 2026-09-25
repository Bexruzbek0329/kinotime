'use client';

import { AdminLayout } from '@/components/layout/AdminLayout';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getUsers, blockUser, unblockUser } from '@/services/api';
import { useState } from 'react';
import { Ban, CheckCircle, Users } from 'lucide-react';
import { format } from 'date-fns';

export default function UsersPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({
    queryKey: ['users', page],
    queryFn: () => getUsers({ page, per_page: 20 }),
  });

  const blockMut = useMutation({
    mutationFn: blockUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });
  const unblockMut = useMutation({
    mutationFn: unblockUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Users className="w-6 h-6 text-indigo-500" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Foydalanuvchilar</h1>
            <p className="text-gray-500 text-sm">Jami foydalanuvchilar: {data?.total ?? 0} ta</p>
          </div>
        </div>

        <div className="card space-y-4">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-100 dark:border-gray-800">
                  <th className="pb-3 font-semibold">Telegram ID</th>
                  <th className="pb-3 font-semibold">Ism</th>
                  <th className="pb-3 font-semibold">Username</th>
                  <th className="pb-3 font-semibold">Qo'shilgan sana</th>
                  <th className="pb-3 font-semibold">Oxirgi faollik</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold text-right">Amal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {isLoading ? (
                  [...Array(6)].map((_, i) => (
                    <tr key={i}>
                      <td colSpan={7} className="py-4">
                        <div className="h-6 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
                      </td>
                    </tr>
                  ))
                ) : data?.items?.length ? (
                  data.items.map((u: any) => (
                    <tr key={u.id} className="table-row">
                      <td className="py-3.5">
                        <code className="text-xs font-mono bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded text-indigo-500 font-semibold">
                          {u.telegram_id}
                        </code>
                      </td>
                      <td className="py-3.5 font-semibold text-gray-900 dark:text-white">
                        {u.first_name} {u.last_name || ''}
                      </td>
                      <td className="py-3.5 text-gray-500">
                        {u.username ? (
                          <a
                            href={`https://t.me/${u.username}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-indigo-400 hover:underline"
                          >
                            @{u.username}
                          </a>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="py-3.5 text-gray-400 text-xs">
                        {u.joined_at ? format(new Date(u.joined_at), 'dd.MM.yyyy HH:mm') : '—'}
                      </td>
                      <td className="py-3.5 text-gray-400 text-xs">
                        {u.last_activity ? format(new Date(u.last_activity), 'dd.MM.yyyy HH:mm') : '—'}
                      </td>
                      <td className="py-3.5">
                        <span className={u.is_blocked ? 'badge-hidden' : 'badge-published'}>
                          {u.is_blocked ? '🚫 Bloklangan' : '✅ Faol'}
                        </span>
                      </td>
                      <td className="py-3.5 text-right">
                        {u.is_blocked ? (
                          <button
                            onClick={() => unblockMut.mutate(u.telegram_id)}
                            className="inline-flex items-center gap-1.5 text-xs text-green-500 hover:bg-green-50 dark:hover:bg-green-900/20 px-2.5 py-1 rounded-lg border border-green-500/30 transition-colors"
                          >
                            <CheckCircle className="w-3.5 h-3.5" /> Blokdan chiqarish
                          </button>
                        ) : (
                          <button
                            onClick={() => {
                              if (confirm(`Foydalanuvchi (${u.first_name}) bloklansinmi?`)) {
                                blockMut.mutate(u.telegram_id);
                              }
                            }}
                            className="inline-flex items-center gap-1.5 text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 px-2.5 py-1 rounded-lg border border-red-500/30 transition-colors"
                          >
                            <Ban className="w-3.5 h-3.5" /> Bloklash
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="py-10 text-center text-gray-400">
                      Foydalanuvchilar topilmadi
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-800">
              <span className="text-sm text-gray-500">
                Sahifa {page} / {data.total_pages} (Jami: {data.total})
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary px-3 py-1 text-sm disabled:opacity-40"
                >
                  ← Oldingi
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                  disabled={page === data.total_pages}
                  className="btn-secondary px-3 py-1 text-sm disabled:opacity-40"
                >
                  Keyingi →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}
