'use client';

import { useEffect, useState, useCallback } from 'react';
import { useWallet } from '@/hooks/useWallet';
import { api, UserRewards, UserStats, Reward } from '@/lib/api';
import { authService } from '@/lib/auth';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

function shortenAddress(address: string): string {
  return `${address.substring(0, 6)}...${address.substring(38)}`;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function getBlockExplorerUrl(chainId: number | null, txHash: string): string {
  const explorers: Record<number, string> = {
    1: 'https://etherscan.io',
    5: 'https://goerli.etherscan.io',
    11155111: 'https://sepolia.etherscan.io',
    137: 'https://polygonscan.com',
    80001: 'https://mumbai.polygonscan.com',
    56: 'https://bscscan.com',
    43114: 'https://snowtrace.io',
    42161: 'https://arbiscan.io',
    10: 'https://optimistic.etherscan.io',
    8453: 'https://basescan.org',
  };
  const base = (chainId && explorers[chainId]) || 'https://etherscan.io';
  return `${base}/tx/${txHash}`;
}

function RewardStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: 'bg-yellow-900 text-yellow-300 border-yellow-700',
    processing: 'bg-blue-900 text-blue-300 border-blue-700',
    distributed: 'bg-green-900 text-green-300 border-green-700',
    failed: 'bg-red-900 text-red-300 border-red-700',
  };
  const style = styles[status] || 'bg-gray-700 text-gray-300 border-gray-600';
  return (
    <span className={`px-2 py-0.5 rounded border text-xs font-medium ${style}`}>{status}</span>
  );
}

