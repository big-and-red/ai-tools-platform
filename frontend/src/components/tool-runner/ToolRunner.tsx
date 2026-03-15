"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/auth/useAuth";
import { useJobStream } from "./useJobStream";
import { MarkdownReport } from "./MarkdownReport";

const AUTH_RETURN_KEY = "auth_return";

interface AuthReturn {
  url: string;
  query: string;
}

function saveAuthReturn(query: string) {
  const data: AuthReturn = { url: window.location.pathname, query };
  localStorage.setItem(AUTH_RETURN_KEY, JSON.stringify(data));
}

function consumeAuthReturn(): AuthReturn | null {
  const raw = localStorage.getItem(AUTH_RETURN_KEY);
  if (!raw) return null;
  localStorage.removeItem(AUTH_RETURN_KEY);
  try { return JSON.parse(raw); } catch { return null; }
}

export function ToolRunner({ toolId, creditCost }: { toolId: string; creditCost?: number }) {
  const [query, setQuery] = useState("");
  const { user, signInWithGoogle } = useAuth();
  const { state, run, reset } = useJobStream(toolId);
  const [showGate, setShowGate] = useState(false);

  useEffect(() => {
    const saved = consumeAuthReturn();
    if (saved?.query) setQuery(saved.query);
  }, []);

  const handleRun = () => {
    if (!query.trim()) return;
    if (!user) {
      setShowGate(true);
      return;
    }
    run(query.trim());
  };

  const handleSignIn = () => {
    saveAuthReturn(query);
    signInWithGoogle();
  };

  return (
    <div className="mt-8 space-y-6">
      {/* Input */}
      {state.status === "idle" && (
        <div className="space-y-3">
          <textarea
            value={query}
            onChange={(e) => { setQuery(e.target.value); setShowGate(false); }}
            placeholder="What do you want to research?"
            rows={3}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800 p-3 text-sm text-white placeholder-zinc-500 focus:border-violet-500 focus:outline-none resize-none"
          />

          {showGate && (
            <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 p-4 space-y-3">
              <p className="text-sm text-zinc-200">
                Sign in to get <span className="font-semibold text-violet-400">500 free credits</span> and run this agent
              </p>
              {creditCost && (
                <p className="text-xs text-zinc-400">
                  ⚡ This tool costs ~{creditCost} credits per run
                </p>
              )}
              <Button
                onClick={handleSignIn}
                className="w-full bg-white text-zinc-900 hover:bg-zinc-100 font-medium"
              >
                Sign in with Google
              </Button>
            </div>
          )}

          {!showGate && (
            <Button
              onClick={handleRun}
              disabled={!query.trim()}
              className="w-full bg-violet-600 hover:bg-violet-500 text-white"
            >
              Run Research Agent →
            </Button>
          )}
        </div>
      )}

      {/* Progress */}
      {state.status === "running" && (
        <div className="space-y-2">
          {state.events
            .filter((e) => e.type === "status" || e.type === "questions")
            .map((event, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                {event.type === "status" && (
                  <>
                    <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse" />
                    <span className="text-zinc-400">{event.message}</span>
                  </>
                )}
                {event.type === "questions" && (
                  <div className="w-full rounded-lg border border-zinc-800 bg-zinc-900 p-3">
                    <p className="text-xs text-zinc-500 mb-1">Sub-questions:</p>
                    <ul className="space-y-0.5">
                      {event.data.questions.map((q, qi) => (
                        <li key={qi} className="text-xs text-zinc-300">
                          • {q}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <span className="animate-spin">⟳</span> Running...
          </div>
        </div>
      )}

      {/* Report */}
      {state.report && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
          <MarkdownReport content={state.report} />
          <div className="mt-6 border-t border-zinc-800 pt-4">
            <Button
              variant="ghost"
              onClick={reset}
              className="text-zinc-500 hover:text-white text-sm"
            >
              ← New search
            </Button>
          </div>
        </div>
      )}

      {/* Error */}
      {state.status === "error" && (
        <div className="rounded-lg border border-red-800 bg-red-950/50 p-4 text-sm text-red-400">
          {state.error}
          <Button
            variant="ghost"
            onClick={reset}
            className="mt-2 block text-zinc-500"
          >
            Try again
          </Button>
        </div>
      )}
    </div>
  );
}
