// useMessageEdit.ts - 消息编辑组合式函数
// 处理用户消息的编辑功能：修改历史消息后重新发送，生成新的会话分支
import { ref, type Ref } from 'vue';
import type { Message } from '@/types/chat';
import { storage, STORAGE_KEYS } from '@/utils/storage';

/**
 * 消息编辑 Composable
 * 当用户编辑历史消息时，会：
 * 1. 截断编辑点之后的所有消息
 * 2. 生成新的 thread_id
 * 3. 将截断的历史保存到新 thread_id 下
 * 4. 更新 session 中的 thread_id
 * 5. 使用新内容重新发送消息
 *
 * @param messages 当前消息列表的响应式引用
 * @param handleSend 发送消息的回调
 * @param generateThreadId 生成新 thread_id 的函数
 * @param onUpdateSessionId 更新 session 中 thread_id 的回调
 * @param getCurrentThreadId 获取当前 thread_id 的函数
 */
export function useMessageEdit(
  messages: Ref<Message[]>,
  handleSend: (message: string) => Promise<void>,
  generateThreadId: () => string,
  onUpdateSessionId: (oldThreadId: string, newThreadId: string) => void,
  getCurrentThreadId: () => string
) {
  // 正在编辑的消息 ID
  const editingMessageId = ref<string | null>(null);
  // 编辑中的消息内容
  const editingContent = ref('');
  // 编辑保存中的加载状态
  const loading = ref(false);

  /**
   * 开始编辑：设置编辑目标消息并填入当前内容
   * @param messageId 要编辑的消息 ID
   */
  const startEdit = (messageId: string) => {
    if (loading.value) return;  // 正在保存时禁止再次编辑

    const msg = messages.value.find(m => m.id === messageId);
    if (!msg || msg.role !== 'user') return;  // 只能编辑用户消息

    editingMessageId.value = messageId;
    editingContent.value = msg.content;
  };

  /**
   * 取消编辑：重置编辑状态
   */
  const cancelEdit = () => {
    editingMessageId.value = null;
    editingContent.value = '';
  };

  /**
   * 保存编辑：截断历史、生成新会话、重新发送
   *
   * 核心流程：
   * 1. 找到编辑点位置
   * 2. 截断保留编辑点之前的消息（不含被编辑消息本身）
   * 3. 生成新的 thread_id 并保存截断历史
   * 4. 删除旧 thread_id 的本地缓存
   * 5. 更新 session 中的 thread_id 引用
   * 6. 使用新内容重新发送消息（AI 会基于截断后的上下文回复）
   *
   * @param messageId 被编辑的消息 ID
   */
  const saveEdit = async (messageId: string) => {
    if (loading.value) return;

    const newContent = editingContent.value.trim();
    if (!newContent) return;  // 空内容不保存

    const editIndex = messages.value.findIndex(m => m.id === messageId);
    if (editIndex === -1) return;

    const editedMessage = messages.value[editIndex];
    if (!editedMessage) return;

    const oldContent = editedMessage.content;
    if (oldContent === newContent) {
      cancelEdit();  // 内容未改变，直接取消
      return;
    }

    loading.value = true;
    // 保存旧 thread_id 和旧历史快照，以备回滚
    const oldThreadId = getCurrentThreadId();
    const oldHistorySnapshot = [...messages.value];
    const cleanHistory = messages.value.slice(0, editIndex);
    const newThreadId = generateThreadId();

    try {
      // 将截断的历史保存到新 thread_id 下
      storage.set(STORAGE_KEYS.MESSAGES(newThreadId), cleanHistory);
      // 删除旧 thread_id 的本地缓存
      storage.remove(STORAGE_KEYS.MESSAGES(oldThreadId));

      // 更新消息列表为截断后的历史
      messages.value = [...cleanHistory];

      // 更新 session 中的 thread_id 引用
      onUpdateSessionId(oldThreadId, newThreadId);
      cancelEdit();

      // 延迟一帧确保 UI 状态更新后再发送
      await new Promise(resolve => setTimeout(resolve, 0));
      // 使用编辑后的新内容发送消息
      await handleSend(newContent);
    } catch (error) {
      // handleSend 失败，回滚 thread_id 并恢复旧会话数据
      console.error('编辑消息发送失败，正在回滚:', error);
      // 回滚 session 中的 thread_id
      onUpdateSessionId(newThreadId, oldThreadId);
      // 恢复旧会话的存储数据
      storage.set(STORAGE_KEYS.MESSAGES(oldThreadId), oldHistorySnapshot);
      storage.remove(STORAGE_KEYS.MESSAGES(newThreadId));
      // 恢复消息列表
      messages.value = oldHistorySnapshot;
      // 恢复编辑状态，让用户可以重新尝试
      editingMessageId.value = messageId;
      editingContent.value = newContent;
    } finally {
      loading.value = false;
    }
  };

  // 对外暴露编辑状态和操作方法
  return {
    editingMessageId,
    editingContent,
    startEdit,
    cancelEdit,
    saveEdit
  };
}