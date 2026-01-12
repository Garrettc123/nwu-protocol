'use client';

import { useEffect, useState } from 'react';
import { useWallet } from '@/hooks/useWallet';
import { api, Contribution, User } from '@/lib/api';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function Dashboard() {
  const { address, connected } = useWallet();
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [contributions, setContributions] = useState<Contribution[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [rewards, setRewards] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!connected || !address) {
      router.push('/');
      return;
    }

    const loadData = async () => {
      try {
        setLoading(true);

        // Load user data
        const [userData, userContributions, userStats, userRewards] = await Promise.all([
          api.getUser(address).catch(() => null),
          api.getUserContributions(address),
          api.getUserStats(address),
          api.getUserRewards(address),
        ]);

        setUser(userData);
        setContributions(userContributions.contributions || []);
        setStats(userStats);
        setRewards(userRewards);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [address, connected, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-gray-400 mt-2">
            Welcome back, {address?.substring(0, 6)}...{address?.substring(38)}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-gray-400 text-sm mb-2">Total Contributions</div>
            <div className="text-3xl font-bold">{stats?.total_contributions || 0}</div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-gray-400 text-sm mb-2">Verified</div>
            <div className="text-3xl font-bold text-green-500">
              {stats?.verified_contributions || 0}
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-gray-400 text-sm mb-2">Avg. Quality Score</div>
            <div className="text-3xl font-bold">{stats?.average_quality_score || 0}</div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-gray-400 text-sm mb-2">Total Rewards</div>
            <div className="text-3xl font-bold text-yellow-500">
              {user?.total_rewards.toFixed(2) || '0.00'} NWU
            </div>
          </div>
        </div>

        {/* Rewards Section */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-8">
          <h2 className="text-xl font-bold mb-4">Rewards</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-gray-400 text-sm">Pending</div>
              <div className="text-2xl font-bold text-yellow-400">
                {rewards?.pending_amount?.toFixed(2) || '0.00'} NWU
              </div>
            </div>
            <div>
              <div className="text-gray-400 text-sm">Distributed</div>
              <div className="text-2xl font-bold text-green-400">
                {rewards?.distributed_amount?.toFixed(2) || '0.00'} NWU
              </div>
            </div>
            <div>
              <div className="text-gray-400 text-sm">Reputation Score</div>
              <div className="text-2xl font-bold">{user?.reputation_score || 0}</div>
            </div>
          </div>
        </div>

        {/* Recent Contributions */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Recent Contributions</h2>
            <Link
              href="/upload"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition"
            >
              New Contribution
            </Link>
          </div>

          {contributions.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <p>No contributions yet.</p>
              <Link href="/upload" className="text-blue-400 hover:text-blue-300 mt-2 inline-block">
                Upload your first contribution
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {contributions.map(contribution => (
                <div
                  key={contribution.id}
                  className="bg-gray-900 p-4 rounded-lg border border-gray-700 hover:border-gray-600 transition"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">{contribution.title}</h3>
                      <p className="text-gray-400 text-sm mt-1">{contribution.description}</p>
                      <div className="flex gap-4 mt-2 text-sm">
                        <span className="text-gray-500">Type: {contribution.file_type}</span>
                        <span className="text-gray-500">
                          Status:{' '}
                          <span
                            className={
                              contribution.status === 'verified'
                                ? 'text-green-400'
                                : contribution.status === 'verifying'
                                  ? 'text-yellow-400'
                                  : contribution.status === 'rejected'
                                    ? 'text-red-400'
                                    : 'text-gray-400'
                            }
                          >
                            {contribution.status}
                          </span>
                        </span>
                        {contribution.quality_score && (
                          <span className="text-gray-500">
                            Score:{' '}
                            <span className="text-blue-400">{contribution.quality_score}</span>
                          </span>
                        )}
                      </div>
                    </div>
                    <Link
                      href={`/contributions/${contribution.id}`}
                      className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
                    >
                      View
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
