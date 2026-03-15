"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";

const MESSAGES: Record<string, string> = {
  auth_failed: "Sign-in failed. Please try again.",
};

export function AuthErrorBanner() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const error = params.get("error");
    if (!error) return;

    setMessage(MESSAGES[error] ?? "Authentication error.");

    // Remove ?error= from URL so it doesn't persist on reload or sharing
    const next = new URLSearchParams(params.toString());
    next.delete("error");
    const qs = next.toString();
    router.replace(pathname + (qs ? `?${qs}` : ""), { scroll: false });
  }, [params, router, pathname]);

  if (!message) return null;

  return (
    <div className="mx-auto max-w-7xl px-6 pt-4">
      <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
        {message}
      </div>
    </div>
  );
}
