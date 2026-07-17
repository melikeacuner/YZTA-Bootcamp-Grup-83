export type MethodologyType = "ishikawa" | "8d" | "5why" | "pdca";

export const METHODOLOGY_LABELS: Record<MethodologyType, string> = {
  ishikawa: "Ishikawa (Balik Kilcigi)",
  "8d": "8D",
  "5why": "5 Why",
  pdca: "PDCA",
};

export interface UserPublic {
  id: string;
  email: string;
  role: "user" | "admin";
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface SessionResponse {
  id: string;
  methodology: MethodologyType;
  status: "active" | "completed" | "abandoned";
  current_step: number;
  problem_description: string;
  answers: Record<string, string>;
}

export interface RecordResponse {
  id: string;
  session_id: string;
  title: string;
  description: string;
  methodology: MethodologyType;
  industry: string | null;
  department: string | null;
  root_cause: string | null;
  corrective_actions: string | null;
  lessons_learned: string;
  embedding_status: "pending" | "processing" | "completed" | "failed";
}

export interface PaginatedRecords {
  items: RecordResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface KnowledgeSearchResult {
  id: string;
  score: number;
  title?: string;
  methodology?: string;
  industry?: string | null;
  department?: string | null;
}
