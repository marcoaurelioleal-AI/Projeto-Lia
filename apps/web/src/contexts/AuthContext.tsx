import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { api, clearToken, setToken } from '../api/client';
import type { User } from '../types';
import { AuthContext, type AuthContextValue } from './AuthContextBase';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .me()
      .then((currentUser) => {
        setToken('cookie');
        setUser(currentUser);
      })
      .catch(() => {
        clearToken();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (username: string, password: string) => {
        const response = await api.login(username, password);
        setToken(response.access_token);
        setUser(response.user);
      },
      logout: () => {
        void api.logout();
        clearToken();
        setUser(null);
      }
    }),
    [loading, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
