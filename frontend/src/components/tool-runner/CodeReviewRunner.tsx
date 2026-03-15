"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { CodeInput } from "@/components/ui/code-input";
import { useAuth } from "@/components/auth/useAuth";
import { useJobStream } from "./useJobStream";
import { CodeReviewResult } from "./CodeReviewResult";

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

interface ReviewData {
  language: string;
  summary: string;
  issues: { severity: "critical" | "warning" | "suggestion"; line: string | null; title: string; explanation: string; code_snippet: string | null }[];
  score: number;
}

const LANGUAGES = [
  "python", "javascript", "typescript", "go", "rust", "java",
  "c", "cpp", "csharp", "ruby", "php", "swift", "kotlin", "sql", "bash",
];

export function CodeReviewRunner({ toolId, creditCost }: { toolId: string; creditCost?: number }) {
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("");
  const { user, signInWithGoogle } = useAuth();
  const { state, run, reset } = useJobStream(toolId);
  const [showGate, setShowGate] = useState(false);
  const [review, setReview] = useState<ReviewData | null>(null);
  const submittedCodeRef = useRef("");

  useEffect(() => {
    const saved = consumeAuthReturn();
    if (saved?.query) setCode(saved.query);
  }, []);

  useEffect(() => {
    const reviewEvent = state.events.find((e) => e.type === "review");
    if (reviewEvent && "data" in reviewEvent) {
      setReview(reviewEvent.data as ReviewData);
    }
  }, [state.events]);

  const handleRun = () => {
    if (!code.trim()) return;
    if (!user) {
      setShowGate(true);
      return;
    }
    setReview(null);
    submittedCodeRef.current = code.trim();
    run(code.trim(), { code: code.trim(), language });
  };

  const handleSignIn = () => {
    saveAuthReturn(code);
    signInWithGoogle();
  };

  const handleReset = () => {
    setCode("");
    setLanguage("");
    setReview(null);
    submittedCodeRef.current = "";
    reset();
  };

  return (
    <div className="mt-8 space-y-6">
      {/* Input */}
      {state.status === "idle" && (
        <div className="space-y-3">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white focus:border-violet-500 focus:outline-none"
          >
            <option value="">Auto-detect language</option>
            {LANGUAGES.map((lang) => (
              <option key={lang} value={lang}>
                {lang.charAt(0).toUpperCase() + lang.slice(1)}
              </option>
            ))}
          </select>

          <CodeInput
            value={code}
            onChange={(v) => { setCode(v); setShowGate(false); }}
            language={language}
          />

          {showGate && (
            <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 p-4 space-y-3">
              <p className="text-sm text-zinc-200">
                Sign in to get <span className="font-semibold text-violet-400">free credits</span> and run this tool
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
              disabled={!code.trim()}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white"
            >
              Review Code →
            </Button>
          )}
        </div>
      )}

      {/* Progress */}
      {state.status === "running" && !review && (
        <div className="space-y-2">
          {state.events
            .filter((e) => e.type === "status")
            .map((event, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse" />
                <span className="text-zinc-400">
                  {"message" in event ? event.message : ""}
                </span>
              </div>
            ))}
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <span className="animate-spin">⟳</span> Reviewing...
          </div>
        </div>
      )}

      {/* Review Result */}
      {review && (
        <div className="space-y-4">
          <CodeReviewResult
            review={review}
            originalCode={submittedCodeRef.current}
            originalLanguage={language}
          />

          <div className="border-t border-zinc-800 pt-4">
            <Button
              variant="ghost"
              onClick={handleReset}
              className="text-zinc-500 hover:text-white text-sm"
            >
              ← Review another snippet
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
            onClick={handleReset}
            className="mt-2 block text-zinc-500"
          >
            Try again
          </Button>
        </div>
      )}
    </div>
  );
}
