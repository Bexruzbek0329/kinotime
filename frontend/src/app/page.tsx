'use client';

import { AdminLayout } from '@/components/layout/AdminLayout';
import { StatCard } from '@/components/ui/StatCard';
import { useQuery } from '@tanstack/react-query';
import { getDashboard } from '@/services/api';
import { Users, Film, Eye, Search, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboard,
    refetchInterval: 30000,
  });

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">KinoBot jonli statistikasi va umumiy ko'rinishi</p>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="card animate-pulse h-28 bg-gray-200 dark:bg-gray-800" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <StatCard
              label="Jami foydalanuvchilar"
              value={stats?.total_users ?? 0}
              icon={Users}
              color="indigo"
              change={stats?.new_users_today}
            />
            <StatCard
              label="Jami kinolar"
              value={stats?.total_movies ?? 0}
              icon={Film}
              color="blue"
            />
            <StatCard
              label="Jami ko'rishlar"
              value={stats?.total_views ?? 0}
              icon={Eye}
              color="green"
            />
            <StatCard
              label="Bugungi qidiruvlar"
              value={stats?.searches_today ?? 0}
              icon={Search}
              color="orange"
            />
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-500" />
              Eng ko'p ko'rilgan kinolar (Top 10)
            </h2>
            {stats?.top_movies && stats.top_movies.length > 0 ? (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.top_movies.slice(0, 8)} layout="vertical" margin={{ left: 10, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                    <XAxis type="number" tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                    <YAxis
                      type="category"
                      dataKey="title"
                      width={120}
                      tick={{ fill: '#9CA3AF', fontSize: 11 }}
                      tickFormatter={(val) => val.length > 14 ? val.substring(0, 14) + '...' : val}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: 8, color: '#fff' }}
                      formatter={(val: number) => [`${val} marta`, "Ko'rildi"]}
                    />
                    <Bar dataKey="views_count" fill="#6366f1" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
                Hozircha ko'rishlar qayd etilmagan
              </div>
            )}
          </div>

          <div className="card">
            <h2 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Search className="w-5 h-5 text-red-500" />
              Topilmagan qidiruvlar (Foydalanuvchilar qidirgan)
            </h2>
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {stats?.not_found_searches && stats.not_found_searches.length > 0 ? (
                stats.not_found_searches.map((s: { query: string; count: number }, i: number) => (
                  <div
                    key={i}
                    className="flex items-center justify-between py-2.5 px-3 rounded-lg bg-gray-50 dark:bg-gray-800/60 border border-gray-100 dark:border-gray-800"
                  >
                    <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                      🔍 {s.query}
                    </span>
                    <span className="text-xs bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400 font-semibold px-2.5 py-1 rounded-full">
                      {s.count} marta
                    </span>
                  </div>
                ))
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
                  Topilmagan qidiruvlar yo'q
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
