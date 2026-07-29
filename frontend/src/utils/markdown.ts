// utils/markdown.ts - Markdown 渲染工具
// 封装 markdown-it + highlight.js，提供安全的 Markdown 渲染能力
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';

// 引入 highlight.js 的主题 CSS（在 main.ts 中已引入 CSS，这里保留注释说明）
// import 'highlight.js/styles/github.css';
// import 'highlight.js/styles/github-dark.css';

/** 工具元数据：图标、中文名、描述等 */
export interface ToolMeta {
  name: string;
  icon: string; // Element Plus 图标名
  label: string; // 中文名
  description: string;
  category: ToolCategory;
}

/** 工具分类（需与 types/chat.ts 中的 ToolCategory 保持一致） */
export type ToolCategory =
  | 'web'
  | 'file'
  | 'code'
  | 'knowledge'
  | 'memory'
  | 'system'
  | 'other';

/** 把历史分类名统一映射到新分类 */
const normalizeCategory = (
  c: string | undefined
): ToolCategory => {
  switch (c) {
    case 'search':
    case 'web':
      return 'web';
    case 'weather':
      return 'system';
    case 'knowledge':
    case 'file':
    case 'code':
    case 'memory':
    case 'system':
    case 'other':
      return c as ToolCategory;
    default:
      return 'other';
  }
};

export const TOOL_META: Record<string, ToolMeta> = {
  get_current_time: {
    name: 'get_current_time',
    icon: 'Clock',
    label: '获取当前时间',
    description: '查询当前日期与时间',
    category: normalizeCategory('system'),
  },
  search_personal_knowledge: {
    name: 'search_personal_knowledge',
    icon: 'Collection',
    label: '检索个人知识库',
    description: '在本地知识库中查找相关文档',
    category: normalizeCategory('knowledge'),
  },
  get_weather: {
    name: 'get_weather',
    icon: 'Sunny',
    label: '查询天气',
    description: '获取指定城市的实时天气',
    category: normalizeCategory('system'),
  },
  save_user_memory: {
    name: 'save_user_memory',
    icon: 'Cpu',
    label: '保存记忆',
    description: '把用户的关键信息记下来',
    category: normalizeCategory('memory'),
  },
  recall_user_memory: {
    name: 'recall_user_memory',
    icon: 'Cpu',
    label: '回忆信息',
    description: '从记忆库中检索相关信息',
    category: normalizeCategory('memory'),
  },
  list_user_memories: {
    name: 'list_user_memories',
    icon: 'Cpu',
    label: '列出所有记忆',
    description: '查看全部已保存的记忆',
    category: normalizeCategory('memory'),
  },
  delete_user_memory: {
    name: 'delete_user_memory',
    icon: 'Cpu',
    label: '删除记忆',
    description: '移除指定的记忆条目',
    category: normalizeCategory('memory'),
  },
  clear_user_memories: {
    name: 'clear_user_memories',
    icon: 'Cpu',
    label: '清空记忆',
    description: '清除所有已保存的记忆',
    category: normalizeCategory('memory'),
  },
  read_file: {
    name: 'read_file',
    icon: 'Document',
    label: '读取文件',
    description: '读取本地文件内容',
    category: normalizeCategory('file'),
  },
  write_file: {
    name: 'write_file',
    icon: 'EditPen',
    label: '写入文件',
    description: '把内容写入到指定文件',
    category: normalizeCategory('file'),
  },
  list_directory: {
    name: 'list_directory',
    icon: 'FolderOpened',
    label: '浏览目录',
    description: '列出目录下的文件和文件夹',
    category: normalizeCategory('file'),
  },
  search_files: {
    name: 'search_files',
    icon: 'Search',
    label: '搜索文件',
    description: '按关键词在目录中搜索文件',
    category: normalizeCategory('file'),
  },
  execute_python: {
    name: 'execute_python',
    icon: 'Files',
    label: '执行 Python 代码',
    description: '在安全沙箱中运行 Python 代码',
    category: normalizeCategory('code'),
  },
  search_web: {
    name: 'search_web',
    icon: 'Search',
    label: '网络搜索',
    description: '通过搜索引擎查询网络信息',
    category: normalizeCategory('web'),
  },
  read_webpage: {
    name: 'read_webpage',
    icon: 'Link',
    label: '读取网页',
    description: '抓取并提取指定 URL 的网页内容',
    category: normalizeCategory('web'),
  },
};

