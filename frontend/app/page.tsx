'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useWallet } from '@/hooks/useWallet';
import { authService } from '@/lib/auth';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  const { address, connected, connecting, connect, error: walletError } = useWallet();
  const [apiStatus, setApiStatus] = useState<any>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [signingIn, setSigningIn] = useState(false);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`)
      .then(res => res.json())
      .then(data => { setApiStatus(data); setStatusLoading(false); })
      .catch(() => setStatusLoading(false));
  }, []);

  const handleConnect = async () => {
    setSigningIn(true);
    try {
      await connect();
      const { address: addr } = useWallet.getState();
      if (!addr) return;

      const { nonce, message } = await authService.connect(addr);
      const { signer } = useWallet.getState();
      if (!signer) return;
      const signature = await signer.signMessage(message);
      const { access_token } = await authService.verify(addr, signature, nonce);
      authService.setAuthToken(access_token);
      router.push('/dashboard');
    } catch {
      // wallet error is shown via walletError state
    } finally {
      setSigningIn(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      {/* Header */}
      <header className="border-b border-gray-700 sticky top-0 z-50 bg-gray-900/90 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-green-400 text-transparent bg-clip-text">
              NWU Protocol
            </h1>
            <nav className="hidden md:flex items-center gap-6 text-sm">
              <Link href="/contributions" className="text-gray-300 hover:text-white transition">Explore</Link>
              <Link href="/pricing" className="text-gray-300 hover:text-white transition">Pricing</Link>
              <Link href="/docs" className="text-gray-300 hover:text-white transition">Docs</Link>
            </nav>
            <div className="flex items-center gap-3">
              {connected ? (
                <Link
                  href="/dashboard"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-semibold transition"
                >
                  Dashboard
                </Link>
              ) : (
                <button
                  onClick={handleConnect}
                  disabled={connecting || signingIn}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 rounded-lg text-sm font-semibold transition"
                >
                  {connecting || signingIn ? 'Connecting…' : 'Connect Wallet'}
                </button>
              )}
            </div>
          </div>
          {walletError && (
            <p className="text-red-400 text-xs mt-1 text-right">{walletError}</p>
          )}
        </div>
      </header>

      {/* Hero */}
      <div className="max-w-7xl mx-auto px-4 pt-24 pb-16 sm:px-6 lg:px-8 text-center">
        <div className="inline-block mb-4 px-3 py-1 bg-blue-900/40 border border-blue-500/30 rounded-full text-blue-300 text-sm">
          Decentralized AI Verification Protocol
        </div>
        <h2 className="text-5xl sm:text-6xl font-bold mb-6 leading-tight">
          Verified Truth,<br />
          <span className="bg-gradient-to-r from-blue-400 to-green-400 text-transparent bg-clip-text">
            On-Chain
          </span>
        </h2>
        <p className="text-xl text-gray-300 mb-10 max-w-3xl mx-auto">
          AI agents verify the quality of code, datasets, and documents. Contribute to earn NWU tokens. Build on our API to access verified intelligence at scale.
        </p>
        <div className="flex flex-wrap gap-4 justify-center">
          <button
            onClick={handleConnect}
            disabled={connected || connecting || signingIn}
            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 rounded-lg font-semibold transition text-lg"
          >
            {connected ? 'Connected' : connecting || signingIn ? 'Connecting…' : 'Get Started Free'}
          </button>
          <Link
            href="/pricing"
            className="px-8 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-semibold transition text-lg"
          >
            View Pricing
          </Link>
        </div>
      </div>

      {/* Pricing Teaser */}
      <div className="max-w-7xl mx-auto px-4 py-16 sm:px-6 lg:px-8">
        <h3 className="text-3xl font-bold text-center mb-4">Simple, Transparent Pricing</h3>
        <p className="text-gray-400 text-center mb-12">Start free. Scale when you're ready.</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              name: 'Free',
              price: '$0',
              sub: 'forever',
              features: ['100 API requests/day', 'Basic verification', 'Community support'],
              cta: 'Get Started',
              href: '#connect',
              highlight: false,
            },
            {
              name: 'Pro',
              price: '$99',
              sub: '/month',
              features: ['10,000 API requests/day', 'Advanced verification', 'Priority support', 'Analytics dashboard'],
              cta: 'Start Pro',
              href: '/pricing',
              highlight: true,
            },
            {
              name: 'Enterprise',
              price: '$999',
              sub: '/month',
              features: ['100,000 API requests/day', 'Premium verification', '24/7 dedicated support', 'SLA guarantee'],
              cta: 'Start Enterprise',
              href: '/pricing',
              highlight: false,
            },
          ].map(tier => (
            <div
              key={tier.name}
              className={`rounded-2xl p-8 border flex flex-col ${
                tier.highlight
                  ? 'border-blue-500 bg-blue-950/30 shadow-lg shadow-blue-500/10 relative'
                  : 'border-gray-700 bg-gray-800'
              }`}
            >
              {tier.highlight && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-xs font-semibold px-4 py-1 rounded-full">
                  Most Popular
                </span>
              )}
              <div className="mb-6">
                <p className="text-gray-400 text-sm mb-1">{tier.name}</p>
                <div className="flex items-end gap-1">
                  <span className="text-4xl font-bold">{tier.price}</span>
                  <span className="text-gray-400 mb-1">{tier.sub}</span>
                </div>
              </div>
              <ul className="space-y-2 mb-8 flex-1">
                {tier.features.map(f => (
                  <li key={f} className="flex items-start gap-2 text-gray-300 text-sm">
                    <span className="text-green-400 mt-0.5">✓</span>
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href={tier.href}
                className={`block text-center py-2.5 rounded-lg font-semibold text-sm transition ${
                  tier.highlight
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-gray-700 hover:bg-gray-600 text-white'
                }`}
              >
                {tier.cta}
              </Link>
            </div>
          ))}
        </div>
        <p className="text-center mt-8">
          <Link href="/pricing" className="text-blue-400 hover:text-blue-300 text-sm transition">
            See full feature comparison →
          </Link>
        </p>
      </div>

      {/* Features */}
      <div className="max-w-7xl mx-auto px-4 py-16 sm:px-6 lg:px-8">
        <h3 className="text-3xl font-bold text-center mb-12">How It Works</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { step: '1', title: 'Upload', desc: 'Submit code, datasets, or documents' },
            { step: '2', title: 'Verify', desc: 'AI agents analyze and score quality' },
            { step: '3', title: 'Store', desc: 'Results recorded on-chain via IPFS' },
            { step: '4', title: 'Earn', desc: 'Receive NWU tokens based on quality' },
          ].map(({ step, title, desc }) => (
            <div key={step} className="text-center">
              <div className="w-14 h-14 bg-blue-600 rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-3">
                {step}
              </div>
              <h4 className="font-semibold mb-1">{title}</h4>
              <p className="text-sm text-gray-400">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* System Status */}
      <div className="max-w-lg mx-auto px-4 pb-16">
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <h3 className="text-lg font-semibold mb-4 text-center">System Status</h3>
          {statusLoading ? (
            <div className="text-center text-gray-400 text-sm">Checking…</div>
          ) : apiStatus ? (
            <div>
              <div className="flex justify-between items-center mb-3">
                <span className="text-gray-300 text-sm">Overall</span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${apiStatus.status === 'healthy' ? 'bg-green-700 text-green-200' : 'bg-yellow-700 text-yellow-200'}`}>
                  {apiStatus.status}
                </span>
              </div>
              {apiStatus.checks && Object.entries(apiStatus.checks).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center py-1">
                  <span className="text-gray-400 text-sm capitalize">{key}</span>
                  <span className={`w-2.5 h-2.5 rounded-full ${value ? 'bg-green-500' : 'bg-red-500'}`} />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-red-400 text-sm">API unavailable</div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-gray-400">
            <p>&copy; 2026 NWU Protocol</p>
            <div className="flex gap-6">
              <Link href="/pricing" className="hover:text-white transition">Pricing</Link>
              <Link href="/docs" className="hover:text-white transition">Docs</Link>
              <a href="https://github.com/Garrettc123/nwu-protocol" target="_blank" className="hover:text-white transition">GitHub</a>
              <a href="mailto:support@nwuprotocol.com" className="hover:text-white transition">Support</a>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
