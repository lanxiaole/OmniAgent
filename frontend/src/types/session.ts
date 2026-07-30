// session.ts - 会话相关类型定义
// 定义会话（Session）的数据结构
export interface Session {
  id: string;       // 会话唯一标识符（thread_id）
  title: string;    // 会话显示标题
  updatedAt?: number; // 最近一次更新时间戳（毫秒），用于按时间分组
  pinned?: boolean;   // 是否置顶
}