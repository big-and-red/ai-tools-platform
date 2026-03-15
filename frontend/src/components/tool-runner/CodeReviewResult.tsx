"use client";

import { useState, useCallback } from "react";
import { SyntaxHighlighter } from "@/components/ui/syntax-highlighter";
import { ChevronDown, ChevronRight, Copy, Check } from "lucide-react";

interface CodeIssue {
  severity: "critical" | "warning" | "suggestion";
  line: string | null;
  title: string;
  explanation: string;
  code_snippet: string | null;
}

interface ReviewData {
  language: string;
  summary: string;
  issues: CodeIssue[];
  score: number;
}

const SEVERITY_CONFIG = {
  critical:   { color: "border-red-500/40 bg-red-950/30", badge: "bg-red-500/20 text-red-300", icon: "●" },
  warning:    { color: "border-yellow-500/40 bg-yellow-950/30", badge: "bg-yellow-500/20 text-yellow-300", icon: "●" },
  suggestion: { color: "border-blue-500/40 bg-blue-950/30", badge: "bg-blue-500/20 text-blue-300", icon: "●" },
} as const;

export function CodeReviewResult({
  review,
  originalCode,
  originalLanguage,
}: {
  review: ReviewData;
  originalCode?: string;
  originalLanguage?: string;
}) {
  const [codeOpen, setCodeOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const lang = originalLanguage || review.language;

  const copyCode = useCallback(() => {
    if (!originalCode) return;
    navigator.clipboard.writeText(originalCode).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [originalCode]);

  return (
    <div className="space-y-4">
      {/* Score + Summary */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-zinc-400">Code Quality Score</h3>
          <div className={`text-2xl font-bold ${
            review.score >= 8 ? "text-emerald-400" :
            review.score >= 5 ? "text-yellow-400" : "text-red-400"
          }`}>
            {review.score}/10
          </div>
        </div>
        <p className="text-sm text-zinc-300">{review.summary}</p>
        {review.language && (
          <span className="mt-3 inline-block rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs text-zinc-400">
            {review.language}
          </span>
        )}
      </div>

      {/* Original Code (collapsible) */}
      {originalCode && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden">
          <div className="flex items-center">
            <button
              onClick={() => setCodeOpen((v) => !v)}
              className="flex flex-1 items-center gap-2 px-5 py-3 text-left text-sm font-medium text-zinc-400 hover:text-zinc-200 transition-colors"
            >
              {codeOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              Original Code
              <span className="ml-auto text-xs text-zinc-600">{originalCode.split("\n").length} lines</span>
            </button>
            <button
              onClick={copyCode}
              className="mr-3 rounded-md p-1.5 text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
              title="Copy code"
            >
              {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
            </button>
          </div>
          {codeOpen && (
            <div className="border-t border-zinc-800">
              <SyntaxHighlighter code={originalCode} language={lang} />
            </div>
          )}
        </div>
      )}

      {/* Issues */}
      {review.issues.length === 0 ? (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4 text-sm text-emerald-300">
          No issues found — code looks good!
        </div>
      ) : (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-zinc-400">
            {review.issues.length} issue{review.issues.length > 1 ? "s" : ""} found
          </h3>
          {review.issues.map((issue, i) => {
            const cfg = SEVERITY_CONFIG[issue.severity];
            return (
              <div key={i} className={`rounded-xl border p-4 ${cfg.color}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cfg.badge}`}>
                      {cfg.icon} {issue.severity}
                    </span>
                    {issue.line && (
                      <span className="text-xs text-zinc-500">
                        Line {issue.line}
                      </span>
                    )}
                  </div>
                </div>
                <p className="mt-2 text-sm font-medium text-white">{issue.title}</p>
                <p className="mt-1 text-sm text-zinc-400">{issue.explanation}</p>
                {issue.code_snippet && (
                  <div className="mt-2">
                    <SyntaxHighlighter code={issue.code_snippet} language={lang} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
