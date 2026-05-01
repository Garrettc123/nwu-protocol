import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export interface User {
  id: number;
  address: string;
  reputation_score: number;
  total_contributions: number;
  total_rewards: number;
  created_at: string;
}

export interface Contribution {
  id: number;
  title: string;
  description: string | null;
  file_type: string;
  status: string;
  quality_score: number | null;
}

export interface UserStats {
  total_contributions: number;
  verified_contributions: number;
  pending_contributions: number;
  average_quality_score: number;
  total_rewards: number;
  reputation_score: number;
}

export interface Reward {
  id: number;
  amount: number;
  status: 'pending' | 'distributed';
  tx_hash: string | null;
  created_at: string;
}

export interface UserRewards {
  pending_amount: number;
  distributed_amount: number;
  total_amount: number;
  total_rewards: number;
  rewards: Reward[];
}

export interface Subscription {
  subscription_id: number | null;
  tier: 'free' | 'pro' | 'enterprise';
  status: string;
  rate_limit: number;
  current_period_start?: string;
  current_period_end?: string;
  cancel_at_period_end?: boolean;
}

export const api = {
  getUser: async (address: string): Promise<User> => {
    const response = await axios.get(`${API_URL}/api/v1/users/${address}`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  getUserContributions: async (address: string): Promise<{ contributions: Contribution[] }> => {
    const response = await axios.get(`${API_URL}/api/v1/users/${address}/contributions`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  getUserStats: async (address: string): Promise<UserStats> => {
    const response = await axios.get(`${API_URL}/api/v1/users/${address}/stats`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  getUserRewards: async (address: string): Promise<UserRewards> => {
    const response = await axios.get(`${API_URL}/api/v1/users/${address}/rewards`, {
      headers: getAuthHeaders(),
    });
    const data = response.data;
    return {
      pending_amount: data.pending_amount ?? 0,
      distributed_amount: data.distributed_amount ?? 0,
      total_amount: data.total_rewards ?? 0,
      total_rewards: data.total_rewards ?? 0,
      rewards: data.rewards ?? [],
    };
  },

  getSubscription: async (): Promise<Subscription> => {
    const response = await axios.get(`${API_URL}/api/v1/payments/subscriptions/current`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  createCheckoutSession: async (
    tier: string,
    successUrl: string,
    cancelUrl: string
  ): Promise<{ checkout_url: string; session_id: string }> => {
    const response = await axios.post(
      `${API_URL}/api/v1/payments/checkout-session`,
      null,
      {
        params: { tier, success_url: successUrl, cancel_url: cancelUrl },
        headers: getAuthHeaders(),
      }
    );
    return response.data;
  },

  getCustomerPortalUrl: async (returnUrl: string): Promise<{ portal_url: string }> => {
    const response = await axios.post(
      `${API_URL}/api/v1/payments/customer-portal`,
      null,
      {
        params: { return_url: returnUrl },
        headers: getAuthHeaders(),
      }
    );
    return response.data;
  },
};
