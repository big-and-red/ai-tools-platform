"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { getAuthHeaders } from "@/lib/auth";
import { createJob } from "@/lib/api/jobs";

const JOB_TIMEOUT_MS = 300_000; // 5min — research agent can take 2-3 min
const PENDING_POLL_INTERVAL_MS = 30_000; // poll DB every 30s to detect stuck pending jobs

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type StreamEvent =
  | { type: "status"; node: string; message: string }
  | { type: "questions"; data: { questions: string[] } }
  | { type: "report"; data: { title: string; content: string } }
  | { type: "review"; node: string; data: Record<string, unknown> }
  | { type: "done"; job_id: string }
  | { type: "error"; message: string };

export interface RunState {
  status: "idle" | "running" | "done" | "error";
  events: StreamEvent[];
  report: string | null;
  error: string | null;
}

export function useJobStream(toolId: string) {
  const [state, setState] = useState<RunState>({
    status: "idle",
    events: [],
    report: null,
    error: null,
  });
  const abortRef = useRef<AbortController | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const jobIdRef = useRef<string | null>(null);
  const isRunningRef = useRef(false);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      abortRef.current?.abort();
    };
  }, []);

  const run = useCallback(
    async (query: string, inputOverride?: Record<string, string>) => {
      if (isRunningRef.current) return;
      isRunningRef.current = true;

      setState({ status: "running", events: [], report: null, error: null });

      try {
        const job = await createJob({ tool_id: toolId, input: inputOverride ?? { query } });

        jobIdRef.current = job.id;

        // Poll DB every 30s — catches stuck pending (worker down) before the big timeout
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = setInterval(async () => {
          try {
            const res = await fetch(`${API_URL}/api/v1/jobs/${job.id}`, {
              headers: getAuthHeaders(),
            });
            if (!res.ok) return;
            const j = await res.json();
            if (j.status === "completed") {
              if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
              abortRef.current?.abort();
              if (timeoutRef.current) clearTimeout(timeoutRef.current);
              isRunningRef.current = false;
              setState((prev) => ({ ...prev, status: "done", report: j.result?.formatted_output ?? prev.report }));
            } else if (j.status === "failed") {
              if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
              abortRef.current?.abort();
              if (timeoutRef.current) clearTimeout(timeoutRef.current);
              isRunningRef.current = false;
              setState((prev) => ({ ...prev, status: "error", error: j.result?.error ?? "Job failed" }));
            }
          } catch {
            // ignore poll errors — SSE is the primary channel
          }
        }, PENDING_POLL_INTERVAL_MS);

        // Safety net: if no terminal event within JOB_TIMEOUT_MS, poll DB and surface error
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(async () => {
          abortRef.current?.abort();
          try {
            const res = await fetch(`${API_URL}/api/v1/jobs/${job.id}`, {
              headers: getAuthHeaders(),
            });
            if (res.ok) {
              const j = await res.json();
              if (j.status === "completed") {
                setState((prev) => ({
                  ...prev,
                  status: "done",
                  report: j.result?.formatted_output ?? prev.report,
                }));
                return;
              }
              if (j.status === "failed") {
                setState((prev) => ({
                  ...prev,
                  status: "error",
                  error: j.result?.error ?? "Job failed",
                }));
                return;
              }
            }
          } catch {
            // ignore
          }
          setState((prev) => ({
            ...prev,
            status: "error",
            error: "Job timed out after 5 minutes. The agent may be overloaded or the AI provider is unavailable — please try again.",
          }));
        }, JOB_TIMEOUT_MS);

        const ctrl = new AbortController();
        abortRef.current = ctrl;
        // Tracks whether we intentionally closed (done/error event) to skip onerror fallback
        let settled = false;

        fetchEventSource(`${API_URL}/api/v1/jobs/${job.id}/stream`, {
          signal: ctrl.signal,
          headers: getAuthHeaders(),
          onopen: async (response) => {
            if (!response.ok) {
              throw new Error(`Stream open failed: ${response.status}`);
            }
          },
          onmessage: (ev) => {
            let event: StreamEvent;
            try {
              event = JSON.parse(ev.data) as StreamEvent;
            } catch {
              return; // ignore malformed messages
            }
            setState((prev) => {
              const next = { ...prev, events: [...prev.events, event] };
              if (event.type === "report") next.report = event.data.content;
              if (event.type === "done") {
                next.status = "done";
                settled = true;
                isRunningRef.current = false;
                if (timeoutRef.current) clearTimeout(timeoutRef.current);
                if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                ctrl.abort();
              }
              if (event.type === "error") {
                next.status = "error";
                next.error = event.message;
                settled = true;
                isRunningRef.current = false;
                if (timeoutRef.current) clearTimeout(timeoutRef.current);
                if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                ctrl.abort();
              }
              return next;
            });
          },
          onerror: (err) => {
            throw err; // stop retry loop → handled in .catch() below
          },
        }).catch(async () => {
          // Skip if we intentionally closed the stream or aborted on unmount/reset/timeout
          if (settled || ctrl.signal.aborted) return;
          isRunningRef.current = false;
          if (timeoutRef.current) clearTimeout(timeoutRef.current);
          // Fetch actual job status from DB — pub/sub may have been missed
          try {
            const statusRes = await fetch(`${API_URL}/api/v1/jobs/${job.id}`, {
              headers: getAuthHeaders(),
            });
            if (statusRes.ok) {
              const jobStatus = await statusRes.json();
              if (jobStatus.status === "failed") {
                setState((prev) => ({
                  ...prev,
                  status: "error",
                  error: jobStatus.result?.error ?? "Job failed",
                }));
                return;
              }
              if (jobStatus.status === "completed") {
                setState((prev) => ({
                  ...prev,
                  status: "done",
                  report: jobStatus.result?.formatted_output ?? prev.report,
                }));
                return;
              }
            }
          } catch {
            // fallthrough to generic message
          }
          setState((prev) => ({
            ...prev,
            status: "error",
            error: "Connection lost. The job may still be running.",
          }));
        });
      } catch (err) {
        isRunningRef.current = false;
        setState({
          status: "error",
          events: [],
          report: null,
          error: err instanceof Error ? err.message : "Failed to start job",
        });
      }
    },
    [toolId],
  );

  const reset = useCallback(() => {
    abortRef.current?.abort();
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    isRunningRef.current = false;
    setState({ status: "idle", events: [], report: null, error: null });
  }, []);

  return { state, run, reset };
}
