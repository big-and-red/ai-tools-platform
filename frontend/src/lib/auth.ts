const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Token storage ──────────────────────────────────────────────────────────

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setToken(token: string): void {
  localStorage.setItem("access_token", token);
}

export function clearToken(): void {
  localStorage.removeItem("access_token");
}

export function getAuthHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── Silent refresh ─────────────────────────────────────────────────────────

let _refreshPromise: Promise<boolean> | null = null;

export async function refreshAccessToken(): Promise<boolean> {
  // Deduplicate concurrent refresh calls
  if (_refreshPromise) return _refreshPromise;

  _refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
        method: "POST",
        credentials: "include", // sends httpOnly refresh_token cookie
      });
      if (!res.ok) return false;
      const data = await res.json();
      setToken(data.access_token);
      return true;
    } catch {
      return false;
    } finally {
      _refreshPromise = null;
    }
  })();

  return _refreshPromise;
}

// ── Authenticated fetch with silent refresh on 401 ─────────────────────────

export async function fetchWithAuth(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const res = await fetch(url, {
    ...options,
    headers: { ...options.headers, ...getAuthHeaders() },
    credentials: "include",
  });

  if (res.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      return fetch(url, {
        ...options,
        headers: { ...options.headers, ...getAuthHeaders() },
        credentials: "include",
      });
    }
    // Refresh failed — session truly expired, clear local state
    clearToken();
  }

  return res;
}
