import { create } from 'zustand';
import { ethers } from 'ethers';

interface WalletState {
  address: string | null;
  provider: ethers.BrowserProvider | null;
  signer: ethers.Signer | null;
  connected: boolean;
  connecting: boolean;
  error: string | null;
  
  connect: () => Promise<void>;
  disconnect: () => void;
  signMessage: (message: string) => Promise<string>;
}

export const useWallet = create<WalletState>((set, get) => ({
  address: null,
  provider: null,
  signer: null,
  connected: false,
  connecting: false,
  error: null,

  connect: async () => {
    set({ connecting: true, error: null });

    try {
      if (typeof window === 'undefined' || !window.ethereum) {
        throw new Error('MetaMask not installed');
      }

      const provider = new ethers.BrowserProvider(window.ethereum);
      
      // Request account access
      const accounts = await provider.send('eth_requestAccounts', []);
      const address = accounts[0];
      
      // Get signer
      const signer = await provider.getSigner();

      set({
        address,
        provider,
        signer,
        connected: true,
        connecting: false,
        error: null
      });

      // Listen for account changes
      window.ethereum.on('accountsChanged', (accounts: string[]) => {
        if (accounts.length === 0) {
          get().disconnect();
        } else {
          set({ address: accounts[0] });
        }
      });

      // Listen for chain changes
      window.ethereum.on('chainChanged', () => {
        window.location.reload();
      });

    } catch (error: any) {
      set({
        connecting: false,
        error: error.message || 'Failed to connect wallet'
      });
      throw error;
    }
  },

  disconnect: () => {
    set({
      address: null,
      provider: null,
      signer: null,
      connected: false,
      connecting: false,
      error: null
    });
  },

  signMessage: async (message: string) => {
    const { signer } = get();
    if (!signer) {
      throw new Error('Wallet not connected');
    }
    return await signer.signMessage(message);
  }
}));

// Type declaration for window.ethereum
declare global {
  interface Window {
    ethereum?: any;
  }
}
