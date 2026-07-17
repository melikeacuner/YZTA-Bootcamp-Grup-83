import type {
  KnowledgeSearchResult,
  MethodologyType,
  PaginatedRecords,
  RecordResponse,
  SessionResponse,
  TokenResponse,
  UserPublic,
} from "./types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const API_V1 = `${API_BASE_URL}/api/v1`;

export interface ApiEnvelope<T> {
  status: "success" | "error";
  data: T | null;
  error: string | null;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string } = {},
): Promise<T> {
  const { token, headers, ...rest } = options;
  const response = await fetch(`${API_V1}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  const envelope = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || envelope.status === "error") {
    throw new ApiError(envelope.error ?? `Istek basarisiz: ${response.status}`, response.status);
  }
  return envelope.data as T;
}

export async function fetchHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Health check basarisiz: ${response.status}`);
  }
  return response.json();
}

export function registerUser(email: string, password: string): Promise<UserPublic> {
  return request<UserPublic>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function loginUser(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function createSession(
  token: string,
  methodology: MethodologyType,
  problemDescription: string,
): Promise<SessionResponse> {
  return request<SessionResponse>("/sessions", {
    method: "POST",
    token,
    body: JSON.stringify({ methodology, problem_description: problemDescription }),
  });
}

export function getSession(token: string, sessionId: string): Promise<SessionResponse> {
  return request<SessionResponse>(`/sessions/${sessionId}`, { token });
}

export function submitStepResponse(
  token: string,
  sessionId: string,
  responseText: string,
): Promise<SessionResponse> {
  return request<SessionResponse>(`/sessions/${sessionId}/steps`, {
    method: "POST",
    token,
    body: JSON.stringify({ response: responseText }),
  });
}

export function requestFollowUp(token: string, sessionId: string): Promise<string> {
  return request<string>(`/sessions/${sessionId}/follow-up`, { method: "POST", token });
}

export function goBackStep(token: string, sessionId: string): Promise<SessionResponse> {
  return request<SessionResponse>(`/sessions/${sessionId}/back`, { method: "POST", token });
}

export function completeSession(token: string, sessionId: string): Promise<SessionResponse> {
  return request<SessionResponse>(`/sessions/${sessionId}/complete`, { method: "POST", token });
}

export function createRecord(
  token: string,
  payload: {
    session_id: string;
    title: string;
    lessons_learned: string;
    root_cause?: string;
    corrective_actions?: string;
    industry?: string;
    department?: string;
  },
): Promise<RecordResponse> {
  return request<RecordResponse>("/records", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export function listRecords(
  token: string,
  page = 1,
  pageSize = 20,
): Promise<PaginatedRecords> {
  return request<PaginatedRecords>(`/records?page=${page}&page_size=${pageSize}`, { token });
}

export function searchKnowledge(
  token: string,
  query: string,
  filters: { methodology?: string; industry?: string; department?: string } = {},
): Promise<KnowledgeSearchResult[]> {
  const params = new URLSearchParams({ q: query, ...filters });
  return request<KnowledgeSearchResult[]>(`/knowledge/search?${params.toString()}`, { token });
}
