export type MethodologyType = "ishikawa" | "8d" | "5why" | "pdca";

export const METHODOLOGY_LABELS: Record<MethodologyType, string> = {
  ishikawa: "Ishikawa (Balık Kılçığı)",
  "8d": "8D Metodolojisi",
  "5why": "5 Neden (5-Why)",
  pdca: "PDCA Döngüsü"
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
  status: "active" | "completed" | "abandoned" | "pool";
  current_step: number;
  problem_description: string;
  answers: Record<string, any>;
  agent_chat_history?: Array<{ role: string; content: string }>;
  agent_status?: string;
  assignee_name?: string | null;
  tracker_name?: string | null;
  next_prompt?: string | null;
  department?: string | null;
  summary?: string | null;
  tags?: string[] | null;
}

export interface RecordResponse {
  id: string;
  session_id: string;
  user_id?: string;
  title: string;
  description: string;
  methodology: string;
  industry: string | null;
  department: string | null;
  problem_category: string | null;
  root_cause: string | null;
  corrective_actions: string | null;
  lessons_learned: string;
  step_responses?: Record<string, any>;
  embedding_status: "pending" | "processing" | "completed" | "failed";

  severity?: number;
  occurrence?: number;
  detection?: number;
  rpn?: number;
  yokoten_applied?: boolean;
  closure_checklist?: Record<string, any>;
  resolution_status: string;
  created_at?: string;
  updated_at?: string;
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

export interface DashboardStats {
  total_problems: number;
  closed_problems: number;
  open_problems: number;
  active_sessions: number;
  total_tasks: number;
  todo_tasks: number;
  in_progress_tasks: number;
  completed_tasks: number;
  delayed_tasks: number;
  delayed_rate: number;
  average_rpn: number;
  department_distribution: Record<string, number>;
  category_distribution: Record<string, number>;
  methodology_distribution: Record<string, number>;
}

export interface TaskResponse {
  id: string;
  problem_record_id: string | null;
  session_id: string | null;
  title: string;
  description: string | null;
  assignee_name: string | null;
  deadline: string | null;
  status: "todo" | "in_progress" | "completed" | "delayed";
  proof_description: string | null;
  proof_url: string | null;
  created_at?: string;
  updated_at?: string;
}
