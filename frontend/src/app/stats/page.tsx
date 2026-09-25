'use client';

import { AdminLayout } from '@/components/layout/AdminLayout';
import { useQuery } from '@tanstack/react-query';
import { getDashboard } from '@/services/api';
import { StatCard } from '@/components/ui/StatCard';
import { Users, Film, Eye, Search, TrendingUp, BarChart3, Clock } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function StatsPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboard,
  });

  return (
    <AdminLayout>
      <div className="space-y-6 pb-12">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-6 h-6 text-indigo-500" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">To'liq Statistika va Tahlil</h1>
            <p className="text-gray-500 text-sm">Foydalanuvchilar faolligi, eng mashhur filmlar va qidiruv tahlillari</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          <StatCard
            label="Jami foydalanuvchilar"
            value={stats?.total_users ?? 0}
            icon={Users}
            color="indigo"
            change={stats?.new_users_today}
          />
          <StatCard
            label="Jami filmlar"
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

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="card space-y-4">
            <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-500" /> 🔥 Eng ko'p ko'rilgan 10 ta film
            </h2>
            {stats?.top_movies && stats.top_movies.length > 0 ? (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.top_movies} layout="vertical" margin={{ left: 10, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                    <XAxis type="number" tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                    <YAxis
                      type="category"
                      dataKey="title"
                      width={130}
                      tick={{ fill: '#9CA3AF', fontSize: 11 }}
                      tickFormatter={(val) => val.length > 15 ? val.substring(0, 15) + '...' : val}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: 8, color: '#fff' }}
                      formatter={(val: number) => [`${val.toLocaleString()} marta`, "Ko'rishlar"]}
                    />
                    <Bar dataKey="views_count" fill="#6366f1" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-gray-400 text-sm py-10 text-center">Ma'lumotlar yo'q</p>
            )}
          </div>

          <div className="card space-y-4">
            <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Search className="w-5 h-5 text-indigo-500" /> 🔎 Eng ko'p qidirilgan so'zlar
            </h2>
            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {stats?.popular_searches && stats.popular_searches.length > 0 ? (
                stats.popular_searches.map((s: any, i: number) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800/40 border border-gray-100 dark:border-gray-800"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="font-bold text-xs text-gray-400">#{i + 1}</span>
                      <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                        {s.query}
                      </span>
                    </div>
                    <span className="text-xs bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 font-bold px-2.5 py-1 rounded-full">
                      {s.count} marta
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-gray-400 text-sm py-10 text-center">Qidiruvlar tarixi yo'q</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
