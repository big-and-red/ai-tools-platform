"use client";

import { useState, useEffect, useCallback } from "react";
import { getToken, clearToken, fetchWithAuth } from "@/lib/auth";
import { jwtDecode } from "jwt-decode";

interface JWTPayload {
  sub: string;
  email: string;
  exp: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function useAuth() {
  const [user, setUser] = useState<JWTPayload | null>(null);
  const [credits, setCredits] = useState<number | null>(null);
  const [creditsError, setCreditsError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const fetchCredits = useCallback(async () => {
    setCreditsError(false);
    try {
      const r = await fetchWithAuth(`${API_URL}/api/v1/auth/me`);
      if (r.status === 401) {
        // fetchWithAuth already tried refresh — truly expired
        clearToken();
        setUser(null);
        setCredits(null);
        return;
      }
      if (!r.ok) {
        setCreditsError(true);
        return;
      }
      const data = await r.json();
      // Re-hydrate user from the (possibly refreshed) token
      const freshToken = getToken();
      if (freshToken) {
        try {
          setUser(jwtDecode<JWTPayload>(freshToken));
        } catch {
          // ignore
        }
      }
      setCredits(data.credits_balance);
    } catch {
      setCreditsError(true);
    }
  }, []);

  // Single effect: decode token → if valid, fetch credits in the same pass (no waterfall)
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const payload = jwtDecode<JWTPayload>(token);
      if (payload.exp * 1000 < Date.now()) {
        clearToken();
        setIsLoading(false);
        return;
      }
      setUser(payload);
    } catch {
      clearToken();
      setIsLoading(false);
      return;
    }
    // Fetch credits immediately — no second render cycle needed
    fetchCredits().finally(() => setIsLoading(false));
  }, [fetchCredits]);

  const signOut = async () => {
    try {
      await fetch(`${API_URL}/api/v1/auth/logout`, {
        method: "POST",
        credentials: "include", // clears the httpOnly refresh cookie
      });
    } catch {
      // ignore network errors on logout
    }
    clearToken();
    setUser(null);
    setCredits(null);
    setCreditsError(false);
    window.location.href = "/";
  };

  const signInWithGoogle = () => {
    window.location.href = `${API_URL}/api/v1/auth/google`;
  };

  return {
    user,
    credits,
    creditsError,
    isLoading,
    signOut,
    signInWithGoogle,
    refreshCredits: fetchCredits,
  };
}
