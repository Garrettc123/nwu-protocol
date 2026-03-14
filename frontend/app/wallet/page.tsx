'use client';

import { useEffect, useState } from 'react';
import { useWallet } from '@/hooks/useWallet';
import { api, Reward, RewardsSummary, UserStats, User } from '@/lib/api';
import { authService } from '@/lib/auth';
import { useRouter } from 'next/navigation';

type RewardTab = 'all' | 'pending' | 'distributed';

function getExplorerTxUrl(txHash: string, chainId: number | null): string {
  switch (chainId) {
    case 1:
      return `https://etherscan.io/tx/${txHash}`;
    case 137:
      return `https://polygonscan.com/tx/${txHash}`;
    case 42161:
      return `https://arbiscan.io/tx/${txHash}`;
    default:
      return `https://etherscan.io/tx/${txHash}`;
  }
}

function getExplorerName(chainId: number | null): string {
  switch (chainId) {
    case 137:
      return 'Polygonscan';
    case 42161:
      return 'Arbiscan';
    default:
      return 'Etherscan';
  }
}

function shortenAddress(address: string): string {
  return `${address.substring(0, 6)}...${address.substring(38)}`;
}

function shortenHash(hash: string): string {
  return `${hash.substring(0, 10)}...${hash.substring(hash.length - 8)}`;
}

