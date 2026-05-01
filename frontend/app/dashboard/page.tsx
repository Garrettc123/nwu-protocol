'use client';

import { useEffect, useState } from 'react';
import { useWallet } from '@/hooks/useWallet';
import { api, Contribution, User, Subscription } from '@/lib/api';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';

export default function Dashboard() {
  const { address, connected } = useWallet();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [user, setUser] = useState<User | null>(null);
  const [contributions, setContributions] = useState<Contribution[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [rewards, setRewards] = useState<any>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [portalLoading, setPortalLoading] = useState(false);

  const checkoutStatus = searchParams.get('checkout');

  useEffect(() => {
    if (!connected || !address) {
      router.push('/');
      return;
    }

    const loadData = async () => {
      try {
        setLoading(true);

        const [userData, userContributions, userStats, userRewards, sub] = await Promise.all([
          api.getUser(address).catch(() => null),
          api.getUserContributions(address).catch(() => ({ contributions: [] })),
          api.getUserStats(address).catch(() => null),
          api.getUserRewards(address).catch(() => null),
          api.getSubscription().catch(() => null),
        ]);

        setUser(userData);
        setContributions(userContributions.contributions ?? []);
        setStats(userStats);
        setRewards(userRewards);
        setSubscription(sub);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [address, connected, router]);

  const handleManageBilling = async () => {
    setPortalLoading(true);
    try {
      const appUrl = process.env.NEXT_PUBLIC_APP_URL || window.location.origin;
      const { portal_url } = await api.getCustomerPortalUrl(`${appUrl}/dashboard`);
      window.location.href = portal_url;
    } catch {
      setPortalLoading(false);
    }
  };

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

  const tierLabel: Record<string, string> = { free: 'Free', pro: 'Pro', enterprise: 'Enterprise' };
  const tierColor: Record<string, string> = {
    free: 'text-gray-400',
    pro: 'text-blue-400',
    enterprise: 'text-purple-400',
  };
  const currentTier = subscription?.tier ?? 'free';

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Checkout result banners */}
        {checkoutStatus === 'success' && (
          <div className="mb-6 bg-green-900/40 border border-green-500 rounded-lg p-4 text-green-300 text-sm">
            Payment successful! Your subscription is now active. It may take a moment to reflect here.
          </div>
        )}
        {checkoutStatus === 'canceled' && (
          <div className="mb-6 bg-yellow-900/40 border border-yellow-500 rounded-lg p-4 text-yellow-300 text-sm">
            Checkout was canceled. No charge was made.{' '}
            <Link href="/pricing" className="underline hover:text-yellow-100">
              View plans
            </Link>
          </div>
        )}

        {/* Header */}
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="text-gray-400 mt-2">
              Welcome back, {address?.substring(0, 6)}...{address?.substring(38)}
            </p>
          </div>
        </div>

        {/* Subscription Banner */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-5 mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">Current Plan</p>
            <div className="flex items-center gap-3">
              <span className={`text-2xl font-bold ${tierColor[currentTier]}`}>
                {tierLabel[currentTier] ?? currentTier}
              </span>
              {subscription?.current_period_end && currentTier !== 'free' && (
                <span className="text-gray-500 text-sm">
                  renews {new Date(subscription.current_period_end).toLocaleDateString()}
                </span>
              )}
              {subscription?.cancel_at_period_end && (
                <span className="text-red-400 text-xs bg-red-900/30 px-2 py-0.5 rounded">
                  Cancels at period end
                </span>
              )}
            </div>
            <p className="text-gray-500 text-sm mt-1">
              {subscription?.rate_limit?.toLocaleString() ?? 100} API requests / day
            </p>
          </div>
          <div className="flex gap-3 shrink-0">
            {currentTier === 'free' ? (
              <Link
                href="/pricing"
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-semibold transition"
              >
                Upgrade Plan
              </Link>
            ) : (
              <button
                onClick={handleManageBilling}
                disabled={portalLoading}
                className="px-5 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-semibold transition disabled:opacity-60"
              >
                {portalLoading ? 'Opening…' : 'Manage Billing'}
              </button>
            )}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-gray-400 text-sm mb-2">Total Contributions</div>
            <div className="text-3xl font-bold">{stats?.total_contributions ?? 0}</div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-gray-400 text-sm mb-2">Verified</div>
            <div className="text-3xl font-bold text-green-500">
              {stats?.verified_contributions ?? 0}
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-gray-400 text-sm mb-2">Avg. Quality Score</div>
            <div className="text-3xl font-bold">{stats?.average_quality_score ?? 0}</div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-gray-400 text-sm mb-2">Total Rewards</div>
            <div className="text-3xl font-bold text-yellow-500">
              {(user?.total_rewards ?? 0).toFixed(2)} NWU
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
                {(rewards?.pending_amount ?? 0).toFixed(2)} NWU
              </div>
            </div>
            <div>
              <div className="text-gray-400 text-sm">Distributed</div>
              <div className="text-2xl font-bold text-green-400">
                {(rewards?.distributed_amount ?? 0).toFixed(2)} NWU
              </div>
            </div>
            <div>
              <div className="text-gray-400 text-sm">Reputation Score</div>
              <div className="text-2xl font-bold">{user?.reputation_score ?? 0}</div>
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
