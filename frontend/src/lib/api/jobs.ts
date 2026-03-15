import { API_URL } from "./config";
import { getAuthHeaders } from "@/lib/auth";

export interface JobCreate {
  tool_id: string;
  input: Record<string, string>;
}

export interface JobRead {
  id: string;
  status: string;
  result: { formatted_output?: string } | null;
}

export async function createJob(payload: JobCreate): Promise<JobRead> {
  const res = await fetch(`${API_URL}/api/v1/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to create job: ${res.status}`);
  return res.json();
}
