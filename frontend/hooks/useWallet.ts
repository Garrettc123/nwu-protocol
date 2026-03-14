import { create } from 'zustand';
import { ethers } from 'ethers';

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

// Track whether MetaMask event listeners have been registered to avoid duplicates.
// We use a WeakRef-style approach: track the ethereum provider object we registered on.
let registeredOnProvider: any = null;

function resolveNetworkName(chainId: number, fallback: string): string {
  const known: Record<number, string> = {
    1: 'Ethereum Mainnet',
    5: 'Goerli Testnet',
    11155111: 'Sepolia Testnet',
    137: 'Polygon Mainnet',
    80001: 'Mumbai Testnet',
    42161: 'Arbitrum One',
    421613: 'Arbitrum Goerli',
    10: 'Optimism',
    420: 'Optimism Goerli',
    56: 'BNB Smart Chain',
    31337: 'Hardhat Local',
    1337: 'Localhost',
  };
  return known[chainId] ?? fallback ?? `Chain ${chainId}`;
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

      // Get signer and network info in parallel
      const [signer, network] = await Promise.all([
        provider.getSigner(),
        provider.getNetwork(),
      ]);

      const chainId = Number(network.chainId);
      const networkName = resolveNetworkName(chainId, network.name);

      // Get ETH balance
      const balanceBigInt = await provider.getBalance(address);
      const ethBalance = ethers.formatEther(balanceBigInt);

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

      // Register MetaMask event listeners only once per provider to prevent duplicates
      if (registeredOnProvider !== window.ethereum) {
        registeredOnProvider = window.ethereum;

        window.ethereum.on('accountsChanged', (accounts: string[]) => {
          if (accounts.length === 0) {
            get().disconnect();
          } else {
            set({ address: accounts[0] });
            get().refreshBalance();
          }
        });

        window.ethereum.on('chainChanged', () => {
          window.location.reload();
        });
      }
    } catch (error: any) {
      set({
        connecting: false,
        error: error.message || 'Failed to connect wallet',
      });
      throw error;
    }
  },

  disconnect: () => {
    registeredOnProvider = null;
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
      const balanceBigInt = await provider.getBalance(address);
      set({ ethBalance: ethers.formatEther(balanceBigInt) });
    } catch {
      // silently ignore balance refresh errors
    }
  },
}));

// Type declaration for window.ethereum
declare global {
  interface Window {
    ethereum?: any;
  }
}
