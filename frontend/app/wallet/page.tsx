'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useWallet } from '@/hooks/useWallet';
import { authService } from '@/lib/auth';
import { api, UserStats, UserRewards, Reward } from '@/lib/api';

// Block explorer URLs by chain ID
const EXPLORER_TX_URL: Record<number, string> = {
  1: 'https://etherscan.io/tx/',
  5: 'https://goerli.etherscan.io/tx/',
  11155111: 'https://sepolia.etherscan.io/tx/',
  137: 'https://polygonscan.com/tx/',
  80001: 'https://mumbai.polygonscan.com/tx/',
  42161: 'https://arbiscan.io/tx/',
  421613: 'https://goerli.arbiscan.io/tx/',
};

const EXPLORER_NAMES: Record<number, string> = {
  1: 'Etherscan',
  5: 'Etherscan (Goerli)',
  11155111: 'Etherscan (Sepolia)',
  137: 'Polygonscan',
  80001: 'Polygonscan (Mumbai)',
  42161: 'Arbiscan',
  421613: 'Arbiscan (Goerli)',
};

type RewardTab = 'all' | 'pending' | 'distributed';

const STATUS_COLORS: Record<string, string> = {
  pending: 'text-yellow-400',
  processing: 'text-blue-400',
  distributed: 'text-green-400',
  failed: 'text-red-400',
};

function truncateAddress(address: string): string {
  return `${address.substring(0, 6)}...${address.substring(38)}`;
}

function formatBalance(balance: string | null): string {
  if (balance === null) return '—';
  const num = parseFloat(balance);
  return isNaN(num) ? '—' : num.toFixed(6);
}

