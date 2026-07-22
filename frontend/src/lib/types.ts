export interface AccountPlan {
  id?: string;
  session_id?: string;
  company_name: string;
  overview: string;
  products_services: string;
  market_position: string;
  competitors: string;
  financial_snapshot: string;
  key_contacts: string;
  opportunities: string;
  risks: string;
  recommended_actions: string;
  locations: string;
  company_images: string[];
  sources: { title: string; url: string; content?: string }[];
  researched_at?: string;
  extra_sections?: Record<string, string>;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface DiffResult {
  [section: string]: {
    old: string;
    new: string;
  };
}

export interface ResearchResponse {
  reply: string;
  plan: AccountPlan;
  chat_history: ChatMessage[];
  diff_result: DiffResult;
  company_name: string;
}
