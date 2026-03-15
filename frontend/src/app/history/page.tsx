"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Header } from "@/components/header/Header";
import { Badge } from "@/components/ui/badge";
import { fetchWithAuth, getToken } from "@/lib/auth";
import { TOOL_BADGE_COLORS, TOOL_LABELS } from "@/lib/constants";
import type { ToolType } from "@/lib/api/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const PAGE_SIZE = 20;
const STALE_THRESHOLD_MS = 5 * 60 * 1000;

interface JobHistoryItem {
  id: string;
  tool_name: string;
  tool_type: string;
  tool_id: string;
  status: "pending" | "running" | "completed" | "failed";
  query: string;
  title: string | null;
  credits_used: number | null;
  created_at: string;
  completed_at: string | null;
}

const STATUS_STYLES: Record<string, string> = {
  completed: "text-green-400 bg-green-400/10",
  failed: "text-red-400 bg-red-400/10",
  running: "text-yellow-400 bg-yellow-400/10",
  pending: "text-zinc-400 bg-zinc-400/10",
  stale: "text-orange-400 bg-orange-400/10",
};
const DEFAULT_STATUS_STYLE = "text-zinc-400 bg-zinc-400/10";

const STATUS_LABELS: Record<string, string> = {
  completed: "completed",
  failed: "failed",
  running: "running",
  pending: "pending",
  stale: "timed out",
};

function getDisplayStatus(job: JobHistoryItem): string {
  if (
    (job.status === "pending" || job.status === "running") &&
    Date.now() - new Date(job.created_at).getTime() > STALE_THRESHOLD_MS
  ) {
    return "stale";
  }
  return job.status;
}

export default function HistoryPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<JobHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [filterTool, setFilterTool] = useState<string | null>(null);

  const fetchJobs = useCallback(
    async (currentOffset: number, append: boolean) => {
      if (append) setLoadingMore(true);

      try {
        const r = await fetchWithAuth(
          `${API_URL}/api/v1/jobs?limit=${PAGE_SIZE}&offset=${currentOffset}`
        );
        if (r.status === 401 || r.status === 403) {
          router.replace("/");
          return;
        }
        if (!r.ok) {
          setError("Failed to load history. Please try again.");
          return;
        }
        const data: JobHistoryItem[] = await r.json();
        setJobs((prev) => (append ? [...prev, ...data] : data));
        setHasMore(data.length === PAGE_SIZE);
        setOffset(currentOffset + data.length);
      } catch {
        setError("Network error. Please check your connection.");
      } finally {
        if (!append) setLoading(false);
        setLoadingMore(false);
      }
    },
    [router]
  );

  useEffect(() => {
    if (!getToken()) {
      router.replace("/");
      return;
    }
    fetchJobs(0, false);
  }, [router, fetchJobs]);

  const handleDelete = async (jobId: string) => {
    setDeletingId(jobId);
    try {
      const r = await fetchWithAuth(`${API_URL}/api/v1/jobs/${jobId}`, {
        method: "DELETE",
      });
      if (r.ok || r.status === 204) {
        setJobs((prev) => prev.filter((j) => j.id !== jobId));
      }
    } finally {
      setDeletingId(null);
    }
  };

  const toolTypes = useMemo(() => {
    const set = new Set(jobs.map((j) => j.tool_type));
    return Array.from(set);
  }, [jobs]);

  const filteredJobs = useMemo(
    () => (filterTool ? jobs.filter((j) => j.tool_type === filterTool) : jobs),
    [jobs, filterTool]
  );

  return (
    <div className="min-h-screen bg-zinc-950">
      <Header />
      <main className="mx-auto max-w-4xl px-6 py-12">
        <h1 className="text-2xl font-bold text-white mb-8">History</h1>

        {loading && <p className="text-zinc-500">Loading...</p>}

        {error && (
          <p className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
            {error}
          </p>
        )}

        {!loading && !error && jobs.length === 0 && (
          <p className="text-zinc-500">
            No runs yet.{" "}
            <Link href="/" className="text-violet-400 hover:underline">
              Run your first tool →
            </Link>
          </p>
        )}

        {!loading && toolTypes.length > 1 && (
          <div className="flex flex-wrap gap-2 mb-6">
            <button
              onClick={() => setFilterTool(null)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                filterTool === null
                  ? "border-white/20 bg-white/10 text-white"
                  : "border-zinc-700 text-zinc-500 hover:text-zinc-300 hover:border-zinc-500"
              }`}
            >
              All
            </button>
            {toolTypes.map((tt) => {
              const isActive = filterTool === tt;
              const colors = TOOL_BADGE_COLORS[tt as ToolType] ?? "";
              return (
                <button
                  key={tt}
                  onClick={() => setFilterTool(isActive ? null : tt)}
                  className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                    isActive
                      ? colors
                      : "border-zinc-700 text-zinc-500 hover:text-zinc-300 hover:border-zinc-500"
                  }`}
                >
                  {TOOL_LABELS[tt as ToolType] ?? tt}
                </button>
              );
            })}
          </div>
        )}

        <div className="space-y-3">
          {filteredJobs.map((job) => {
            const displayStatus = getDisplayStatus(job);
            return (
              <div
                key={job.id}
                className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900 hover:border-zinc-600 transition-colors"
              >
                <Link
                  href={`/history/${job.id}`}
                  className="flex-1 min-w-0 p-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex flex-col gap-1.5">
                      <p className="text-sm font-medium text-white truncate">
                        {job.title || job.query || "(no title)"}
                      </p>
                      <Badge
                        variant="outline"
                        className={`w-fit ${TOOL_BADGE_COLORS[job.tool_type as ToolType] ?? ""}`}
                      >
                        {TOOL_LABELS[job.tool_type as ToolType] ?? job.tool_name}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      {job.credits_used !== null && (
                        <span className="text-xs text-zinc-500">
                          ⚡ {job.credits_used}
                        </span>
                      )}
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${STATUS_STYLES[displayStatus] ?? DEFAULT_STATUS_STYLE}`}
                      >
                        {STATUS_LABELS[displayStatus] ?? displayStatus}
                      </span>
                      <span className="text-xs text-zinc-600">
                        {new Date(job.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </Link>
                <button
                  onClick={() => handleDelete(job.id)}
                  disabled={deletingId === job.id}
                  className="p-3 mr-2 rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-400/10 transition-colors disabled:opacity-50"
                  title="Delete"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    <line x1="10" y1="11" x2="10" y2="17" />
                    <line x1="14" y1="11" x2="14" y2="17" />
                  </svg>
                </button>
              </div>
            );
          })}
        </div>

        {hasMore && (
          <div className="mt-6 text-center">
            <button
              onClick={() => fetchJobs(offset, true)}
              disabled={loadingMore}
              className="rounded-lg border border-zinc-700 bg-zinc-900 px-6 py-2 text-sm text-zinc-400 hover:border-zinc-500 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loadingMore ? "Loading..." : "Load more"}
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