export default function WalletPage() {
  const router = useRouter();
  const { address, connected, chainId, networkName, ethBalance, disconnect, refreshBalance } =
    useWallet();

  const [stats, setStats] = useState<UserStats | null>(null);
  const [rewards, setRewards] = useState<UserRewards | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<RewardTab>('all');
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!address) return;
    try {
      setLoading(true);
      setLoadError(null);
      const [userStats, userRewards] = await Promise.all([
        api.getUserStats(address).catch(() => null),
        api.getUserRewards(address).catch(() => null),
      ]);
      setStats(userStats);
      setRewards(userRewards);
    } catch (err: unknown) {
      setLoadError(err instanceof Error ? err.message : 'Failed to load wallet data');
    } finally {
      setLoading(false);
    }
  }, [address]);

  useEffect(() => {
    if (!connected || !address) {
      router.push('/');
      return;
    }
    loadData();
    refreshBalance();
  }, [address, connected, router, loadData, refreshBalance]);

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

  const explorerTxBase = chainId ? EXPLORER_TX_URL[chainId] : null;
  const explorerName = chainId ? (EXPLORER_NAMES[chainId] ?? `Explorer`) : null;

  const filteredRewards: Reward[] = rewards?.rewards
    ? rewards.rewards.filter(reward => {
        if (activeTab === 'all') return true;
        if (activeTab === 'pending') return reward.status === 'pending' || reward.status === 'processing';
        if (activeTab === 'distributed') return reward.status === 'distributed';
        return true;
      })
    : [];

  if (!connected) {
    return null; // Redirect handled in useEffect
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-3xl font-bold">Wallet</h1>
            <p className="text-gray-400 mt-1">Manage your NWU Protocol wallet</p>
          </div>
          <button
            onClick={handleDisconnect}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition text-sm font-medium"
          >
            Disconnect
          </button>
        </div>

        {/* Address Card */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="text-gray-400 text-sm mb-1">Wallet Address</div>
              <div className="font-mono text-lg break-all">{address}</div>
            </div>
            <div className="flex flex-col gap-1">
              <button
                onClick={handleCopyAddress}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition text-sm font-medium whitespace-nowrap"
              >
                {copied ? '✓ Copied!' : 'Copy Address'}
              </button>
              {copyError && <p className="text-xs text-red-400 text-center">{copyError}</p>}
            </div>
          </div>
        </div>

        {/* Network + Balance Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-5">
            <div className="text-gray-400 text-sm mb-1">Network</div>
            <div className="font-semibold">{networkName ?? '—'}</div>
            {chainId !== null && (
              <div className="text-gray-500 text-xs mt-1">Chain ID: {chainId}</div>
            )}
          </div>

          <div className="bg-gray-800 rounded-lg border border-gray-700 p-5">
            <div className="text-gray-400 text-sm mb-1">ETH Balance</div>
            <div className="text-2xl font-bold">{formatBalance(ethBalance)} ETH</div>
            <button
              onClick={refreshBalance}
              className="mt-2 text-xs text-blue-400 hover:text-blue-300 transition"
            >
              Refresh
            </button>
          </div>

          <div className="bg-gray-800 rounded-lg border border-gray-700 p-5">
            <div className="text-gray-400 text-sm mb-1">Total NWU Rewards</div>
            <div className="text-2xl font-bold text-yellow-400">
              {rewards?.total_rewards?.toFixed(2) ?? '—'} NWU
            </div>
          </div>
        </div>

        {/* Stats + Pending Rewards Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 className="text-lg font-bold mb-4">Contribution Stats</h2>
            {loading ? (
              <div className="text-gray-500 text-sm">Loading…</div>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Total Contributions</span>
                  <span className="font-semibold">{stats?.total_contributions ?? '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Verified</span>
                  <span className="font-semibold text-green-400">
                    {stats?.verified_contributions ?? '—'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Avg. Quality Score</span>
                  <span className="font-semibold">{stats?.average_quality_score ?? '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Reputation Score</span>
                  <span className="font-semibold text-blue-400">
                    {stats?.reputation_score ?? '—'}
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 className="text-lg font-bold mb-4">NWU Rewards</h2>
            {loading ? (
              <div className="text-gray-500 text-sm">Loading…</div>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Pending</span>
                  <span className="font-semibold text-yellow-400">
                    {rewards?.pending_amount?.toFixed(2) ?? '—'} NWU
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Distributed</span>
                  <span className="font-semibold text-green-400">
                    {rewards?.distributed_amount?.toFixed(2) ?? '—'} NWU
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Total</span>
                  <span className="font-semibold">
                    {rewards?.total_rewards?.toFixed(2) ?? '—'} NWU
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Reward History */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <h2 className="text-lg font-bold">Reward History</h2>
            {/* Tabs */}
            <div className="flex gap-1 bg-gray-900 rounded-lg p-1">
              {(['all', 'pending', 'distributed'] as RewardTab[]).map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition capitalize ${
                    activeTab === tab
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          {loadError && (
            <p className="text-red-400 text-sm mb-4">{loadError}</p>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-10">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : filteredRewards.length === 0 ? (
            <div className="text-center py-10 text-gray-500">
              <p>No rewards found for this filter.</p>
              <Link
                href="/upload"
                className="mt-2 inline-block text-blue-400 hover:text-blue-300 transition text-sm"
              >
                Upload a contribution to earn rewards →
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-400 border-b border-gray-700">
                    <th className="pb-3 pr-4 font-medium">Amount</th>
                    <th className="pb-3 pr-4 font-medium">Status</th>
                    <th className="pb-3 pr-4 font-medium">Network</th>
                    <th className="pb-3 pr-4 font-medium">Transaction</th>
                    <th className="pb-3 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {filteredRewards.map(reward => (
                    <tr key={reward.id} className="hover:bg-gray-750 transition">
                      <td className="py-3 pr-4 font-semibold text-yellow-400">
                        {reward.amount.toFixed(4)} NWU
                      </td>
                      <td className={`py-3 pr-4 capitalize ${STATUS_COLORS[reward.status] ?? 'text-gray-400'}`}>
                        {reward.status}
                      </td>
                      <td className="py-3 pr-4 text-gray-300 capitalize">{reward.blockchain}</td>
                      <td className="py-3 pr-4">
                        {reward.tx_hash ? (
                          explorerTxBase ? (
                            <a
                              href={`${explorerTxBase}${reward.tx_hash}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-400 hover:text-blue-300 transition font-mono text-xs"
                              title={`View on ${explorerName}`}
                            >
                              {truncateAddress(reward.tx_hash)}↗
                            </a>
                          ) : (
                            <span className="font-mono text-xs text-gray-400">
                              {truncateAddress(reward.tx_hash)}
                            </span>
                          )
                        ) : (
                          <span className="text-gray-600">—</span>
                        )}
                      </td>
                      <td className="py-3 text-gray-400">
                        {new Date(reward.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
