"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { setToken } from "@/lib/auth";

const AUTH_RETURN_KEY = "auth_return";

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const hash = window.location.hash.slice(1);
    const params = new URLSearchParams(hash);
    const token = params.get("token");

    if (token) {
      setToken(token);
      let returnUrl = "/";
      try {
        const saved = localStorage.getItem(AUTH_RETURN_KEY);
        if (saved) {
          const data = JSON.parse(saved);
          if (data.url) returnUrl = data.url;
        }
      } catch { /* keep "/" */ }
      router.replace(returnUrl);
    } else {
      router.replace("/?error=auth_failed");
    }
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950">
      <p className="text-zinc-400">Signing you in...</p>
    </div>
  );
}
