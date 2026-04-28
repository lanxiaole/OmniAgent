/**
 * 清空会话历史
 * @param threadId 会话 ID
 * @returns Promise<{status: string, message?: string}> 操作结果
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

/**
 * 使用 fetch + ReadableStream 发送流式请求
 * @param message 用户消息
 * @param threadId 会话ID
 * @param onToken 每收到一个token时的回调
 */
export const sendMessageStream = async (
  message: string,
  threadId: string,
  onToken: (token: string) => void,
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
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        try {
          const token = JSON.parse(data);
          if (token === '[DONE]') {
            return;
          }
          if (typeof token === 'string' && !token.startsWith('[ERROR]')) {
            onToken(token);
          }
        } catch {
          // 如果解析失败，尝试作为纯文本处理
          if (data !== '[DONE]' && !data.startsWith('[ERROR]')) {
            onToken(data);
          }
        }
      }
    }
  }
};
