import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { login as apiLogin, register as apiRegister, getCurrentUser as apiGetCurrentUser } from "../api/client";

const AuthContext = createContext(null);

function extractErrorMessage(e, fallback) {
  const detail = e.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join(", ");
  }
  return fallback;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem("supportai_token");
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const data = await apiGetCurrentUser();
      setUser(data);
    } catch {
      localStorage.removeItem("supportai_token");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = useCallback(async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiLogin(email, password);
      localStorage.setItem("supportai_token", data.access_token);
      await fetchUser();
    } catch (e) {
      setError(extractErrorMessage(e, "Login failed"));
      throw e;
    } finally {
      setLoading(false);
    }
  }, [fetchUser]);

  const register = useCallback(async (email, password, fullName) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiRegister(email, password, fullName);
      localStorage.removeItem("supportai_token");
      window.location.href = "/login";
    } catch (e) {
      setError(extractErrorMessage(e, "Registration failed"));
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("supportai_token");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, error }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
