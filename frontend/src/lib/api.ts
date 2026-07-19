import type {
  KnowledgeSearchResult,
  MethodologyType,
  PaginatedRecords,
  RecordResponse,
  SessionResponse,
  TokenResponse,
  UserPublic,
  DashboardStats,
  TaskResponse,
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
    public message: string,
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

export function getMe(token: string): Promise<UserPublic> {
  return request<UserPublic>("/auth/me", { token });
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

export function listSessions(token: string): Promise<SessionResponse[]> {
  return request<SessionResponse[]>("/sessions", { token });
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
    problem_category?: string;
    severity?: number;
    occurrence?: number;
    detection?: number;
    yokoten_applied?: boolean;
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

export function getRecord(token: string, recordId: string): Promise<RecordResponse> {
  return request<RecordResponse>(`/records/${recordId}`, { token });
}

export function searchKnowledge(
  token: string,
  query: string,
  filters: { methodology?: string; industry?: string; department?: string } = {},
): Promise<KnowledgeSearchResult[]> {
  const params = new URLSearchParams({ q: query, ...filters });
  return request<KnowledgeSearchResult[]>(`/knowledge/search?${params.toString()}`, { token });
}

// --- Dashboard & Task APIs ---

export function getDashboardStats(token: string): Promise<DashboardStats> {
  return request<DashboardStats>("/dashboard/stats", { token });
}

export function listTasks(
  token: string,
  filters: { problem_record_id?: string; session_id?: string; status?: string } = {},
): Promise<TaskResponse[]> {
  const cleanFilters: Record<string, string> = {};
  if (filters.problem_record_id) cleanFilters.problem_record_id = filters.problem_record_id;
  if (filters.session_id) cleanFilters.session_id = filters.session_id;
  if (filters.status) cleanFilters.status = filters.status;

  const params = new URLSearchParams(cleanFilters);
  return request<TaskResponse[]>(`/tasks?${params.toString()}`, { token });
}

export function createTask(
  token: string,
  payload: {
    problem_record_id?: string | null;
    session_id?: string | null;
    title: string;
    description?: string;
    assignee_name?: string;
    deadline?: string;
  },
): Promise<any> {
  return request<any>("/tasks", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export function updateTask(
  token: string,
  taskId: string,
  payload: {
    title?: string;
    description?: string;
    assignee_name?: string;
    deadline?: string;
    status?: string;
    proof_description?: string;
    proof_url?: string;
  },
): Promise<any> {
  return request<any>(`/tasks/${taskId}`, {
    method: "PUT",
    token,
    body: JSON.stringify(payload),
  });
}

export function deleteTask(token: string, taskId: string): Promise<any> {
  return request<any>(`/tasks/${taskId}`, {
    method: "DELETE",
    token,
  });
}

// --- AI Agent Chat APIs ---

export function agentChat(token: string, sessionId: string, message: string): Promise<{ reply: string }> {
  return request<{ reply: string }>(`/sessions/${sessionId}/agent-chat`, {
    method: "POST",
    token,
    body: JSON.stringify({ message }),
  });
}

export function agentResolve(token: string, sessionId: string): Promise<{ record_id: string; message: string }> {
  return request<{ record_id: string; message: string }>(`/sessions/${sessionId}/agent-resolve`, {
    method: "POST",
    token,
  });
}

export function updateSession(
  token: string,
  sessionId: string,
  payload: {
    assignee_name?: string | null;
    tracker_name?: string | null;
    department?: string | null;
    summary?: string | null;
    tags?: string[] | null;
  },
): Promise<SessionResponse> {
  return request<SessionResponse>(`/sessions/${sessionId}`, {
    method: "PUT",
    token,
    body: JSON.stringify(payload),
  });
}

export function poolChat(
  token: string,
  sessionId: string,
  message: string,
): Promise<SessionResponse> {
  return request<SessionResponse>(`/sessions/${sessionId}/resolve-chat`, {
    method: "POST",
    token,
    body: JSON.stringify({ message }),
  });
}

export function closePoolSession(
  token: string,
  sessionId: string,
): Promise<{ message: string; record_id: string }> {
  return request<{ message: string; record_id: string }>(`/sessions/${sessionId}/pool-close`, {
    method: "POST",
    token,
  });
}
