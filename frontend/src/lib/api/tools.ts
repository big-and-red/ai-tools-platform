import { SERVER_API_URL } from "./config";
import { ToolRead } from "./types";

export async function getTools(): Promise<ToolRead[]> {
  const res = await fetch(`${SERVER_API_URL}/api/v1/tools`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error(`Failed to fetch tools: ${res.status}`);
  return res.json();
}

export async function getTool(id: string): Promise<ToolRead> {
  const res = await fetch(`${SERVER_API_URL}/api/v1/tools/${id}`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error(`Tool not found: ${res.status}`);
  return res.json();
}
