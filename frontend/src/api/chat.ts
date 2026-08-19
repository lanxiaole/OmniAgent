/**
 * chat.ts - 聊天 API 封装
 * 提供 清空历史 / 获取历史 / 流式发送 / 审批 四组接口
 */

// =============== 类型定义 ===============

/** 审批请求信息 */
export interface ApprovalRequest {
  request_id: string;
  tool: string;
  args: Record<string, unknown>;
  reason: string;
}

/** 流式事件回调接口 */
export interface StreamCallbacks {
  /** 文本 token 片段 */
  onToken?: (content: string) => void;
  /** 思考过程片段 */
  onReasoning?: (content: string) => void;
  /** 工具调用开始 */
  onToolCall?: (toolCall: { id: string; name: string; args: unknown }) => void;
  /** 工具调用结果 */
  onToolResult?: (result: { id: string; result: unknown }) => void;
  /** 需要审批 */
  onRequireApproval?: (approval: ApprovalRequest) => void;
  /** 错误 */
  onError?: (message: string) => void;
  /** 上下文总结通知 */
  onSummaryNotice?: (data: {
    summarized_count: number;
    preserved_count: number;
    triggered_at: string;
    summary_content: string;
  }) => void;
  /** 上下文压缩开始 */
  onCompressing?: () => void;
  /** 上下文压缩完成 */
  onCompressDone?: () => void;
}

/** 后端 SSE 事件结构 */
interface StreamEvent {
  type: 'token' | 'reasoning' | 'tool_call' | 'tool_result' | 'require_approval' | 'done' | 'error' | 'summary_notice' | 'compressing' | 'compress_done';
  content?: string;
  id?: string;
  name?: string;
  args?: Record<string, unknown>;
  result?: unknown;
  message?: string;
  request_id?: string;
  tool?: string;
  reason?: string;
  summarized_count?: number;
  preserved_count?: number;
  triggered_at?: string;
  summary_content?: string;
}

// =============== API 函数 ===============

/**
 * 清空会话历史
 */
export const clearHistory = async (threadId: string): Promise<{status: string, message?: string}> => {
  try {
    const response = await fetch(`/api/chat/history?thread_id=${threadId}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('清空会话失败:', error);
    return { status: 'error', message: '清空失败' };
  }
};

/** 后端返回的单条历史消息 */
export interface HistoryMessage {
  role: string;
  content: string;
  reasoning?: string;
  toolCalls?: {
    id: string;
    name: string;
    args: unknown;
    result?: string;
    status: string;
  }[];
  isSummaryNotice?: boolean;
  summaryData?: {
    summarized_count: number;
    preserved_count: number;
    triggered_at: string;
    content: string;
  };
}

/**
 * 从后端获取会话历史消息
 */
export const fetchHistory = async (threadId: string): Promise<HistoryMessage[]> => {
  const response = await fetch(`/api/chat/history?thread_id=${threadId}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  const data = await response.json();
  return data.messages || [];
};

/**
 * 发送审批决策到后端
 */
export const sendApproval = async (
  requestId: string,
  approved: boolean
): Promise<{success: boolean; message?: string}> => {
  try {
    const response = await fetch('/api/agent/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request_id: requestId, approved }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('发送审批决策失败:', error);
    return { success: false, message: '审批请求失败' };
  }
};

/**
 * 使用 fetch + ReadableStream 发送流式请求
 * 解析后端结构化 SSE 事件，分发到对应回调
 *
 * @param message 用户消息
 * @param threadId 会话ID
 * @param callbacks 事件回调集合
 * @param signal AbortSignal，用于取消请求
 */
export const sendMessageStream = async (
  message: string,
  threadId: string,
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> => {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, thread_id: threadId }),
    signal: signal,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('ReadableStream not supported');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    // SSE 事件以 \n\n 分隔
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const data = line.slice(6);

      try {
        const event: StreamEvent = JSON.parse(data);

        switch (event.type) {
          case 'token':
            if (event.content) callbacks.onToken?.(event.content);
            break;
          case 'reasoning':
            if (event.content) callbacks.onReasoning?.(event.content);
            break;
          case 'tool_call':
            callbacks.onToolCall?.({
              id: event.id || '',
              name: event.name || 'unknown',
              args: event.args,
            });
            break;
          case 'tool_result':
            callbacks.onToolResult?.({
              id: event.id || '',
              result: event.result,
            });
            break;
          case 'require_approval':
            callbacks.onRequireApproval?.({
              request_id: event.request_id || '',
              tool: event.tool || '',
              args: event.args || {},
              reason: event.reason || '',
            });
            break;
          case 'summary_notice':
            callbacks.onSummaryNotice?.({
              summarized_count: event.summarized_count || 0,
              preserved_count: event.preserved_count || 0,
              triggered_at: event.triggered_at || '',
              summary_content: event.summary_content || '',
            });
            break;
          case 'compressing':
            callbacks.onCompressing?.();
            break;
          case 'compress_done':
            callbacks.onCompressDone?.();
            break;
          case 'done':
            // 正确释放 reader，避免连接挂起导致 ERR_ABORTED
            reader.cancel();
            return;
          case 'error':
            callbacks.onError?.(event.message || '未知错误');
            reader.cancel();
            return;
        }
      } catch {
        // JSON 解析失败：可能是旧版后端的纯字符串格式，做兼容降级
        if (data === '"[DONE]"' || data === '[DONE]') return;
        if (typeof data === 'string' && !data.startsWith('[ERROR]')) {
          callbacks.onToken?.(data);
        }
      }
    }
  }
};