export default function WalletPage() {
  const { address, connected, chainId, networkName, ethBalance, refreshBalance, disconnect } =
    useWallet();
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [rewardsSummary, setRewardsSummary] = useState<RewardsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<RewardTab>('all');

  useEffect(() => {
    if (!connected || !address) {
      router.push('/');
      return;
    }

    const loadData = async () => {
      try {
        setLoading(true);
        const [userData, userStats, userRewards] = await Promise.all([
          api.getUser(address).catch(() => null),
          api.getUserStats(address).catch(() => null),
          api.getUserRewards(address).catch(() => null),
        ]);

        setUser(userData);
        setStats(userStats);
        setRewardsSummary(userRewards);
      } catch (error) {
        console.error('Failed to load wallet data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [address, connected, router]);

  const handleRefreshBalance = async () => {
    setRefreshing(true);
    await refreshBalance();
    setRefreshing(false);
  };

  const handleCopyAddress = async () => {
    if (!address) return;
    setCopyError(null);
    try {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopyError('Failed to copy — please copy manually');
      setTimeout(() => setCopyError(null), 3000);
    }
  };

  const handleDisconnect = async () => {
    if (address) {
      await authService.logout(address);
      authService.clearAuthToken();
    }
    disconnect();
    router.push('/');
  };

  const filteredRewards = (rewardsSummary?.rewards ?? []).filter((reward: Reward) => {
    if (activeTab === 'pending') return reward.status === 'pending' || reward.status === 'processing';
    if (activeTab === 'distributed') return reward.status === 'distributed';
    return true;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading wallet...</p>
        </div>
      </div>
    );
  }

  const totalRewards =
    (rewardsSummary?.pending_amount ?? 0) + (rewardsSummary?.distributed_amount ?? 0);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold">Wallet</h1>
            <p className="text-gray-400 mt-1">Manage your NWU rewards and account</p>
          </div>
          <button
            onClick={handleDisconnect}
            className="self-start sm:self-auto px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition text-sm font-medium"
          >
            Disconnect
          </button>
        </div>

        {/* Address + Network Card */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="text-gray-400 text-xs uppercase tracking-wider mb-1">Address</div>
              <div className="flex items-center gap-3">
                <span className="font-mono text-lg">
                  {address ? shortenAddress(address) : '—'}
                </span>
                <button
                  onClick={handleCopyAddress}
                  title="Copy full address"
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition"
                >
                  {copied ? '✓ Copied' : 'Copy'}
                </button>
              </div>
              {copyError && <p className="mt-1 text-xs text-red-400">{copyError}</p>}
              {address && (
                <p className="mt-1 text-xs text-gray-500 font-mono break-all">{address}</p>
              )}
            </div>

            <div className="flex flex-col sm:items-end gap-1">
              <div className="text-gray-400 text-xs uppercase tracking-wider">Network</div>
              <div className="text-white font-medium">{networkName ?? '—'}</div>
              {chainId !== null && (
                <div className="text-gray-400 text-xs">Chain ID: {chainId}</div>
              )}
            </div>
          </div>
        </div>

        {/* ETH Balance Card */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-gray-400 text-xs uppercase tracking-wider mb-1">ETH Balance</div>
              <div className="text-3xl font-bold">
                {ethBalance !== null ? `${parseFloat(ethBalance).toFixed(6)} ETH` : '—'}
              </div>
            </div>
            <button
              onClick={handleRefreshBalance}
              disabled={refreshing}
              title="Refresh balance"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition text-sm font-medium"
            >
              {refreshing ? 'Refreshing…' : '↻ Refresh'}
            </button>
          </div>
        </div>

        {/* NWU Rewards Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="text-gray-400 text-xs uppercase tracking-wider mb-2">
              Pending Rewards
            </div>
            <div className="text-2xl font-bold text-yellow-400">
              {(rewardsSummary?.pending_amount ?? 0).toFixed(4)} NWU
            </div>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="text-gray-400 text-xs uppercase tracking-wider mb-2">
              Distributed Rewards
            </div>
            <div className="text-2xl font-bold text-green-400">
              {(rewardsSummary?.distributed_amount ?? 0).toFixed(4)} NWU
            </div>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="text-gray-400 text-xs uppercase tracking-wider mb-2">Total Rewards</div>
            <div className="text-2xl font-bold text-white">
              {totalRewards.toFixed(4)} NWU
            </div>
          </div>
        </div>

        {/* Contribution Stats + Reputation */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <div className="text-gray-400 text-xs uppercase tracking-wider mb-2">
              Total Contributions
            </div>
            <div className="text-2xl font-bold">{stats?.total_contributions ?? 0}</div>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <div className="text-gray-400 text-xs uppercase tracking-wider mb-2">Verified</div>
            <div className="text-2xl font-bold text-green-400">
              {stats?.verified_contributions ?? 0}
            </div>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <div className="text-gray-400 text-xs uppercase tracking-wider mb-2">
              Avg Quality Score
            </div>
            <div className="text-2xl font-bold">
              {stats?.average_quality_score?.toFixed(1) ?? '0.0'}
            </div>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <div className="text-gray-400 text-xs uppercase tracking-wider mb-2">
              Reputation Score
            </div>
            <div className="text-2xl font-bold text-blue-400">
              {user?.reputation_score ?? stats?.reputation_score ?? 0}
            </div>
          </div>
        </div>

        {/* Reward History Table */}
        <div className="bg-gray-800 rounded-xl border border-gray-700">
          {/* Tab Bar */}
          <div className="flex border-b border-gray-700">
            {(['all', 'pending', 'distributed'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-4 text-sm font-medium capitalize transition ${
                  activeTab === tab
                    ? 'border-b-2 border-blue-500 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            {filteredRewards.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <p>No {activeTab === 'all' ? '' : activeTab} rewards found.</p>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 text-xs uppercase tracking-wider border-b border-gray-700">
                    <th className="px-6 py-3 text-left">Amount</th>
                    <th className="px-6 py-3 text-left">Status</th>
                    <th className="px-6 py-3 text-left">Chain</th>
                    <th className="px-6 py-3 text-left">Date</th>
                    <th className="px-6 py-3 text-left">Tx Hash</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {filteredRewards.map((reward: Reward) => (
                    <tr key={reward.id} className="hover:bg-gray-750 transition">
                      <td className="px-6 py-4 font-medium">
                        {reward.amount.toFixed(4)} NWU
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            reward.status === 'distributed'
                              ? 'bg-green-900 text-green-300'
                              : reward.status === 'pending'
                                ? 'bg-yellow-900 text-yellow-300'
                                : reward.status === 'processing'
                                  ? 'bg-blue-900 text-blue-300'
                                  : 'bg-red-900 text-red-300'
                          }`}
                        >
                          {reward.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-400 capitalize">
                        {reward.blockchain ?? '—'}
                      </td>
                      <td className="px-6 py-4 text-gray-400">
                        {reward.distributed_at
                          ? new Date(reward.distributed_at).toLocaleDateString()
                          : new Date(reward.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        {reward.tx_hash ? (
                          <a
                            href={getExplorerTxUrl(reward.tx_hash, chainId)}
                            target="_blank"
                            rel="noopener noreferrer"
                            title={`View on ${getExplorerName(chainId)}`}
                            className="font-mono text-blue-400 hover:text-blue-300 transition"
                          >
                            {shortenHash(reward.tx_hash)}
                          </a>
                        ) : (
                          <span className="text-gray-600">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
