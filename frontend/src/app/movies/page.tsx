'use client';

import { AdminLayout } from '@/components/layout/AdminLayout';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getMovies, deleteMovie, updateMovie } from '@/services/api';
import { useState } from 'react';
import { Plus, Search, Edit, Trash2, Eye, EyeOff } from 'lucide-react';
import Link from 'next/link';
import type { Movie } from '@/types';

export default function MoviesPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['movies', page, search, statusFilter, typeFilter],
    queryFn: () =>
      getMovies({
        page,
        per_page: 20,
        search: search || undefined,
        status: statusFilter || undefined,
        content_type: typeFilter || undefined,
      }),
  });

  const deleteMut = useMutation({
    mutationFn: deleteMovie,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['movies'] }),
  });

  const toggleStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => updateMovie(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['movies'] }),
  });

  const statusBadge = (status: string) => {
    const cls = status === 'published' ? 'badge-published' : status === 'draft' ? 'badge-draft' : 'badge-hidden';
    const labels: Record<string, string> = { published: 'Nashr qilingan', draft: 'Qoralama', hidden: 'Yashiringan' };
    return <span className={cls}>{labels[status] ?? status}</span>;
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Kinolar va seriallar</h1>
            <p className="text-gray-500 text-sm mt-0.5">Jami: {data?.total ?? 0} ta</p>
          </div>
          <Link href="/movies/new" className="btn-primary flex items-center justify-center gap-2">
            <Plus className="w-4 h-4" /> Yangi qo'shish
          </Link>
        </div>

        <div className="card space-y-4">
          <div className="flex items-center gap-2 border-b border-gray-100 dark:border-gray-800 pb-3">
            <button
              onClick={() => { setTypeFilter(''); setPage(1); }}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                typeFilter === ''
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
              }`}
            >
              Barchasi ({data?.total ?? 0})
            </button>
            <button
              onClick={() => { setTypeFilter('movie'); setPage(1); }}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                typeFilter === 'movie'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
              }`}
            >
              🎬 Kinolar
            </button>
            <button
              onClick={() => { setTypeFilter('serial'); setPage(1); }}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                typeFilter === 'serial'
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
              }`}
            >
              📺 Seriallar
            </button>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
              <input
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    setSearch(searchInput);
                    setPage(1);
                  }
                }}
                className="input pl-9"
                placeholder="Kino/serial nomi yoki kodi bo'yicha qidirish (Enter bosing)..."
              />
            </div>
            <select
              value={typeFilter}
              onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
              className="input sm:w-40"
            >
              <option value="">Barcha turlar</option>
              <option value="movie">🎬 Kinolar</option>
              <option value="serial">📺 Seriallar</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="input sm:w-40"
            >
              <option value="">Barcha statuslar</option>
              <option value="published">Nashr qilingan</option>
              <option value="draft">Qoralama</option>
              <option value="hidden">Yashiringan</option>
            </select>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-100 dark:border-gray-800">
                  <th className="pb-3 font-semibold">Turi</th>
                  <th className="pb-3 font-semibold">Nomi</th>
                  <th className="pb-3 font-semibold">Kodi</th>
                  <th className="pb-3 font-semibold">Yili / Qismlar</th>
                  <th className="pb-3 font-semibold">IMDb</th>
                  <th className="pb-3 font-semibold">Ko'rishlar</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Videolar</th>
                  <th className="pb-3 font-semibold text-right">Amallar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {isLoading ? (
                  [...Array(6)].map((_, i) => (
                    <tr key={i}>
                      <td colSpan={9} className="py-4">
                        <div className="h-6 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
                      </td>
                    </tr>
                  ))
                ) : data?.items?.length ? (
                  data.items.map((movie: Movie) => (
                    <tr key={movie.id} className="table-row">
                      <td className="py-3.5 pr-2">
                        {movie.content_type === 'serial' ? (
                          <span className="text-xs bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 font-medium px-2 py-0.5 rounded-full inline-flex items-center gap-1">
                            📺 Serial
                          </span>
                        ) : (
                          <span className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-medium px-2 py-0.5 rounded-full inline-flex items-center gap-1">
                            🎬 Kino
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 pr-3">
                        <div className="font-semibold text-gray-900 dark:text-white">{movie.title}</div>
                        {movie.original_title && (
                          <div className="text-xs text-gray-400 font-normal">{movie.original_title}</div>
                        )}
                      </td>
                      <td className="py-3.5">
                        <code className="bg-gray-100 dark:bg-gray-800 text-indigo-500 font-mono px-2 py-0.5 rounded text-xs">
                          #{movie.code}
                        </code>
                      </td>
                      <td className="py-3.5 text-gray-600 dark:text-gray-400">
                        {movie.content_type === 'serial' && (movie.total_seasons || movie.total_episodes) ? (
                          <span className="text-xs">
                            {movie.total_seasons ? `${movie.total_seasons} m.` : ''}
                            {movie.total_seasons && movie.total_episodes ? ' • ' : ''}
                            {movie.total_episodes ? `${movie.total_episodes} q.` : ''}
                            {movie.year ? ` (${movie.year})` : ''}
                          </span>
                        ) : (
                          movie.year ?? '—'
                        )}
                      </td>
                      <td className="py-3.5 font-medium text-amber-500">
                        {movie.imdb_rating ? `⭐ ${movie.imdb_rating}` : '—'}
                      </td>
                      <td className="py-3.5 text-gray-600 dark:text-gray-400 font-mono">
                        {movie.views_count.toLocaleString()}
                      </td>
                      <td className="py-3.5">{statusBadge(movie.status)}</td>
                      <td className="py-3.5">
                        {movie.content_type === 'serial' ? (
                          <Link
                            href={`/movies/${movie.id}`}
                            className="text-xs bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 font-medium px-2.5 py-1 rounded-full hover:bg-purple-100 dark:hover:bg-purple-900/50 transition-colors inline-flex items-center gap-1"
                          >
                            📺 {movie.episodes?.length ?? 0} ta qism
                          </Link>
                        ) : (
                          <span className="text-xs bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-medium px-2 py-0.5 rounded-full">
                            {movie.videos?.length ?? 0} ta sifat
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Link
                            href={`/movies/${movie.id}`}
                            className="p-1.5 text-gray-400 hover:text-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-colors"
                            title="Tahrirlash"
                          >
                            <Edit className="w-4 h-4" />
                          </Link>
                          <button
                            onClick={() =>
                              toggleStatus.mutate({
                                id: movie.id,
                                status: movie.status === 'published' ? 'hidden' : 'published',
                              })
                            }
                            className="p-1.5 text-gray-400 hover:text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded transition-colors"
                            title={movie.status === 'published' ? "Yashirish" : "Nashr qilish"}
                          >
                            {movie.status === 'published' ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                          <button
                            onClick={() => {
                              if (confirm(`"${movie.title}" kinosini o'chirib tashlamoqchimisiz?`)) {
                                deleteMut.mutate(movie.id);
                              }
                            }}
                            className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                            title="O'chirish"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={9} className="py-10 text-center text-gray-400">
                      Kinolar yoki seriallar topilmadi
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
