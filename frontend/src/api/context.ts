// context.ts - 上下文统计 API 封装
// 提供上下文信息面板所需的数据接口

/** 上下文统计响应 */
export interface ContextStats {
  thread_id: string;
  message_count: number;
  total_tokens: number;
  max_context_window: number;
  usage_percentage: number;
  breakdown: {
    system_prompt: number;
    history_messages: number;
    user_messages: number;
    ai_replies: number;
    tool_calls: number;
    tool_results: number;
    summary: number;
    manual_context: number;
  };
  summary_status: {
    is_summarized: boolean;
    triggered_at?: string;
    original_count?: number;
    preserved_count?: number;
    summary_tokens?: number;
  };
}

/** 后端响应结构 */
interface ContextStatsResponse {
  success: boolean;
  data: ContextStats;
}

/**
 * 获取会话上下文统计信息
 * @param threadId 会话 ID
 * @returns 上下文统计信息
 */
export const getContextStats = async (threadId: string): Promise<ContextStats> => {
  const response = await fetch(`/api/context/${encodeURIComponent(threadId)}/stats`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  const data: ContextStatsResponse = await response.json();
  return data.data;
};