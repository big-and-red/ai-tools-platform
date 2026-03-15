/**
 * Server-side fetches (Server Components) run inside Docker network.
 * They must use the internal Docker hostname "backend:8000", not localhost.
 *
 * Client-side fetches (browser) always use NEXT_PUBLIC_API_URL = http://localhost:8000.
 *
 * API_INTERNAL_URL is set in docker-compose only (not exposed to browser).
 */
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const SERVER_API_URL =
  process.env.API_INTERNAL_URL ?? API_URL;
