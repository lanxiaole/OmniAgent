export interface ChatRequest {
  message: string;
  thread_id: string;   // 必需，无默认值
}

export interface ChatResponse {
  reply: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export interface HistoryResponse {
  messages: Message[];
}