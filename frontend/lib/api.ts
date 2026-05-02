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
  average_quality_score: number;
  total_rewards: number;
  reputation_score: number;
}

export interface UserRewards {
  pending_amount: number;
  distributed_amount: number;
  total_rewards: number;
}

// ---------------------------------------------------------------------------
// Perplexity types
// ---------------------------------------------------------------------------

export interface PerplexityResult {
  success: boolean;
  content: string;
  citations: string[];
  model: string;
  usage: Record<string, number>;
  finish_reason: string | null;
}

export interface PerplexityStatus {
  configured: boolean;
  message: string;
  available_models: string[];
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------

export const api = {
  // Perplexity
  perplexityStatus: async (): Promise<PerplexityStatus> => {
    const response = await axios.get(`${API_URL}/api/v1/perplexity/status`);
    return response.data;
  },

  perplexitySearch: async (
    query: string,
    model = 'sonar',
    systemPrompt?: string
  ): Promise<PerplexityResult> => {
    const response = await axios.post(
      `${API_URL}/api/v1/perplexity/search`,
      { query, model, system_prompt: systemPrompt },
      { headers: getAuthHeaders() }
    );
    return response.data;
  },

  perplexityResearch: async (
    topic: string,
    depth: 'standard' | 'deep' = 'standard'
  ): Promise<PerplexityResult> => {
    const response = await axios.post(
      `${API_URL}/api/v1/perplexity/research`,
      { topic, depth },
      { headers: getAuthHeaders() }
    );
    return response.data;
  },

  perplexityFactCheck: async (claim: string): Promise<PerplexityResult> => {
    const response = await axios.post(
      `${API_URL}/api/v1/perplexity/fact-check`,
      { claim },
      { headers: getAuthHeaders() }
    );
    return response.data;
  },

  perplexityChat: async (
    messages: ChatMessage[],
    model = 'sonar'
  ): Promise<PerplexityResult> => {
    const response = await axios.post(
      `${API_URL}/api/v1/perplexity/chat`,
      { messages, model },
      { headers: getAuthHeaders() }
    );
    return response.data;
  },

  perplexityMarketAnalysis: async (market: string): Promise<PerplexityResult> => {
    const response = await axios.post(
      `${API_URL}/api/v1/perplexity/market-analysis`,
      { market },
      { headers: getAuthHeaders() }
    );
    return response.data;
  },

  perplexityTechnicalResearch: async (subject: string): Promise<PerplexityResult> => {
    const response = await axios.post(
      `${API_URL}/api/v1/perplexity/technical-research`,
      { subject },
      { headers: getAuthHeaders() }
    );
    return response.data;
  },

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
    return response.data;
  },
};
