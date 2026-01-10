'use client';

import { useWallet } from '@/hooks/useWallet';
import { authService } from '@/lib/auth';
import { useState } from 'react';

export default function WalletConnect() {
  const { address, connected, connecting, connect, disconnect, signMessage } = useWallet();
  const [authenticating, setAuthenticating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConnect = async () => {
    try {
      setError(null);
      
      // Connect wallet
      await connect();
      
      // Get the connected address
      const walletAddress = useWallet.getState().address;
      if (!walletAddress) {
        throw new Error('Failed to get wallet address');
      }

      setAuthenticating(true);

      // Get nonce from backend
      const { nonce, message } = await authService.connect(walletAddress);

      // Sign message
      const signature = await signMessage(message);

      // Verify signature and get JWT token
      const authResponse = await authService.verify(walletAddress, signature, nonce);

      // Store token
      authService.setAuthToken(authResponse.access_token);

      setAuthenticating(false);
    } catch (err: any) {
      setError(err.message || 'Failed to connect wallet');
      setAuthenticating(false);
    }
  };

  const handleDisconnect = async () => {
    if (address) {
      await authService.logout(address);
      authService.clearAuthToken();
    }
    disconnect();
  };

  if (connected && address) {
    return (
      <div className="flex items-center gap-4">
        <div className="bg-gray-800 px-4 py-2 rounded-lg border border-gray-700">
          <span className="text-sm text-gray-400">Connected:</span>
          <span className="ml-2 font-mono">
            {address.substring(0, 6)}...{address.substring(38)}
          </span>
        </div>
        <button
          onClick={handleDisconnect}
          className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition"
        >
          Disconnect
        </button>
      </div>
    );
  }

  return (
    <div>
      <button
        onClick={handleConnect}
        disabled={connecting || authenticating}
        className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {connecting ? 'Connecting...' : authenticating ? 'Authenticating...' : 'Connect Wallet'}
      </button>
      {error && (
        <p className="mt-2 text-sm text-red-400">{error}</p>
      )}
    </div>
  );
}
