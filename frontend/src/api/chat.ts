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