/** 获取工具元信息，找不到时返回通用信息 */
export const getToolMeta = (name: string): ToolMeta => {
  return (
    TOOL_META[name] ?? {
      name,
      icon: 'MagicStick',
      label: name,
      description: '调用自定义工具',
      category: 'system',
    }
  );
};

/** 创建 markdown-it 实例 */
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight(str, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    try {
      const highlighted = hljs.highlight(str, { language, ignoreIllegals: true }).value;
      return (
        `<pre class="hljs code-block" data-lang="${language}">` +
        `<code class="language-${language}">${highlighted}</code>` +
        `</pre>`
      );
    } catch {
      return `<pre class="hljs code-block" data-lang="plaintext"><code class="language-plaintext">${md.utils.escapeHtml(str)}</code></pre>`;
    }
  },
});

/** 安全地渲染 Markdown 为 HTML（已开启 XSS 防护：html=false） */
export const renderMarkdown = (text: string): string => {
  if (!text) return '';
  return md.render(text);
};

/**
 * 格式化工具入参：
 * - 支持 JSON 字符串、已解析对象、纯字符串、数字等任意类型
 * - 返回类型标记方便模板选择 pre/code 或普通 div
 */
export const formatToolArgs = (args: unknown): { type: 'json' | 'text'; value: string } => {
  if (args === undefined || args === null) return { type: 'text', value: '' };
  if (typeof args === 'string') {
    if (!args) return { type: 'text', value: '' };
    // 字符串可能本身就是 JSON，尝试美化
    try {
      const parsed = JSON.parse(args);
      return { type: 'json', value: JSON.stringify(parsed, null, 2) };
    } catch {
      return { type: 'text', value: args };
    }
  }
  if (typeof args === 'number' || typeof args === 'boolean') {
    return { type: 'text', value: String(args) };
  }
  // 对象 / 数组：美化 JSON
  try {
    return { type: 'json', value: JSON.stringify(args, null, 2) };
  } catch {
    return { type: 'text', value: Object.prototype.toString.call(args) };
  }
};

/**
 * 把任意类型的「结果」归一化为字符串：
 * - 结构化对象 → 美化 JSON
 * - 字符串 → 原样（字符串可能本身是 JSON，需要时可解析美化）
 */
export const stringifyResult = (result: unknown): string => {
  if (result === undefined || result === null) return '';
  if (typeof result === 'string') return result;
  if (typeof result === 'number' || typeof result === 'boolean') return String(result);
  try {
    return JSON.stringify(result, null, 2);
  } catch {
    return Object.prototype.toString.call(result);
  }
};

/**
 * 判断字符串是不是 JSON 形状（以 { 或 [ 开头，且是美化后的 JSON）
 * 仅用于模板里是否展示为代码块
 */
export const looksLikeJson = (text: string): boolean => {
  if (!text) return false;
  const t = text.trim();
  return (t.startsWith('{') && t.endsWith('}')) || (t.startsWith('[') && t.endsWith(']'));
};

/** 把错误对象归一化成可读字符串 */
export const formatError = (err: { type?: string; message: string; stack?: string } | string | undefined | null): string => {
  if (!err) return '';
  if (typeof err === 'string') return err;
  const parts: string[] = [];
  if (err.type) parts.push(`[${err.type}]`);
  if (err.message) parts.push(err.message);
  const head = parts.join(' ');
  if (err.stack) return head + '\n\n' + err.stack;
  return head;
};

/** 复制文本到剪贴板，返回是否成功 */
export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    // Fallback for non-secure context
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(textarea);
    return ok;
  } catch {
    return false;
  }
};

/** 把毫秒时间戳格式化为 HH:mm 或 YYYY-MM-DD HH:mm */
export const formatTime = (timestamp?: number, withDate = false): string => {
  if (!timestamp) return '';
  const d = new Date(timestamp);
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  const time = `${hh}:${mm}`;
  if (!withDate) return time;
  const yyyy = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mo}-${dd} ${time}`;
};

/** 计算工具调用耗时（ms），返回格式化字符串 */
export const formatDuration = (startMs?: number, endMs?: number): string => {
  if (!startMs) return '';
  const end = endMs ?? Date.now();
  const duration = end - startMs;
  if (duration < 1000) return `${duration} ms`;
  return `${(duration / 1000).toFixed(1)} s`;
};
