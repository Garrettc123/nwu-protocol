'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useWallet } from '@/hooks/useWallet';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
};

interface ReferralStats {
  address: string;
  total_referrals: number;
  total_conversions: number;
  total_nwu_earned: number;
  pending_rewards: number;
  is_affiliate: boolean;
  revenue_share_percent: number;
}

interface ReferralCode {
  referral_code: string;
  referral_url: string;
  is_affiliate: boolean;
}

export default function ReferralsPage() {
  const router = useRouter();
  const { address, connected } = useWallet();

  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [code, setCode] = useState<ReferralCode | null>(null);
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState(false);
  const [claimResult, setClaimResult] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const appUrl =
    (typeof window !== 'undefined' ? process.env.NEXT_PUBLIC_APP_URL : null) ||
    (typeof window !== 'undefined' ? window.location.origin : '');

  useEffect(() => {
    if (!connected || !address) {
      router.push('/');
      return;
    }

    const load = async () => {
      try {
        setLoading(true);
        const headers = getAuthHeaders();
        const [statsRes, codeRes] = await Promise.all([
          axios.get(`${API_URL}/api/v1/referrals/stats`, { headers }).catch(() => null),
          axios.post(`${API_URL}/api/v1/referrals/generate`, null, { headers }).catch(() => null),
        ]);
        if (statsRes) setStats(statsRes.data);
        if (codeRes) setCode(codeRes.data);
      } catch {
        // handled per-request above
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [address, connected, router]);

  const shareUrl = code ? `${appUrl}${code.referral_url}` : '';

  const handleCopy = useCallback(async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback: select the input
    }
  }, [shareUrl]);

  const handleClaim = useCallback(async () => {
    setClaiming(true);
    setClaimResult(null);
    try {
      const res = await axios.post(
        `${API_URL}/api/v1/referrals/claim`,
        null,
        { headers: getAuthHeaders() }
      );
      const { nwu_claimed } = res.data;
      setClaimResult(
        nwu_claimed > 0
          ? `Claimed ${nwu_claimed.toFixed(2)} NWU successfully!`
          : 'No pending rewards to claim right now.'
      );
      // Refresh stats
      const statsRes = await axios.get(`${API_URL}/api/v1/referrals/stats`, {
        headers: getAuthHeaders(),
      });
      setStats(statsRes.data);
    } catch {
      setClaimResult('Claim failed. Please try again.');
    } finally {
      setClaiming(false);
    }
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto" />
          <p className="mt-4 text-gray-400">Loading referrals…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-3xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Referrals</h1>
          <p className="text-gray-400 mt-1">
            Share your link. Earn NWU rewards for every user you bring in.
          </p>
        </div>

        {/* Affiliate badge */}
        {stats?.is_affiliate && (
          <div className="mb-6 bg-purple-900/40 border border-purple-500 rounded-lg p-4 flex items-center gap-3">
            <span className="text-2xl">★</span>
            <div>
              <p className="font-semibold text-purple-300">Affiliate Status Active</p>
              <p className="text-sm text-purple-400">
                You earn {stats.revenue_share_percent}% revenue share on every subscription
                from your referrals.
              </p>
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <p className="text-gray-400 text-xs uppercase tracking-wider">Referrals</p>
            <p className="text-2xl font-bold mt-1">{stats?.total_referrals ?? 0}</p>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <p className="text-gray-400 text-xs uppercase tracking-wider">Converted</p>
            <p className="text-2xl font-bold mt-1 text-green-400">
              {stats?.total_conversions ?? 0}
            </p>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <p className="text-gray-400 text-xs uppercase tracking-wider">Pending NWU</p>
            <p className="text-2xl font-bold mt-1 text-yellow-400">
              {(stats?.pending_rewards ?? 0).toFixed(2)}
            </p>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <p className="text-gray-400 text-xs uppercase tracking-wider">Total Earned</p>
            <p className="text-2xl font-bold mt-1 text-blue-400">
              {(stats?.total_nwu_earned ?? 0).toFixed(2)}
            </p>
          </div>
        </div>

        {/* Referral link */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-1">Your Referral Link</h2>
          <p className="text-gray-400 text-sm mb-4">
            Share this link. Every signup earns you 50 NWU.
          </p>
          <div className="flex gap-3">
            <input
              readOnly
              value={shareUrl}
              className="flex-1 bg-gray-900 border border-gray-600 rounded-lg px-4 py-2.5 text-sm font-mono text-gray-300 focus:outline-none"
              onClick={e => (e.target as HTMLInputElement).select()}
            />
            <button
              onClick={handleCopy}
              className="shrink-0 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-semibold transition"
            >
              {copied ? '✓ Copied' : 'Copy'}
            </button>
          </div>
          {code?.referral_code && (
            <p className="text-gray-500 text-xs mt-2">
              Code: <span className="font-mono text-gray-300">{code.referral_code}</span>
            </p>
          )}
        </div>

        {/* Claim rewards */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-1">Claim Rewards</h2>
          <p className="text-gray-400 text-sm mb-4">
            You have{' '}
            <span className="text-yellow-400 font-semibold">
              {(stats?.pending_rewards ?? 0).toFixed(2)} NWU
            </span>{' '}
            pending. Claim to add them to your balance.
          </p>
          {claimResult && (
            <div
              className={`mb-4 px-4 py-2 rounded-lg text-sm ${
                claimResult.includes('success') || claimResult.includes('Claimed')
                  ? 'bg-green-900/40 border border-green-500 text-green-300'
                  : 'bg-yellow-900/40 border border-yellow-500 text-yellow-300'
              }`}
            >
              {claimResult}
            </div>
          )}
          <button
            onClick={handleClaim}
            disabled={claiming || (stats?.pending_rewards ?? 0) === 0}
            className="px-6 py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-semibold transition"
          >
            {claiming ? 'Claiming…' : 'Claim NWU Rewards'}
          </button>
        </div>

        {/* How it works */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <h2 className="text-lg font-semibold mb-4">How It Works</h2>
          <div className="space-y-3 text-sm text-gray-300">
            <div className="flex gap-3">
              <span className="text-blue-400 font-bold shrink-0">1.</span>
              <span>Share your referral link with developers or AI researchers.</span>
            </div>
            <div className="flex gap-3">
              <span className="text-blue-400 font-bold shrink-0">2.</span>
              <span>
                When they sign up using your link, you earn{' '}
                <span className="text-yellow-400 font-semibold">50 NWU</span> per conversion.
              </span>
            </div>
            <div className="flex gap-3">
              <span className="text-blue-400 font-bold shrink-0">3.</span>
              <span>
                Reach <span className="text-purple-400 font-semibold">10 conversions</span> to
                unlock Affiliate status and earn a revenue share on subscriptions.
              </span>
            </div>
            <div className="flex gap-3">
              <span className="text-blue-400 font-bold shrink-0">4.</span>
              <span>Claim your pending NWU rewards at any time above.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
