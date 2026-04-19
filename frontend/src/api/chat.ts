import axios from 'axios';
import type { ChatRequest, ChatResponse } from '../types/chat';

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
 * @param threadId 会话 ID，默认为 'web_user'
 * @returns Promise<string> 后端返回的回复
 */
export const sendMessage = async (message: string, threadId: string = 'web_user'): Promise<string> => {
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
