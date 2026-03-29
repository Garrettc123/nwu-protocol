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

function getNetworkName(chainId: number): string {
  const networks: Record<number, string> = {
    1: 'Ethereum Mainnet',
    5: 'Goerli Testnet',
    11155111: 'Sepolia Testnet',
    137: 'Polygon Mainnet',
    80001: 'Mumbai Testnet',
    56: 'BNB Smart Chain',
    43114: 'Avalanche C-Chain',
    42161: 'Arbitrum One',
    10: 'Optimism',
    8453: 'Base',
    31337: 'Localhost',
  };
  return networks[chainId] || `Chain ${chainId}`;
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

      // Get signer
      const signer = await provider.getSigner();

      // Get network info
      const network = await provider.getNetwork();
      const chainId = Number(network.chainId);
      const networkName = getNetworkName(chainId);

      // Get ETH balance
      const balanceWei = await provider.getBalance(address);
      const ethBalance = parseFloat(ethers.formatEther(balanceWei)).toFixed(4);

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
      window.ethereum.on('accountsChanged', (newAccounts: string[]) => {
        if (newAccounts.length === 0) {
          get().disconnect();
        } else {
          set({ address: newAccounts[0] });
          get().refreshBalance();
        }
      });

      // Listen for chain changes
      window.ethereum.on('chainChanged', () => {
        window.location.reload();
      });
    } catch (error: any) {
      set({
        connecting: false,
        error: error.message || 'Failed to connect wallet',
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
      const ethBalance = parseFloat(ethers.formatEther(balanceWei)).toFixed(4);
      const network = await provider.getNetwork();
      const chainId = Number(network.chainId);
      const networkName = getNetworkName(chainId);
      set({ ethBalance, chainId, networkName });
    } catch (error: any) {
      console.error('Failed to refresh wallet balance:', error?.message || error);
    }
  },
}));

// Type declaration for window.ethereum
declare global {
  interface Window {
    ethereum?: any;
  }
}
