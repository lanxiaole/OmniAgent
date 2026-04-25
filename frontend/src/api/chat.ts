import axios from 'axios';
import type { ChatRequest, ChatResponse, HistoryResponse } from '../types/chat';

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

/**
 * 发送消息到后端
 * @param message 用户输入的消息
 * @param threadId 会话 ID
 * @returns Promise<string> 后端返回的回复
 */
export const sendMessage = async (message: string, threadId: string): Promise<string> => {
  try {
    const request: ChatRequest = {
      message,
      thread_id: threadId
    };
    
    const response = await api.post<ChatResponse>('/chat', request);
    return response.data.reply;
  } catch (error) {
    console.error('发送消息失败:', error);
    return '抱歉，服务暂时不可用，请稍后再试。';
  }
};

/**
 * 获取会话历史消息
 * @param threadId 会话 ID
 * @returns Promise<HistoryResponse> 历史消息响应
 */
export const getHistory = async (threadId: string): Promise<HistoryResponse> => {
  try {
    const response = await api.get<HistoryResponse>(`/chat/history?thread_id=${threadId}`);
    return response.data;
  } catch (error) {
    console.error('获取历史消息失败:', error);
    return { messages: [] };
  }
};

/**
 * 清空会话历史
 * @param threadId 会话 ID
 * @returns Promise<{status: string, message?: string}> 操作结果
 */
export const clearHistory = async (threadId: string): Promise<{status: string, message?: string}> => {
  try {
    const response = await api.delete(`/chat/history?thread_id=${threadId}`);
    return response.data;
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
  onToken: (token: string) => void
): Promise<void> => {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, thread_id: threadId }),
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