export default function WalletPage() {
  const { address, connected, connecting, ethBalance, chainId, networkName, connect, disconnect, refreshBalance } =
    useWallet();
  const router = useRouter();

  const [rewards, setRewards] = useState<UserRewards | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'history'>('overview');

  const loadWalletData = useCallback(async () => {
    if (!address) return;
    try {
      setLoading(true);
      const [rewardsData, statsData] = await Promise.all([
        api.getUserRewards(address).catch(() => null),
        api.getUserStats(address).catch(() => null),
      ]);
      setRewards(rewardsData);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load wallet data:', error);
    } finally {
      setLoading(false);
    }
  }, [address]);

  useEffect(() => {
    if (connected && address) {
      loadWalletData();
    }
  }, [connected, address, loadWalletData]);

  const handleCopyAddress = async () => {
    if (!address) return;
    try {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      console.error('Failed to copy address to clipboard');
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([refreshBalance(), loadWalletData()]);
    setRefreshing(false);
  };

  const handleDisconnect = async () => {
    if (address) {
      await authService.logout(address);
      authService.clearAuthToken();
    }
    disconnect();
    router.push('/');
  };

  if (!connected) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="text-6xl mb-6">💼</div>
          <h1 className="text-3xl font-bold mb-4">Connect Your Wallet</h1>
          <p className="text-gray-400 mb-8">
            Connect your MetaMask wallet to view your NWU balances, rewards, and transaction
            history.
          </p>
          <button
            onClick={connect}
            disabled={connecting}
            className="px-8 py-3 bg-green-600 hover:bg-green-700 rounded-lg font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {connecting ? 'Connecting...' : 'Connect Wallet'}
          </button>
          <div className="mt-6">
            <Link href="/" className="text-gray-400 hover:text-white transition text-sm">
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const pendingRewards = rewards?.rewards.filter(r => r.status === 'pending') ?? [];
  const distributedRewards = rewards?.rewards.filter(r => r.status === 'distributed') ?? [];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">My Wallet</h1>
          <div className="flex gap-3">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition text-sm disabled:opacity-50"
            >
              {refreshing ? '↻ Refreshing...' : '↻ Refresh'}
            </button>
            <button
              onClick={handleDisconnect}
              className="px-4 py-2 bg-red-700 hover:bg-red-600 rounded-lg transition text-sm"
            >
              Disconnect
            </button>
          </div>
        </div>

        {/* Wallet Address Card */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-gray-400 text-sm mb-2">Wallet Address</div>
              <div className="flex items-center gap-3">
                <span className="font-mono text-lg font-semibold">
                  {address ? shortenAddress(address) : '—'}
                </span>
                <button
                  onClick={handleCopyAddress}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs transition"
                >
                  {copied ? '✓ Copied' : 'Copy'}
                </button>
              </div>
              {address && (
                <div className="font-mono text-xs text-gray-500 mt-1 break-all">{address}</div>
              )}
            </div>
            <div className="text-right">
              <div className="flex items-center gap-2 justify-end mb-1">
                <span
                  className={`w-2 h-2 rounded-full ${chainId ? 'bg-green-400' : 'bg-gray-500'}`}
                />
                <span className="text-sm text-gray-300">{networkName || 'Unknown Network'}</span>
              </div>
              {chainId && (
                <div className="text-xs text-gray-500">Chain ID: {chainId}</div>
              )}
            </div>
          </div>
        </div>

        {/* Balance Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="text-gray-400 text-sm mb-2">ETH Balance</div>
            <div className="text-2xl font-bold">
              {ethBalance !== null ? (
                <>
                  <span>{ethBalance}</span>
                  <span className="text-gray-400 text-base ml-1">ETH</span>
                </>
              ) : (
                <span className="text-gray-500">—</span>
              )}
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="text-gray-400 text-sm mb-2">Pending NWU Rewards</div>
            <div className="text-2xl font-bold text-yellow-400">
              {loading ? (
                <span className="text-gray-500 text-base">Loading...</span>
              ) : (
                <>
                  <span>{rewards?.pending_amount?.toFixed(4) ?? '0.0000'}</span>
                  <span className="text-gray-400 text-base ml-1">NWU</span>
                </>
              )}
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="text-gray-400 text-sm mb-2">Total NWU Earned</div>
            <div className="text-2xl font-bold text-green-400">
              {loading ? (
                <span className="text-gray-500 text-base">Loading...</span>
              ) : (
                <>
                  <span>{rewards?.total_rewards?.toFixed(4) ?? '0.0000'}</span>
                  <span className="text-gray-400 text-base ml-1">NWU</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 text-center">
            <div className="text-2xl font-bold">{stats?.total_contributions ?? '—'}</div>
            <div className="text-gray-400 text-xs mt-1">Contributions</div>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 text-center">
            <div className="text-2xl font-bold text-green-400">
              {stats?.verified_contributions ?? '—'}
            </div>
            <div className="text-gray-400 text-xs mt-1">Verified</div>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 text-center">
            <div className="text-2xl font-bold">{stats?.average_quality_score?.toFixed(1) ?? '—'}</div>
            <div className="text-gray-400 text-xs mt-1">Avg. Quality</div>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 text-center">
            <div className="text-2xl font-bold text-blue-400">
              {stats?.reputation_score?.toFixed(0) ?? '—'}
            </div>
            <div className="text-gray-400 text-xs mt-1">Reputation</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
          <div className="flex border-b border-gray-700">
            <button
              onClick={() => setActiveTab('overview')}
              className={`flex-1 py-3 text-sm font-medium transition ${
                activeTab === 'overview'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-750'
              }`}
            >
              Pending Rewards ({pendingRewards.length})
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex-1 py-3 text-sm font-medium transition ${
                activeTab === 'history'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-750'
              }`}
            >
              Reward History ({rewards?.rewards.length ?? 0})
            </button>
          </div>

          <div className="p-6">
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500 mx-auto"></div>
                <p className="mt-3 text-gray-400 text-sm">Loading rewards...</p>
              </div>
            ) : activeTab === 'overview' ? (
              pendingRewards.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <div className="text-4xl mb-3">🏆</div>
                  <p className="font-medium">No pending rewards</p>
                  <p className="text-sm mt-1">
                    Upload and verify contributions to earn NWU tokens.
                  </p>
                  <Link
                    href="/upload"
                    className="inline-block mt-4 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm transition"
                  >
                    Upload Contribution
                  </Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {pendingRewards.map((reward: Reward) => (
                    <div
                      key={reward.id}
                      className="flex items-center justify-between bg-gray-900 rounded-lg p-4 border border-gray-700"
                    >
                      <div>
                        <div className="text-sm text-gray-400">
                          Contribution #{reward.contribution_id}
                        </div>
                        <div className="text-xs text-gray-500 mt-0.5">
                          {formatDate(reward.created_at)}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-yellow-400">
                          +{reward.amount.toFixed(4)} NWU
                        </span>
                        <RewardStatusBadge status={reward.status} />
                      </div>
                    </div>
                  ))}
                  <div className="mt-4 pt-4 border-t border-gray-700 flex justify-between items-center">
                    <span className="text-gray-400 text-sm">
                      Total pending: {pendingRewards.length} reward(s)
                    </span>
                    <span className="font-bold text-yellow-400">
                      {rewards?.pending_amount?.toFixed(4)} NWU
                    </span>
                  </div>
                </div>
              )
            ) : rewards?.rewards.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <div className="text-4xl mb-3">📋</div>
                <p className="font-medium">No reward history yet</p>
                <p className="text-sm mt-1">Your reward transactions will appear here.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-gray-400 text-left border-b border-gray-700">
                      <th className="pb-3 pr-4">Contribution</th>
                      <th className="pb-3 pr-4">Amount</th>
                      <th className="pb-3 pr-4">Status</th>
                      <th className="pb-3 pr-4">Date</th>
                      <th className="pb-3">Tx Hash</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {rewards?.rewards.map((reward: Reward) => (
                      <tr key={reward.id} className="hover:bg-gray-750 transition">
                        <td className="py-3 pr-4 text-gray-300">#{reward.contribution_id}</td>
                        <td className="py-3 pr-4 font-medium text-green-400">
                          +{reward.amount.toFixed(4)} NWU
                        </td>
                        <td className="py-3 pr-4">
                          <RewardStatusBadge status={reward.status} />
                        </td>
                        <td className="py-3 pr-4 text-gray-400">
                          {formatDate(reward.created_at)}
                        </td>
                        <td className="py-3">
                          {reward.tx_hash ? (
                            <a
                              href={getBlockExplorerUrl(chainId, reward.tx_hash)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="font-mono text-xs text-blue-400 hover:text-blue-300 transition"
                            >
                              {reward.tx_hash.substring(0, 10)}...
                            </a>
                          ) : (
                            <span className="text-gray-600 text-xs">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link
            href="/upload"
            className="bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-green-600 rounded-xl p-5 text-center transition group"
          >
            <div className="text-3xl mb-2">📤</div>
            <div className="font-semibold group-hover:text-green-400 transition">
              Upload Contribution
            </div>
            <div className="text-gray-400 text-xs mt-1">Earn NWU tokens</div>
          </Link>

          <Link
            href="/dashboard"
            className="bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-blue-600 rounded-xl p-5 text-center transition group"
          >
            <div className="text-3xl mb-2">📊</div>
            <div className="font-semibold group-hover:text-blue-400 transition">Dashboard</div>
            <div className="text-gray-400 text-xs mt-1">View all activity</div>
          </Link>

          <Link
            href="/contributions"
            className="bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-purple-600 rounded-xl p-5 text-center transition group"
          >
            <div className="text-3xl mb-2">🔍</div>
            <div className="font-semibold group-hover:text-purple-400 transition">
              Browse Contributions
            </div>
            <div className="text-gray-400 text-xs mt-1">Explore verified work</div>
          </Link>
        </div>
      </div>
    </div>
  );
}
