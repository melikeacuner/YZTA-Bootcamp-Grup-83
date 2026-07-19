"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getMe } from "./api";
import { UserPublic } from "./types";

const TOKEN_STORAGE_KEY = "proby_ai_token";

interface AuthContextValue {
  token: string | null;
  user: UserPublic | null;
  isLoading: boolean;
  login: (token: string) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserPublic | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUser = useCallback(async (authToken: string) => {
    try {
      const userData = await getMe(authToken);
      setUser(userData);
    } catch (err) {
      console.error("Failed to fetch user profile:", err);
      // If token is invalid, clear it
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
      setToken(null);
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const storedToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (storedToken) {
      setToken(storedToken);
      fetchUser(storedToken).finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [fetchUser]);

  const login = useCallback((newToken: string) => {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, newToken);
    setToken(newToken);
    setIsLoading(true);
    fetchUser(newToken).finally(() => setIsLoading(false));
  }, [fetchUser]);

  const logout = useCallback(() => {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (token) {
      await fetchUser(token);
    }
  }, [token, fetchUser]);

  return (
    <AuthContext.Provider value={{ token, user, isLoading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth, AuthProvider icinde kullanilmalidir");
  }
  return context;
}
