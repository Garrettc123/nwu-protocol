'use client';

import { useEffect, useState } from 'react';
import { useWallet } from '@/hooks/useWallet';
import { useRouter } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

interface ReferralStats {
  address: string;
  total_referrals: number;
  total_conversions: number;
  total_nwu_earned: number;
  pending_rewards: number;
  is_affiliate: boolean;
  revenue_share_percent: number;
}

interface GenerateCodeResponse {
  referral_code: string;
  referral_url: string;
  is_affiliate: boolean;
}

async function apiFetch<T>(path: string, token: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(options?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export default function WalletPage() {
  const { address, connected } = useWallet();
  const router = useRouter();

  const [token, setToken] = useState<string | null>(null);
  const [referralStats, setReferralStats] = useState<ReferralStats | null>(null);
  const [referralCode, setReferralCode] = useState<string | null>(null);
  const [claimMessage, setClaimMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState(false);
  const [generatingCode, setGeneratingCode] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!connected || !address) {
      router.push('/');
      return;
    }
    // Retrieve JWT from localStorage (set during wallet auth flow)
    const storedToken = localStorage.getItem('nwu_token');
    setToken(storedToken);
  }, [address, connected, router]);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    const loadStats = async () => {
      try {
        setLoading(true);
        const stats = await apiFetch<ReferralStats>('/api/v1/referrals/stats', token);
        setReferralStats(stats);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load referral stats');
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, [token]);

  const handleGenerateCode = async () => {
    if (!token) return;
    setGeneratingCode(true);
    setError(null);
    try {
      const data = await apiFetch<GenerateCodeResponse>('/api/v1/referrals/generate', token, {
        method: 'POST',
      });
      setReferralCode(data.referral_code);
      // Refresh stats
      const stats = await apiFetch<ReferralStats>('/api/v1/referrals/stats', token);
      setReferralStats(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate referral code');
    } finally {
      setGeneratingCode(false);
    }
  };

  const handleClaim = async () => {
    if (!token) return;
    setClaiming(true);
    setClaimMessage(null);
    setError(null);
    try {
      const result = await apiFetch<{ message: string; nwu_claimed: number; total_nwu_claimed: number }>(
        '/api/v1/referrals/claim',
        token,
        { method: 'POST' },
      );
      setClaimMessage(`${result.message} (+${result.nwu_claimed.toFixed(2)} NWU)`);
      // Refresh stats
      const stats = await apiFetch<ReferralStats>('/api/v1/referrals/stats', token);
      setReferralStats(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to claim rewards');
    } finally {
      setClaiming(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(
      () => {
        setCopyFeedback('Copied!');
        setTimeout(() => setCopyFeedback(null), 2000);
      },
      () => {
        setCopyFeedback('Copy failed — please copy manually.');
        setTimeout(() => setCopyFeedback(null), 3000);
      },
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto" />
          <p className="mt-4 text-gray-400">Loading wallet...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Wallet</h1>
          <p className="text-gray-400 mt-2">
            {address ? `${address.substring(0, 6)}...${address.substring(38)}` : 'Not connected'}
          </p>
        </div>

        {error && (
          <div className="mb-6 bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-300">
            {error}
          </div>
        )}

        {claimMessage && (
          <div className="mb-6 bg-green-900/50 border border-green-700 rounded-lg p-4 text-green-300">
            {claimMessage}
          </div>
        )}

        {!token ? (
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <p className="text-gray-400">Please sign in with your wallet to view referral stats.</p>
          </div>
        ) : (
          <>
            {/* NWU Rewards overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <div className="text-gray-400 text-sm mb-2">Pending NWU Rewards</div>
                <div className="text-3xl font-bold text-yellow-400">
                  {referralStats?.pending_rewards?.toFixed(2) ?? '0.00'}
                </div>
                <div className="text-gray-500 text-xs mt-1">NWU tokens</div>
              </div>

              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <div className="text-gray-400 text-sm mb-2">Total NWU Earned</div>
                <div className="text-3xl font-bold text-green-400">
                  {referralStats?.total_nwu_earned?.toFixed(2) ?? '0.00'}
                </div>
                <div className="text-gray-500 text-xs mt-1">from referrals</div>
              </div>

              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <div className="text-gray-400 text-sm mb-2">Affiliate Status</div>
                <div className={`text-2xl font-bold ${referralStats?.is_affiliate ? 'text-purple-400' : 'text-gray-400'}`}>
                  {referralStats?.is_affiliate ? '⭐ Affiliate' : 'Standard'}
                </div>
                <div className="text-gray-500 text-xs mt-1">
                  {referralStats?.revenue_share_percent ?? 5}% revenue share
                </div>
              </div>
            </div>

            {/* Referral Stats */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
              <h2 className="text-xl font-bold mb-4">Referral Programme</h2>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <div className="text-gray-400 text-sm">Total Referrals</div>
                  <div className="text-2xl font-bold">{referralStats?.total_referrals ?? 0}</div>
                </div>
                <div>
                  <div className="text-gray-400 text-sm">Conversions</div>
                  <div className="text-2xl font-bold text-green-400">
                    {referralStats?.total_conversions ?? 0}
                  </div>
                </div>
              </div>

              {!referralStats?.is_affiliate && (
                <div className="mb-6 bg-purple-900/30 border border-purple-700/50 rounded-lg p-4">
                  <p className="text-purple-300 text-sm">
                    🚀 Reach{' '}
                    <strong>10 conversions</strong> to unlock{' '}
                    <strong>Affiliate</strong> status and earn{' '}
                    <strong>10% revenue share</strong> on referrals!
                  </p>
                </div>
              )}

              {/* Generate referral code */}
              <div className="mb-4">
                <button
                  onClick={handleGenerateCode}
                  disabled={generatingCode}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 rounded-lg transition mr-3"
                >
                  {generatingCode ? 'Generating...' : 'Get Referral Code'}
                </button>
              </div>

              {referralCode && (
                <div className="flex items-center gap-3 bg-gray-900 rounded-lg p-4 border border-gray-600">
                  <code className="flex-1 text-green-400 font-mono text-lg">{referralCode}</code>
                  <button
                    onClick={() => copyToClipboard(`${window.location.origin}/signup?ref=${referralCode}`)}
                    className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm transition"
                  >
                    Copy Link
                  </button>
                </div>
              )}
              {copyFeedback && (
                <p className="text-sm mt-2 text-gray-400">{copyFeedback}</p>
              )}
            </div>

            {/* Claim rewards */}
            {(referralStats?.pending_rewards ?? 0) > 0 && (
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                <h2 className="text-xl font-bold mb-2">Claim Rewards</h2>
                <p className="text-gray-400 mb-4">
                  You have{' '}
                  <span className="text-yellow-400 font-semibold">
                    {referralStats?.pending_rewards?.toFixed(2)} NWU
                  </span>{' '}
                  pending. Claim them now!
                </p>
                <button
                  onClick={handleClaim}
                  disabled={claiming}
                  className="px-6 py-3 bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-800 rounded-lg font-semibold transition"
                >
                  {claiming ? 'Claiming...' : `Claim ${referralStats?.pending_rewards?.toFixed(2)} NWU`}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
