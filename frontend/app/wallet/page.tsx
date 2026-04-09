'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useWallet } from '@/hooks/useWallet';
import { authService } from '@/lib/auth';
import { api, User, UserStats, UserRewards, Reward } from '@/lib/api';

type Tab = 'all' | 'pending' | 'distributed';

function getExplorerBaseUrl(chainId: number | null): string {
  switch (chainId) {
    case 1:
      return 'https://etherscan.io';
    case 5:
      return 'https://goerli.etherscan.io';
    case 11155111:
      return 'https://sepolia.etherscan.io';
    case 137:
      return 'https://polygonscan.com';
    case 80001:
      return 'https://mumbai.polygonscan.com';
    case 42161:
      return 'https://arbiscan.io';
    case 421613:
      return 'https://goerli.arbiscan.io';
    case 10:
      return 'https://optimistic.etherscan.io';
    default:
      return 'https://etherscan.io';
  }
}

function shortenAddress(address: string): string {
  if (address.length < 10) return address;
  return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
}

function formatEth(balance: string | null): string {
  if (!balance) return '0.0000';
  const num = parseFloat(balance);
  if (isNaN(num)) return '0.0000';
  return num.toFixed(4);
}

export default function WalletPage() {
  const router = useRouter();
  const { address, connected, chainId, networkName, ethBalance, disconnect, refreshBalance } =
    useWallet();

  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [rewards, setRewards] = useState<UserRewards | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>('all');
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState<string | null>(null);
  const [balanceRefreshing, setBalanceRefreshing] = useState(false);

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
        setRewards(userRewards);
      } catch (error) {
        console.error('Failed to load wallet data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [address, connected, router]);

  const handleRefreshBalance = useCallback(async () => {
    setBalanceRefreshing(true);
    await refreshBalance();
    setBalanceRefreshing(false);
  }, [refreshBalance]);

  const handleCopy = useCallback(async () => {
    if (!address) return;
    setCopyError(null);
    try {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopyError('Copy failed — please copy manually');
      setTimeout(() => setCopyError(null), 3000);
    }
  }, [address]);

  const handleDisconnect = useCallback(async () => {
    if (address) {
      await authService.logout(address);
      authService.clearAuthToken();
    }
    disconnect();
    router.push('/');
  }, [address, disconnect, router]);

  const filteredRewards: Reward[] = (rewards?.rewards ?? []).filter(r => {
    if (tab === 'pending') return r.status === 'pending';
    if (tab === 'distributed') return r.status === 'distributed';
    return true;
  });

  const explorerBase = getExplorerBaseUrl(chainId);

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

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-3xl font-bold">Wallet</h1>
            <p className="text-gray-400 mt-1">Your NWU Protocol account</p>
          </div>
          <button
            onClick={handleDisconnect}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition text-sm font-medium"
          >
            Disconnect
          </button>
        </div>

        {/* Address Card */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">Address</p>
              <p className="font-mono text-lg break-all">{address}</p>
              {copyError && <p className="text-red-400 text-xs mt-1">{copyError}</p>}
            </div>
            <button
              onClick={handleCopy}
              className="shrink-0 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition text-sm font-medium"
              title="Copy address"
            >
              {copied ? '✓ Copied' : 'Copy'}
            </button>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-700 flex flex-wrap gap-4 text-sm">
            <div>
              <span className="text-gray-400">Network: </span>
              <span className="text-green-400 font-medium">{networkName ?? 'Unknown'}</span>
            </div>
            <div>
              <span className="text-gray-400">Chain ID: </span>
              <span className="font-medium">{chainId ?? '—'}</span>
            </div>
          </div>
        </div>

        {/* Balance & Rewards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* ETH Balance */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <div className="flex justify-between items-start">
              <p className="text-gray-400 text-xs uppercase tracking-wider">ETH Balance</p>
              <button
                onClick={handleRefreshBalance}
                disabled={balanceRefreshing}
                className="text-gray-500 hover:text-white transition disabled:opacity-50 text-xs"
                title="Refresh balance"
              >
                {balanceRefreshing ? '…' : '↻'}
              </button>
            </div>
            <p className="text-2xl font-bold mt-2">{formatEth(ethBalance)} ETH</p>
          </div>

          {/* Pending NWU */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <p className="text-gray-400 text-xs uppercase tracking-wider">Pending NWU</p>
            <p className="text-2xl font-bold mt-2 text-yellow-400">
              {(rewards?.pending_amount ?? 0).toFixed(2)} NWU
            </p>
          </div>

          {/* Total NWU */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <p className="text-gray-400 text-xs uppercase tracking-wider">Total NWU</p>
            <p className="text-2xl font-bold mt-2 text-green-400">
              {(user?.total_rewards ?? rewards?.total_amount ?? 0).toFixed(2)} NWU
            </p>
          </div>

          {/* Reputation Score */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <p className="text-gray-400 text-xs uppercase tracking-wider">Reputation</p>
            <p className="text-2xl font-bold mt-2 text-blue-400">{user?.reputation_score ?? 0}</p>
          </div>
        </div>

        {/* Contribution Stats */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Contribution Stats</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-gray-400 text-xs uppercase tracking-wider">Total</p>
              <p className="text-xl font-bold mt-1">{stats?.total_contributions ?? 0}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs uppercase tracking-wider">Verified</p>
              <p className="text-xl font-bold mt-1 text-green-400">
                {stats?.verified_contributions ?? 0}
              </p>
            </div>
            <div>
              <p className="text-gray-400 text-xs uppercase tracking-wider">Pending</p>
              <p className="text-xl font-bold mt-1 text-yellow-400">
                {stats?.pending_contributions ?? 0}
              </p>
            </div>
            <div>
              <p className="text-gray-400 text-xs uppercase tracking-wider">Avg. Score</p>
              <p className="text-xl font-bold mt-1">
                {(stats?.average_quality_score ?? 0).toFixed(1)}
              </p>
            </div>
          </div>
        </div>

        {/* Reward History */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <h2 className="text-lg font-semibold mb-4">Reward History</h2>

          {/* Tabs */}
          <div className="flex gap-1 mb-4 bg-gray-900 rounded-lg p-1 w-fit">
            {(['all', 'pending', 'distributed'] as Tab[]).map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition capitalize ${
                  tab === t ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {filteredRewards.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No {tab === 'all' ? '' : tab} rewards found.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 text-xs uppercase tracking-wider border-b border-gray-700">
                    <th className="pb-3 text-left">Date</th>
                    <th className="pb-3 text-right">Amount</th>
                    <th className="pb-3 text-center">Status</th>
                    <th className="pb-3 text-right">Transaction</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {filteredRewards.map(reward => (
                    <tr key={reward.id} className="hover:bg-gray-700/50 transition">
                      <td className="py-3 text-gray-300">
                        {new Date(reward.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 text-right font-mono font-medium">
                        {reward.amount.toFixed(2)} NWU
                      </td>
                      <td className="py-3 text-center">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                            reward.status === 'distributed'
                              ? 'bg-green-900 text-green-300'
                              : 'bg-yellow-900 text-yellow-300'
                          }`}
                        >
                          {reward.status}
                        </span>
                      </td>
                      <td className="py-3 text-right">
                        {reward.tx_hash ? (
                          <a
                            href={`${explorerBase}/tx/${reward.tx_hash}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-400 hover:text-blue-300 font-mono text-xs transition"
                            title={reward.tx_hash}
                          >
                            {shortenAddress(reward.tx_hash)} ↗
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
    </div>
  );
}
