"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/auth/useAuth";

export function Header() {
  const { user, credits, creditsError, isLoading, signOut, signInWithGoogle } = useAuth();

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-xl font-bold text-white">
          AI Market
        </Link>
        <nav className="flex items-center gap-4" aria-label="User navigation">
          {/* Render nothing while hydrating to prevent FOUC */}
          {!isLoading && (
            <>
              {user ? (
                <>
                  <Link
                    href="/history"
                    className="text-sm text-zinc-400 hover:text-white transition-colors"
                  >
                    History
                  </Link>
                  {creditsError ? (
                    <span
                      className="text-xs text-red-400"
                      title="Failed to load credits — try refreshing"
                      aria-label="Credits unavailable"
                    >
                      <span aria-hidden="true">⚡</span> error
                    </span>
                  ) : (
                    <span
                      className={`text-xs ${credits !== null && credits < 0 ? "text-red-400" : "text-zinc-500"}`}
                      aria-label={`Credits balance: ${credits ?? "loading"}`}
                      title={credits !== null && credits < 0 ? "Negative balance — top up to run tools" : undefined}
                    >
                      <span aria-hidden="true">⚡</span>{" "}
                      {credits !== null ? credits.toLocaleString("ru-RU") : "..."}
                    </span>
                  )}
                  <span className="text-xs text-zinc-500 hidden sm:inline">
                    {user.email}
                  </span>
                  <Button
                    variant="ghost"
                    onClick={signOut}
                    className="text-zinc-400"
                  >
                    Sign Out
                  </Button>
                </>
              ) : (
                <Button
                  onClick={signInWithGoogle}
                  className="bg-violet-600 hover:bg-violet-500 text-white transition-colors flex items-center gap-2"
                >
                  Sign in with Google
                </Button>
              )}
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
