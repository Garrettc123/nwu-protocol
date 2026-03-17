/**
 * API client for NWU Protocol frontend.
 * Provides typed wrappers around the backend REST API.
 */

import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Shared types
// ---------------------------------------------------------------------------

export interface User {
  id: number;
  address: string;
  username: string | null;
  email: string | null;
  reputation_score: number;
  total_contributions: number;
  total_rewards: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Contribution {
  id: number;
  ipfs_hash: string;
  file_name: string;
  file_type: string;
  file_size: number;
  title: string;
  description: string | null;
  status: string;
  quality_score: number | null;
  verification_count: number;
  created_at: string;
}

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

export const api = {
  /** Fetch a user by Ethereum address. */
  async getUser(address: string): Promise<User> {
    const response = await axios.get(`${API_BASE}/api/v1/users/${address}`);
    return response.data;
  },

  /** Fetch a user's contributions. */
  async getUserContributions(
    address: string,
  ): Promise<{ contributions: Contribution[]; total: number }> {
    const response = await axios.get(
      `${API_BASE}/api/v1/users/${address}/contributions`,
    );
    return response.data;
  },

  /** Fetch a user's reward stats. */
  async getUserRewards(address: string): Promise<{
    pending_amount: number;
    distributed_amount: number;
    total_amount: number;
  }> {
    const response = await axios.get(`${API_BASE}/api/v1/users/${address}/rewards`);
    return response.data;
  },

  /** Fetch a user's contribution statistics. */
  async getUserStats(address: string): Promise<{
    total_contributions: number;
    verified_contributions: number;
    average_quality_score: number;
  }> {
    const response = await axios.get(`${API_BASE}/api/v1/users/${address}/stats`);
    return response.data;
  },
};
