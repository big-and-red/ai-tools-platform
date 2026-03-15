"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Header } from "@/components/header/Header";
import { getAuthHeaders, getToken } from "@/lib/auth";
import { MarkdownReport } from "@/components/tool-runner/MarkdownReport";
import { CodeReviewResult } from "@/components/tool-runner/CodeReviewResult";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface JobDetail {
  id: string;
  tool_id: string;
  tool_type: string;
  status: string;
  input: Record<string, any>;
  result: any;
  credits_used: number | null;
  created_at: string;
}

export default function HistoryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/");
      return;
    }
    if (!id) return;

    fetch(`${API_URL}/api/v1/jobs/${id}`, { headers: getAuthHeaders() })
      .then(async (r) => {
        if (r.status === 401 || r.status === 403) {
          router.replace("/");
          return null;
        }
        return r.ok ? r.json() : null;
      })
      .then((jobData) => {
        if (jobData) setJob(jobData);
      })
      .finally(() => setLoading(false));
  }, [id, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950">
        <Header />
        <main className="mx-auto max-w-4xl px-6 py-12">
          <p className="text-zinc-500">Loading...</p>
        </main>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-zinc-950">
        <Header />
        <main className="mx-auto max-w-4xl px-6 py-12">
          <p className="text-zinc-500">Not found.</p>
        </main>
      </div>
    );
  }

  const isCodeReview = job.tool_type === "code_review";
  const isResearchAgent = job.tool_type === "research_agent";

  let content = null;
  if (job.status === "completed" && job.result) {
    if (isCodeReview) {
      content = (
        <CodeReviewResult
          review={job.result}
          originalCode={job.input?.code}
          originalLanguage={job.input?.language}
        />
      );
    } else if (isResearchAgent && job.result.formatted_output) {
      // Research agent has formatted_output
      content = (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
          <MarkdownReport content={job.result.formatted_output} />
        </div>
      );
    }
  }

  const errorMsg = job.status === "failed" 
    ? (job.result?.error ?? "Unknown error")
    : null;

  return (
    <div className="min-h-screen bg-zinc-950">
      <Header />
      <main className="mx-auto max-w-4xl px-6 py-12">
        <Link
          href="/history"
          className="text-sm text-zinc-500 hover:text-white mb-6 block"
        >
          ← Back to History
        </Link>

        {job.credits_used !== null && (
          <p className="text-xs text-zinc-500 mb-4">⚡ {job.credits_used} credits used</p>
        )}

        {content ? (
          content
        ) : errorMsg ? (
          <p className="text-zinc-500">Failed: {errorMsg}</p>
        ) : (
          <p className="text-zinc-500">No result available yet.</p>
        )}
      </main>
    </div>
  );
}
