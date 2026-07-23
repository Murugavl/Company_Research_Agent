import type { ResearchResponse, ChatMessage, AccountPlan } from "./types";

export function generateSessionId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).substring(2, 15) + 
         Math.random().toString(36).substring(2, 15);
}

const rawApiUrl = import.meta.env.VITE_API_BASE_URL || "";
const API_BASE_URL = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl;

export async function researchCompany(payload: {
  user_message: string;
  company_name: string;
  session_id: string;
  chat_history: ChatMessage[];
  current_plan: AccountPlan | null;
}): Promise<ResearchResponse> {
  // Proxied through Vite in dev, or absolute URL in prod
  console.log("Fetching research from:", `${API_BASE_URL}/api/research`);
  const response = await fetch(`${API_BASE_URL}/api/research`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Research failed. Ensure Backend is running.");
  }

  return response.json();
}

export async function researchCompanyStream(
  payload: {
    user_message: string;
    company_name: string;
    session_id: string;
    chat_history: ChatMessage[];
    current_plan: AccountPlan | null;
  },
  onToken: (token: string) => void,
  onPlan: (response: ResearchResponse) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    console.log("Fetching stream from:", `${API_BASE_URL}/api/research/stream`);
    const response = await fetch(`${API_BASE_URL}/api/research/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Research failed. Ensure Backend is running.");
    }

    if (!response.body) {
      throw new Error("ReadableStream not yet supported in this browser.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let done = false;
    let buffer = "";

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        
        // Keep the last partial line in the buffer
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.substring(6).trim();
            if (!dataStr) continue;
            
            try {
              const event = JSON.parse(dataStr);
              if (event.type === "token") {
                onToken(event.content);
              } else if (event.type === "plan") {
                onPlan({
                  reply: "", // will be handled by UI
                  plan: event.plan,
                  chat_history: event.chat_history,
                  diff_result: event.diff_result,
                  company_name: event.company_name
                });
              } else if (event.type === "error") {
                onError(event.message);
              }
            } catch (e) {
              console.error("Failed to parse event:", dataStr, e);
            }
          }
        }
      }
    }
  } catch (err: any) {
    onError(err.message || "An unexpected error occurred during streaming");
  }
}
