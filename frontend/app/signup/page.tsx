'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useWallet } from '@/hooks/useWallet';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export default function SignupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const refCode = searchParams.get('ref');

  const { address, connected, connect } = useWallet();
  const [status, setStatus] = useState<'idle' | 'connecting' | 'applying' | 'done' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const applied = useRef(false);

  const applyReferral = async () => {
    if (!refCode || applied.current) return;
    applied.current = true;
    setStatus('applying');
    try {
      await axios.post(
        `${API_URL}/api/v1/referrals/apply`,
        { referral_code: refCode },
        { headers: getAuthHeaders() }
      );
      setStatus('done');
      setMessage(`Referral code "${refCode}" applied! Your referrer earned 50 NWU.`);
    } catch (err: any) {
      const detail = err.response?.data?.detail ?? '';
      if (detail.toLowerCase().includes('already') || err.response?.status === 409) {
        setStatus('done');
        setMessage('Referral already applied to this account.');
      } else {
        setStatus('error');
        setMessage(detail || 'Failed to apply referral code. You can still use the app normally.');
      }
    }
    setTimeout(() => router.push('/dashboard'), 2500);
  };

  useEffect(() => {
    if (connected && address && status === 'connecting') {
      applyReferral();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connected, address]);

  const handleConnect = async () => {
    if (connected) {
      await applyReferral();
      return;
    }
    setStatus('connecting');
    try {
      await connect();
    } catch {
      setStatus('error');
      setMessage('Wallet connection failed. Please try again.');
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-gray-800 rounded-2xl border border-gray-700 p-8 text-center">
        <h1 className="text-3xl font-bold mb-2">Join NWU Protocol</h1>

        {refCode ? (
          <p className="text-gray-400 mb-6">
            You were invited with referral code{' '}
            <span className="font-mono text-blue-400">{refCode}</span>. Connect your wallet to
            claim your spot and credit your referrer.
          </p>
        ) : (
          <p className="text-gray-400 mb-6">
            Connect your wallet to get started with NWU Protocol.
          </p>
        )}

        {status === 'done' && (
          <div className="mb-6 bg-green-900/40 border border-green-600 rounded-lg px-4 py-3 text-green-300 text-sm">
            {message} Redirecting to dashboard…
          </div>
        )}

        {status === 'error' && (
          <div className="mb-6 bg-red-900/40 border border-red-600 rounded-lg px-4 py-3 text-red-300 text-sm">
            {message}
          </div>
        )}

        {status !== 'done' && (
          <button
            onClick={handleConnect}
            disabled={status === 'connecting' || status === 'applying'}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed rounded-lg font-semibold transition"
          >
            {status === 'connecting'
              ? 'Connecting…'
              : status === 'applying'
              ? 'Applying referral…'
              : 'Connect Wallet'}
          </button>
        )}

        <p className="mt-6 text-xs text-gray-500">
          By connecting, you agree to use the protocol in accordance with its terms.
        </p>
      </div>
    </main>
  );
}
