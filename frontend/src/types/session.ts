// session.ts - 会话相关类型定义
// 定义会话（Session）的数据结构
export interface Session {
  id: string;       // 会话唯一标识符（thread_id）
  title: string;    // 会话显示标题
}