# search_tool.py - 联网搜索与网页阅读工具
# 基于 Tavily 官方 Python SDK，供 Agent 直接调用
#
# 两个工具：
#   1. search_web：搜索互联网，返回标题、链接、摘要
#   2. read_webpage：读取指定网页的完整内容（清洗后）
#
# 积分优化：
#   - 搜索结果缓存7天，网页内容缓存30天，命中缓存不消耗积分
#   - 默认 basic 模式，必要时才升级 advanced
#
# 内容安全：
#   - 对搜索结果进行内容清洗（去除控制字符、零宽字符）
#   - 截断过长内容，降低触发 LLM 内容安全检测的概率
#   - 新闻类查询自动使用 topic="news" + time_range="day"

import re
from langchain_core.tools import tool
from agent_core.search.tavily_engine import get_engine
from agent_core.logger import get_logger

logger = get_logger(__name__)

# 内容安全相关常量
MAX_CONTENT_LENGTH = 500  # 每条搜索结果摘要最大字符数


# ==================== 内容清洗工具 ====================

def _sanitize_text(text: str) -> str:
    """清洗文本内容，去除可能导致 LLM API 内容安全检测失败的字符

    清洗规则：
    1. 去除 Unicode 控制字符（零宽空格、零宽连接符、方向控制符等）
    2. 去除不可打印的 ASCII 控制字符（保留换行、制表符）
    3. 规范化连续空白字符
    4. 去除首尾空白
    """
    if not text:
        return ""

    # 1. 去除零宽字符和其他控制字符（保留 \n \r \t）
    # 零宽空格 U+200B, 零宽连接符 U+200D, 零宽非连接符 U+200C 等
    text = re.sub(r'[\u200b\u200c\u200d\u2060\ufeff\u180e]', '', text)
    # 去除方向控制符（RTL/LTR 标记）
    text = re.sub(r'[\u202a-\u202e\u2066-\u2069]', '', text)
    # 去除不可打印 ASCII 控制字符（保留 \n \r \t）
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # 2. 规范化连续空白
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 3. 去除首尾空白
    return text.strip()


def _truncate_content(text: str, max_len: int = MAX_CONTENT_LENGTH) -> str:
    """截断过长内容，保留完整语义"""
    if not text or len(text) <= max_len:
        return text
    # 在最后一个完整句子处截断，避免截到一半
    truncated = text[:max_len]
    # 尝试找到最后一个句号、问号或感叹号
    for sep in ['。', '？', '！', '. ', '? ', '! ', '\n']:
        idx = truncated.rfind(sep)
        if idx > max_len * 0.5:  # 至少保留一半内容
            return truncated[:idx + 1]
    return truncated + "..."


# ==================== 智能参数推断 ====================

# 新闻类查询关键词（用于自动推断 topic="news"）
_NEWS_KEYWORDS = {
    '新闻', '热点', '时事', '头条', '资讯', '报道', '事件', '突发',
    'today', 'news', 'headline', 'breaking', 'latest',
    '今日', '今天', '最近', '最新', '实时', '热点新闻',
}

# 金融类查询关键词
_FINANCE_KEYWORDS = {
    '股票', '股市', '行情', '基金', '债券', '期货', '外汇', '加密货币',
    'bitcoin', 'stock', 'market', 'finance', 'trading',
}


def _infer_search_params(query: str) -> dict:
    """根据查询内容智能推断搜索参数（topic 和 time_range）

    返回:
        dict: 包含 topic 和 time_range 的字典
    """
    q_lower = query.lower()
    params = {"topic": "general", "time_range": None}

    # 判断是否包含新闻关键词
    is_news = any(kw in q_lower for kw in _NEWS_KEYWORDS)
    is_finance = any(kw in q_lower for kw in _FINANCE_KEYWORDS)

    if is_finance:
        params["topic"] = "finance"
    elif is_news:
        params["topic"] = "news"

    # 新闻/热点类查询自动限制为最近一天
    if is_news or is_finance:
        params["time_range"] = "day"

    logger.debug(f"查询 '{query}' 推断参数: topic={params['topic']}, time_range={params['time_range']}")
    return params


# ==================== 工具定义 ====================

