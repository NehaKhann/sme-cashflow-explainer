import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import type { User } from "../types/api";
import { getMeApi, loginApi, signupApi } from "../api/client";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isDemo: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => void;
  enterDemo: () => void;
  exitDemo: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ apiBase, children }: { apiBase: string; children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(() => localStorage.getItem("demo_mode") === "true");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    getMeApi(apiBase)
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      })
      .finally(() => setLoading(false));
  }, [apiBase]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await loginApi(apiBase, email, password);
    localStorage.setItem("access_token", res.access_token);
    localStorage.setItem("refresh_token", res.refresh_token);
    localStorage.removeItem("demo_mode");
    setIsDemo(false);
    setUser(res.user);
  }, [apiBase]);

  const signup = useCallback(async (email: string, password: string, displayName: string) => {
    const res = await signupApi(apiBase, email, password, displayName);
    localStorage.setItem("access_token", res.access_token);
    localStorage.setItem("refresh_token", res.refresh_token);
    localStorage.removeItem("demo_mode");
    setIsDemo(false);
    setUser(res.user);
  }, [apiBase]);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("demo_mode");
    setUser(null);
    setIsDemo(false);
  }, []);

  const enterDemo = useCallback(() => {
    localStorage.setItem("demo_mode", "true");
    setIsDemo(true);
  }, []);

  const exitDemo = useCallback(() => {
    localStorage.removeItem("demo_mode");
    setIsDemo(false);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, isDemo, login, signup, logout, enterDemo, exitDemo }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
