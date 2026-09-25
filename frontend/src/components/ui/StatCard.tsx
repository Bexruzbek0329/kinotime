import clsx from 'clsx';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  color?: 'indigo' | 'green' | 'blue' | 'orange';
  change?: number;
}

const colorMap = {
  indigo: 'bg-indigo-500/10 text-indigo-500',
  green: 'bg-green-500/10 text-green-500',
  blue: 'bg-blue-500/10 text-blue-500',
  orange: 'bg-orange-500/10 text-orange-500',
};

export function StatCard({ label, value, icon: Icon, color = 'indigo', change }: StatCardProps) {
  return (
    <div className="card flex items-start justify-between">
      <div>
        <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
        <p className="text-2xl font-bold mt-1 text-gray-900 dark:text-white">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </p>
        {change !== undefined && (
          <p className={clsx('text-xs mt-1', change >= 0 ? 'text-green-500' : 'text-red-500')}>
            {change >= 0 ? '+' : ''}{change} bugun
          </p>
        )}
      </div>
      <div className={clsx('w-12 h-12 rounded-xl flex items-center justify-center', colorMap[color])}>
        <Icon className="w-6 h-6" />
      </div>
    </div>
  );
}
