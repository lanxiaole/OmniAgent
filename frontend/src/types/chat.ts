export interface ChatRequest {
  message: string;
  thread_id?: string;   // 可选，默认 "web_user"
}

export interface ChatResponse {
  reply: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}
