import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const TOKEN_KEY = 'auth_token';

const getAuthHeaders = () => {
  const token = typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const authService = {
  connect: async (address: string): Promise<{ nonce: string; message: string }> => {
    const response = await axios.post(`${API_URL}/api/v1/auth/connect`, { address });
    return response.data;
  },

  verify: async (
    address: string,
    signature: string,
    nonce: string
  ): Promise<{ access_token: string }> => {
    const response = await axios.post(`${API_URL}/api/v1/auth/verify`, {
      address,
      signature,
      nonce,
    });
    return response.data;
  },

  logout: async (address: string): Promise<void> => {
    await axios.post(`${API_URL}/api/v1/auth/logout`, { address }, { headers: getAuthHeaders() });
  },

  getAuthToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(TOKEN_KEY);
  },

  setAuthToken: (token: string): void => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEY, token);
    }
  },

  clearAuthToken: (): void => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY);
    }
  },
};
