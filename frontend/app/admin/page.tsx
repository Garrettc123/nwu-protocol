'use client';

import { useEffect, useState } from 'react';
import { useWallet } from '@/hooks/useWallet';
import { authService } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface RevenueSummary {
  mrr: number;
  arr: number;
  revenue_this_month: number;
  churn_rate: number;
  active_subscriptions: number;
}

interface DailyRevenue {
  date: string;
  amount: number;
}

interface UserStats {
  total_users: number;
  active_users_30d: number;
  new_users_this_week: number;
}

interface ApiKeyStats {
  total_calls_today: number;
  total_calls_this_month: number;
  top_consumers: { subscription_id: number; total_calls: number }[];
}

interface StakingStats {
  total_nwu_staked: number;
  yield_distributed: number;
  staking_participation_rate: number;
}

function MetricCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: string;
}) {
  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
      <div className="text-gray-400 text-sm mb-2">{label}</div>
      <div className={`text-3xl font-bold ${accent ?? ''}`}>{value}</div>
      {sub && <div className="text-gray-500 text-xs mt-1">{sub}</div>}
    </div>
  );
}

function RevenueChart({ data }: { data: DailyRevenue[] }) {
  if (!data.length) return null;

  const chartWidth = 800;
  const chartHeight = 200;
  const paddingX = 8;
  const paddingY = 16;
  const innerWidth = chartWidth - paddingX * 2;
  const innerHeight = chartHeight - paddingY * 2;

  const maxAmount = Math.max(...data.map(d => d.amount), 1);
  const stepX = innerWidth / (data.length - 1 || 1);

  const points = data.map((d, index) => {
    const x = paddingX + index * stepX;
    const y = paddingY + innerHeight - (d.amount / maxAmount) * innerHeight;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const polylinePoints = points.join(' ');

  // Build closed polygon for the filled area
  const firstPoint = points[0];
  const lastPoint = points[points.length - 1];
  const bottomLeft = `${paddingX.toFixed(1)},${(paddingY + innerHeight).toFixed(1)}`;
  const bottomRight = `${(paddingX + innerWidth).toFixed(1)},${(paddingY + innerHeight).toFixed(1)}`;
  const areaPoints = `${bottomLeft} ${polylinePoints} ${bottomRight}`;

  // Axis labels: first, middle, last date
  const labelIndices = [0, Math.floor(data.length / 2), data.length - 1];

  return (
    <div className="overflow-x-auto">
      <svg
        viewBox={`0 0 ${chartWidth} ${chartHeight + 24}`}
        className="w-full"
        aria-label="90-day daily revenue chart"
      >
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map(fraction => {
          const y = paddingY + innerHeight - fraction * innerHeight;
          return (
            <line
              key={fraction}
              x1={paddingX}
              y1={y}
              x2={paddingX + innerWidth}
              y2={y}
              stroke="#374151"
              strokeWidth="1"
            />
          );
        })}

        {/* Filled area */}
        <polygon points={areaPoints} fill="rgba(59,130,246,0.15)" />

        {/* Revenue line */}
        <polyline
          points={polylinePoints}
          fill="none"
          stroke="#3b82f6"
          strokeWidth="2"
          strokeLinejoin="round"
        />

        {/* X-axis date labels */}
        {labelIndices.map(index => {
          const x = paddingX + index * stepX;
          const label = data[index]?.date ?? '';
          return (
            <text
              key={index}
              x={x}
              y={chartHeight + 18}
              textAnchor="middle"
              fontSize="10"
              fill="#9ca3af"
            >
              {label}
            </text>
          );
        })}

        {/* Y-axis max label */}
        <text x={paddingX + 2} y={paddingY - 4} fontSize="10" fill="#9ca3af">
          ${maxAmount.toLocaleString()}
        </text>
      </svg>
    </div>
  );
}

export default function AdminDashboard() {
  const { connected } = useWallet();
  const router = useRouter();

  const [revenueSummary, setRevenueSummary] = useState<RevenueSummary | null>(null);
  const [dailyRevenue, setDailyRevenue] = useState<DailyRevenue[]>([]);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [apiKeyStats, setApiKeyStats] = useState<ApiKeyStats | null>(null);
  const [stakingStats, setStakingStats] = useState<StakingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!connected) {
      router.push('/');
      return;
    }

    const token = authService.getAuthToken();
    if (!token) {
      router.push('/');
      return;
    }

    const headers = { Authorization: `Bearer ${token}` };

    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [summaryRes, dailyRes, usersRes, apiKeysRes, stakingRes] = await Promise.all([
          axios.get(`${API_BASE}/api/v1/admin/revenue/summary`, { headers }),
          axios.get(`${API_BASE}/api/v1/admin/revenue/daily`, { headers }),
          axios.get(`${API_BASE}/api/v1/admin/users/stats`, { headers }),
          axios.get(`${API_BASE}/api/v1/admin/api-keys/stats`, { headers }),
          axios.get(`${API_BASE}/api/v1/admin/staking/stats`, { headers }),
        ]);

        setRevenueSummary(summaryRes.data);
        setDailyRevenue(dailyRes.data.daily ?? []);
        setUserStats(usersRes.data);
        setApiKeyStats(apiKeysRes.data);
        setStakingStats(stakingRes.data);
      } catch (err: unknown) {
        if (axios.isAxiosError(err) && err.response?.status === 403) {
          setError('Access denied. Admin privileges required.');
        } else {
          setError('Failed to load admin data. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [connected, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          <p className="text-gray-400 mt-2">Revenue metrics and analytics</p>
        </div>

        {/* Revenue Metrics */}
        <h2 className="text-xl font-semibold mb-4">Revenue</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
          <MetricCard
            label="MRR"
            value={`$${revenueSummary?.mrr.toLocaleString() ?? '—'}`}
            sub="Monthly Recurring Revenue"
            accent="text-green-400"
          />
          <MetricCard
            label="ARR"
            value={`$${revenueSummary?.arr.toLocaleString() ?? '—'}`}
            sub="Annual Recurring Revenue"
            accent="text-green-300"
          />
          <MetricCard
            label="This Month"
            value={`$${revenueSummary?.revenue_this_month.toLocaleString() ?? '—'}`}
            sub="Total revenue this month"
          />
          <MetricCard
            label="Churn Rate"
            value={`${revenueSummary?.churn_rate ?? '—'}%`}
            sub="Last 30 days"
            accent="text-red-400"
          />
          <MetricCard
            label="Active Subscriptions"
            value={String(revenueSummary?.active_subscriptions ?? '—')}
            accent="text-blue-400"
          />
        </div>

        {/* 90-Day Revenue Chart */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Daily Revenue — Last 90 Days</h2>
          <RevenueChart data={dailyRevenue} />
        </div>

        {/* User Stats */}
        <h2 className="text-xl font-semibold mb-4">Users</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <MetricCard label="Total Users" value={String(userStats?.total_users ?? '—')} />
          <MetricCard
            label="Active (30d)"
            value={String(userStats?.active_users_30d ?? '—')}
            sub="Users active in the last 30 days"
            accent="text-blue-400"
          />
          <MetricCard
            label="New This Week"
            value={String(userStats?.new_users_this_week ?? '—')}
            accent="text-yellow-400"
          />
        </div>

        {/* API Key Stats */}
        <h2 className="text-xl font-semibold mb-4">API Usage</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <MetricCard
            label="Calls Today"
            value={apiKeyStats?.total_calls_today.toLocaleString() ?? '—'}
          />
          <MetricCard
            label="Calls This Month"
            value={apiKeyStats?.total_calls_this_month.toLocaleString() ?? '—'}
          />
        </div>

        {apiKeyStats && apiKeyStats.top_consumers.length > 0 && (
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">Top API Consumers (This Month)</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 border-b border-gray-700">
                    <th className="text-left pb-3">#</th>
                    <th className="text-left pb-3">Subscription ID</th>
                    <th className="text-right pb-3">Total Calls</th>
                  </tr>
                </thead>
                <tbody>
                  {apiKeyStats.top_consumers.map((consumer, index) => (
                    <tr
                      key={consumer.subscription_id}
                      className="border-b border-gray-700 hover:bg-gray-700 transition"
                    >
                      <td className="py-3 text-gray-400">{index + 1}</td>
                      <td className="py-3">{consumer.subscription_id}</td>
                      <td className="py-3 text-right font-mono">
                        {consumer.total_calls.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Staking Stats */}
        <h2 className="text-xl font-semibold mb-4">NWU Staking</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <MetricCard
            label="Total NWU Staked"
            value={`${stakingStats?.total_nwu_staked.toLocaleString() ?? '—'} NWU`}
            accent="text-purple-400"
          />
          <MetricCard
            label="Yield Distributed"
            value={`${stakingStats?.yield_distributed.toLocaleString() ?? '—'} NWU`}
            accent="text-green-400"
          />
          <MetricCard
            label="Participation Rate"
            value={`${stakingStats?.staking_participation_rate ?? '—'}%`}
          />
        </div>
      </div>
    </div>
  );
}