@tool
def search_web(query: str, search_depth: str = "basic") -> str:
    """搜索互联网获取实时信息。当需要查询最新资讯、新闻、数据、教程等时使用。

    参数:
        query: 搜索关键词
        search_depth: 搜索深度，"basic"（1积分）或"advanced"（2积分），默认"basic"

    返回格式：
        搜索结果列表，每条含标题、链接、摘要，末尾附积分消耗与来源链接汇总。
        重复搜索同一关键词不消耗积分（命中缓存）。
        新闻/热点类查询会自动限制为最近一天的结果。
    """
    engine = get_engine()

    # 智能推断搜索参数（topic、time_range）
    inferred = _infer_search_params(query)

    result = engine.search(
        query,
        search_depth=search_depth,
        topic=inferred["topic"],
        time_range=inferred["time_range"],
    )

    # 错误处理：直接返回友好提示，物理中断
    if result.get("error"):
        return result["error"]

    results = result.get("results", [])
    if not results:
        return f"🔍 搜索: {query}\n\n未找到相关信息。"

    # 按要求格式化输出（内容清洗 + 截断）
    lines = [f"🔍 搜索: {query}"]
    cached_tag = "（命中缓存，未消耗积分）" if result.get("cached") else ""
    topic_tag = f" [类别: {inferred['topic']}]" if inferred["topic"] != "general" else ""
    time_tag = f" [时间: 最近一天]" if inferred["time_range"] == "day" else ""
    lines.append(f"找到 {len(results)} 条结果{topic_tag}{time_tag}{cached_tag}：\n")

    for i, item in enumerate(results, 1):
        title = _sanitize_text(item.get("title", "无标题"))
        url = _sanitize_text(item.get("url", ""))
        # 清洗并截断内容，避免触发 LLM 内容安全检测
        content_raw = item.get("content", "无摘要")
        content = _truncate_content(_sanitize_text(content_raw))

        lines.append(f"{i}. {title}")
        lines.append(f"   📎 {url}")
        lines.append(f"   📝 {content}\n")

    # 积分消耗汇总
    credits = result.get("credits_used", 0)
    lines.append("---")
    if result.get("cached"):
        lines.append("💡 本次命中缓存，未消耗积分。")
    else:
        lines.append(f"💡 共消耗 {credits} 积分。如需更深入的内容，可指定 search_depth=\"advanced\"。")

    # 来源链接汇总
    lines.append("\n📎 来源链接汇总：")
    for i, item in enumerate(results, 1):
        title = _sanitize_text(item.get("title", "无标题"))
        url = _sanitize_text(item.get("url", ""))
        lines.append(f"  {i}. [{title}]({url})")

    # 低积分警告
    warning = engine._credit_warning()
    if warning:
        lines.append(warning)

    return "\n".join(lines)


@tool
def read_webpage(url: str) -> str:
    """读取指定网页的完整内容（清洗后）。当需要详细了解某个网页的内容时使用。

    参数:
        url: 网页 URL

    返回格式：
        清洗后的网页正文内容（Markdown 格式）。
        内容已缓存30天，下次读取同一 URL 不消耗积分。
    """
    # 简单 URL 校验
    if not url or not url.strip():
        return "❌ 请提供有效的网页 URL。"
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return "❌ URL 必须以 http:// 或 https:// 开头。"

    engine = get_engine()
    result = engine.extract(url)

    # 错误处理：直接返回友好提示，物理中断
    if result.get("error"):
        return result["error"]

    results = result.get("results", [])
    failed = result.get("failed_results", [])

    if not results:
        if failed:
            return f"❌ 网页内容提取失败：{failed[0].get('error', '未知原因')}"
        return f"❌ 未能从 {url} 提取到内容。"

    # 取第一个结果（单 URL 提取）并清洗内容
    content_raw = results[0].get("content", "")
    if not content_raw:
        return f"❌ 提取到的网页内容为空：{url}"

    content = _sanitize_text(content_raw)

    # 按要求格式化输出
    cached_tag = "（命中缓存，未消耗积分）" if result.get("cached") else ""
    lines = [f"📄 网页内容：{url}{cached_tag}"]
    lines.append("---")
    lines.append(content)
    lines.append("---")

    if result.get("cached"):
        lines.append("💡 本次命中缓存，未消耗积分。")
    else:
        credits = result.get("credits_used", 0)
        lines.append(f"💡 内容已缓存，下次读取将不消耗积分。本次消耗约 {credits} 积分。")

    # 低积分警告
    warning = engine._credit_warning()
    if warning:
        lines.append(warning)

    return "\n".join(lines)
