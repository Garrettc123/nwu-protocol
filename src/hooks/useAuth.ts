import { useBlinkAuth } from '@blinkdotnew/react';
import { blink } from '../lib/blink';

export function useAuth() {
  const { user, isAuthenticated, isLoading, signOut } = useBlinkAuth();

  const login = () => blink.auth.login(window.location.href);

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout: signOut,
  };
}
