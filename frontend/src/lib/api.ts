export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface ApiEnvelope<T> {
  status: "success" | "error";
  data: T | null;
  error: string | null;
}

export async function fetchHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Health check basarisiz: ${response.status}`);
  }
  return response.json();
}
