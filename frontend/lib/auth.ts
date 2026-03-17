/**
 * Authentication service for NWU Protocol frontend.
 * Handles wallet-based JWT authentication against the backend API.
 */

import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const AUTH_TOKEN_KEY = 'nwu_auth_token';

export const authService = {
  /** Initiate wallet connection and receive a nonce to sign. */
  async connect(address: string): Promise<{ nonce: string; message: string }> {
    const response = await axios.post(`${API_BASE}/api/v1/auth/connect`, { address });
    return response.data;
  },

  /** Verify the signed nonce and receive a JWT access token. */
  async verify(
    address: string,
    signature: string,
    nonce: string
  ): Promise<{ access_token: string; token_type: string }> {
    const response = await axios.post(`${API_BASE}/api/v1/auth/verify`, {
      address,
      signature,
      nonce,
    });
    return response.data;
  },

  /** Logout the current wallet session. */
  async logout(address: string): Promise<void> {
    try {
      await axios.post(`${API_BASE}/api/v1/auth/logout`, { address });
    } catch {
      // Ignore logout errors — token will be cleared locally regardless.
    }
  },

  /** Persist the JWT token in localStorage. */
  setAuthToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(AUTH_TOKEN_KEY, token);
    }
  },

  /** Retrieve the stored JWT token, or null if not authenticated. */
  getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(AUTH_TOKEN_KEY);
    }
    return null;
  },

  /** Remove the stored JWT token. */
  clearAuthToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(AUTH_TOKEN_KEY);
    }
  },
};
