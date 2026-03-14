import { create } from 'zustand';
import { ethers } from 'ethers';

const CHAIN_NAMES: Record<number, string> = {
  1: 'Ethereum Mainnet',
  5: 'Goerli Testnet',
  11155111: 'Sepolia Testnet',
  137: 'Polygon Mainnet',
  80001: 'Polygon Mumbai',
  42161: 'Arbitrum One',
  421613: 'Arbitrum Goerli',
};

interface WalletState {
  address: string | null;
  provider: ethers.BrowserProvider | null;
  signer: ethers.Signer | null;
  connected: boolean;
  connecting: boolean;
  error: string | null;
  chainId: number | null;
  networkName: string | null;
  ethBalance: string | null;

  connect: () => Promise<void>;
  disconnect: () => void;
  signMessage: (message: string) => Promise<string>;
  refreshBalance: () => Promise<void>;
}

export const useWallet = create<WalletState>((set, get) => ({
  address: null,
  provider: null,
  signer: null,
  connected: false,
  connecting: false,
  error: null,
  chainId: null,
  networkName: null,
  ethBalance: null,

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

      // Get signer and network info
      const [signer, network, balanceWei] = await Promise.all([
        provider.getSigner(),
        provider.getNetwork(),
        provider.getBalance(address),
      ]);

      const chainId = Number(network.chainId);
      const networkName = CHAIN_NAMES[chainId] ?? `Chain ${chainId}`;
      const ethBalance = ethers.formatEther(balanceWei);

      set({
        address,
        provider,
        signer,
        connected: true,
        connecting: false,
        error: null,
        chainId,
        networkName,
        ethBalance,
      });

      // Remove any previously registered listeners before adding new ones
      window.ethereum.removeAllListeners('accountsChanged');
      window.ethereum.removeAllListeners('chainChanged');

      // Listen for account changes
      window.ethereum.on('accountsChanged', (changedAccounts: string[]) => {
        if (changedAccounts.length === 0) {
          get().disconnect();
        } else {
          set({ address: changedAccounts[0] });
          get().refreshBalance();
        }
      });

      // Listen for chain changes
      window.ethereum.on('chainChanged', () => {
        window.location.reload();
      });
    } catch (error: unknown) {
      set({
        connecting: false,
        error: error instanceof Error ? error.message : 'Failed to connect wallet',
      });
      throw error;
    }
  },

  disconnect: () => {
    if (typeof window !== 'undefined' && window.ethereum) {
      window.ethereum.removeAllListeners('accountsChanged');
      window.ethereum.removeAllListeners('chainChanged');
    }
    set({
      address: null,
      provider: null,
      signer: null,
      connected: false,
      connecting: false,
      error: null,
      chainId: null,
      networkName: null,
      ethBalance: null,
    });
  },

  signMessage: async (message: string) => {
    const { signer } = get();
    if (!signer) {
      throw new Error('Wallet not connected');
    }
    return await signer.signMessage(message);
  },

  refreshBalance: async () => {
    const { provider, address } = get();
    if (!provider || !address) return;
    try {
      const balanceWei = await provider.getBalance(address);
      set({ ethBalance: ethers.formatEther(balanceWei) });
    } catch {
      // Silently ignore balance refresh failures
    }
  },
}));

// Type declaration for window.ethereum
declare global {
  interface Window {
    ethereum?: any;
  }
}
