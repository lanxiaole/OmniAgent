# tavily_engine.py - Tavily 联网搜索与网页内容提取核心引擎
# 基于 Tavily 官方 Python SDK（https://docs.tavily.com/sdk/python/reference）
#
# 核心设计原则：
#   1. 积分精打细算：默认 basic 搜索（1积分/次），extract 基础模式（每5个成功URL消耗1积分）
#   2. 来源可追溯：返回结果包含标题、URL、摘要
#   3. 智能缓存：搜索结果缓存7天，网页内容缓存30天，命中缓存不消耗积分
#   4. 物理中断：积分不足或API调用失败时，代码层面直接返回友好提示，禁止继续执行

from typing import Union
from agent_core.config.settings import (
    TAVILY_API_KEY,
    TAVILY_SEARCH_DEPTH,
    TAVILY_EXTRACT_DEPTH,
    TAVILY_MAX_RESULTS,
)
from agent_core.logger import get_logger
from agent_core.search import cache

logger = get_logger(__name__)

# Tavily 每月免费积分额度
FREE_CREDITS_PER_MONTH = 1000
# 积分不足警告阈值
LOW_CREDITS_WARNING_THRESHOLD = 100


class TavilyEngine:
    """Tavily 搜索与内容提取引擎

    封装 TavilyClient 的 search() 和 extract() 方法，提供：
    - 搜索结果缓存（7天有效期）
    - 网页内容缓存（30天有效期）
    - 积分使用统计与低积分警告
    - 友好的异常处理（API Key 无效、积分不足、网络超时）
    """

    def __init__(self, api_key: str = None):
        """初始化 Tavily 引擎

        参数:
            api_key: Tavily API Key，未传入则从配置读取
        """
        self.api_key = api_key or TAVILY_API_KEY
        # 已消耗积分（本次会话累计，仅作低积分提醒参考）
        self.credits_used = 0
        self._client = None  # 延迟初始化，避免未配置时 import 报错

    def _get_client(self):
        """延迟初始化 TavilyClient，避免未配置 API Key 时模块加载失败"""
        if self._client is not None:
            return self._client

        if not self.api_key:
            # 物理中断：未配置 API Key 直接返回 None，由调用方处理
            return None

        # 按官方文档写法初始化客户端
        from tavily import TavilyClient
        self._client = TavilyClient(api_key=self.api_key)
        return self._client

    def _record_credits(self, credits: int) -> None:
        """记录积分消耗"""
        self.credits_used += credits
        logger.debug(f"消耗 {credits} 积分，本次会话累计消耗: {self.credits_used}")

    def _credit_warning(self) -> str:
        """生成低积分警告提示（剩余积分接近用完时）"""
        # 估算剩余积分（仅作提醒，实际以官方账户为准）
        remaining = FREE_CREDITS_PER_MONTH - self.credits_used
        if remaining < LOW_CREDITS_WARNING_THRESHOLD:
            return f"\n\n⚠️ 积分提醒：本次会话已消耗约 {self.credits_used} 积分，月度免费额度可能所剩不多。"
        return ""

    def search(
        self,
        query: str,
        search_depth: str = None,
        max_results: int = None,
        time_range: str = None,
        topic: str = "general",
    ) -> dict:
        """执行互联网搜索

        按 Tavily 官方文档调用 TavilyClient.search()，结果缓存7天。

        参数:
            query: 搜索关键词
            search_depth: 搜索深度，"basic"（1积分）或"advanced"（2积分），默认从配置读取
            max_results: 最大结果数（0-20），默认从配置读取
            time_range: 时间范围，"day"/"week"/"month"/"year"，默认 None（不限）
            topic: 搜索类别，"general"/"news"/"finance"，默认 "general"

        返回:
            dict，包含字段：
                - query: 搜索关键词
                - results: 结果列表，每项含 title/url/content/score
                - response_time: 响应耗时
                - cached: 是否来自缓存
                - credits_used: 本次消耗积分
                - error: 错误提示（成功时为空字符串）
        """
        # 参数默认值从配置读取
        if search_depth is None:
            search_depth = TAVILY_SEARCH_DEPTH or "basic"
        if max_results is None:
            max_results = TAVILY_MAX_RESULTS or 5

        # 标准化返回结构
        empty_result = {
            "query": query,
            "results": [],
            "response_time": 0,
            "cached": False,
            "credits_used": 0,
            "error": "",
        }

        # 1. 检查 API Key
        if not self.api_key:
            empty_result["error"] = "❌ Tavily API Key 无效，请检查 .env 配置。"
            return empty_result

        # 2. 检查缓存（命中则不消耗积分）
        cached = cache.get_search_cache(query)
        if cached is not None:
            cached["cached"] = True
            cached["credits_used"] = 0
            cached["error"] = ""
            return cached

        # 3. 调用 Tavily API
        client = self._get_client()
        if client is None:
            empty_result["error"] = "❌ Tavily 客户端初始化失败，请检查 API Key 配置。"
            return empty_result

        try:
            logger.info(f"Tavily 搜索: {query} (depth={search_depth}, max={max_results}, time_range={time_range}, topic={topic})")
            # 按官方文档调用 search()，传入 time_range 和 topic 优化新闻类查询
            search_kwargs = {
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "topic": topic,
            }
            if time_range:
                search_kwargs["time_range"] = time_range
            response = client.search(**search_kwargs)

            # 计算积分消耗：basic=1，advanced=2
            credits = 2 if search_depth == "advanced" else 1
            self._record_credits(credits)

            # 提取并标准化结果
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0),
                })

            result = {
                "query": response.get("query", query),
                "results": results,
                "response_time": response.get("response_time", 0),
                "cached": False,
                "credits_used": credits,
                "error": "",
            }

            # 写入缓存
            cache.set_search_cache(query, result)
            return result

        except Exception as e:
            return self._handle_exception(e, empty_result)

    def extract(self, urls: Union[str, list], extract_depth: str = None) -> dict:
        """提取网页内容

        按 Tavily 官方文档调用 TavilyClient.extract()，提取并清洗网页内容。
        单个 URL 或 URL 列表（最多20个）均可。结果缓存30天。

        参数:
            urls: 单个 URL 字符串或 URL 列表（最多20个）
            extract_depth: 提取深度，"basic"（每5个成功URL消耗1积分）或"advanced"（每5个消耗2积分），默认从配置读取

        返回:
            dict，包含字段：
                - results: 成功提取列表，每项含 url/content
                - failed_results: 失败列表，每项含 url/error
                - response_time: 响应耗时
                - cached: 是否来自缓存
                - credits_used: 本次消耗积分
                - error: 错误提示（成功时为空字符串）
        """
        if extract_depth is None:
            extract_depth = TAVILY_EXTRACT_DEPTH or "basic"

        # 统一转为列表处理
        if isinstance(urls, str):
            urls_list = [urls]
        else:
            urls_list = list(urls)

        empty_result = {
            "results": [],
            "failed_results": [],
            "response_time": 0,
            "cached": False,
            "credits_used": 0,
            "error": "",
        }

        # 1. 检查 API Key
        if not self.api_key:
            empty_result["error"] = "❌ Tavily API Key 无效，请检查 .env 配置。"
            return empty_result

        # 2. 单 URL 时优先查缓存（列表提取不查缓存，避免部分命中逻辑复杂）
        if len(urls_list) == 1:
            cached_content = cache.get_page_cache(urls_list[0])
            if cached_content is not None:
                return {
                    "results": [{"url": urls_list[0], "content": cached_content}],
                    "failed_results": [],
                    "response_time": 0,
                    "cached": True,
                    "credits_used": 0,
                    "error": "",
                }

        # 3. 调用 Tavily API
        client = self._get_client()
        if client is None:
            empty_result["error"] = "❌ Tavily 客户端初始化失败，请检查 API Key 配置。"
            return empty_result

        try:
            logger.info(f"Tavily 提取: {len(urls_list)} 个URL (depth={extract_depth})")
            # 按官方文档调用 extract()
            response = client.extract(
                urls=urls_list,
                extract_depth=extract_depth,
            )

            # 提取成功结果
            results = []
            for item in response.get("results", []):
                url = item.get("url", "")
                content = item.get("raw_content", "")
                results.append({"url": url, "content": content})
                # 单 URL 时写入缓存
                if len(urls_list) == 1 and url and content:
                    cache.set_page_cache(url, content)

            # 提取失败结果
            failed_results = []
            for item in response.get("failed_results", []):
                failed_results.append({
                    "url": item.get("url", ""),
                    "error": item.get("error", ""),
                })

            # 计算积分：basic 每个成功URL消耗0.2积分（5个=1），advanced每个0.4（5个=2）
            # 官方按"每5个成功URL"计费，这里按比例估算
            success_count = len(results)
            if extract_depth == "advanced":
                credits = (success_count * 2 + 4) // 5  # 向上取整
            else:
                credits = (success_count + 4) // 5  # 向上取整
            self._record_credits(credits)

            return {
                "results": results,
                "failed_results": failed_results,
                "response_time": response.get("response_time", 0),
                "cached": False,
                "credits_used": credits,
                "error": "",
            }

        except Exception as e:
            return self._handle_exception(e, empty_result)

    def search_with_extract(self, query: str, search_depth: str = None, max_results: int = None) -> dict:
        """组合调用：先搜索，再对结果 URL 提取完整内容

        智能降级：如果 extract() 失败（如积分不足），自动降级为只返回搜索结果摘要。

        参数:
            query: 搜索关键词
            search_depth: 搜索深度，默认从配置读取
            max_results: 最大结果数，默认从配置读取

        返回:
            dict，包含字段：
                - query: 搜索关键词
                - results: 搜索结果列表（含摘要）
                - extracted: 提取的网页内容列表，每项含 url/content
                - response_time: 总响应耗时
                - cached: 是否来自缓存
                - credits_used: 本次总消耗积分
                - error: 错误提示
                - degraded: 是否发生降级
        """
        # 1. 先执行搜索
        search_result = self.search(query, search_depth=search_depth, max_results=max_results)
        if search_result.get("error"):
            # 搜索就失败了，直接返回
            return {
                "query": query,
                "results": [],
                "extracted": [],
                "response_time": 0,
                "cached": False,
                "credits_used": 0,
                "error": search_result["error"],
                "degraded": False,
            }

        # 2. 对搜索结果 URL 提取完整内容
        urls = [r["url"] for r in search_result.get("results", []) if r.get("url")]
        if not urls:
            return {
                "query": query,
                "results": search_result.get("results", []),
                "extracted": [],
                "response_time": search_result.get("response_time", 0),
                "cached": search_result.get("cached", False),
                "credits_used": search_result.get("credits_used", 0),
                "error": "",
                "degraded": False,
            }

        extract_result = self.extract(urls, extract_depth=TAVILY_EXTRACT_DEPTH or "basic")

        # 3. 智能降级：extract 失败时只返回搜索摘要
        if extract_result.get("error"):
            logger.warning(f"提取失败，降级为仅返回搜索摘要: {extract_result['error']}")
            return {
                "query": query,
                "results": search_result.get("results", []),
                "extracted": [],
                "response_time": search_result.get("response_time", 0),
                "cached": search_result.get("cached", False),
                "credits_used": search_result.get("credits_used", 0),
                "error": "",
                "degraded": True,
            }

        return {
            "query": query,
            "results": search_result.get("results", []),
            "extracted": extract_result.get("results", []),
            "response_time": search_result.get("response_time", 0) + extract_result.get("response_time", 0),
            "cached": search_result.get("cached", False),
            "credits_used": search_result.get("credits_used", 0) + extract_result.get("credits_used", 0),
            "error": "",
            "degraded": False,
        }

    def _handle_exception(self, e: Exception, result: dict) -> dict:
        """统一异常处理，将异常转换为友好提示（物理中断，禁止继续执行）

        判断依据：异常消息文本与类型，覆盖 Tavily SDK 常见错误场景
        """
        err_msg = str(e).lower()
        logger.error(f"Tavily API 异常: {type(e).__name__}: {e}")

        # 1. API Key 无效（401 / unauthorized / invalid api key）
        if any(kw in err_msg for kw in ["401", "unauthorized", "invalid api key", "api key"]):
            result["error"] = "❌ Tavily API Key 无效，请检查 .env 配置。"
            return result

        # 2. 积分不足（402 / payment required / credits / quota / insufficient）
        if any(kw in err_msg for kw in ["402", "payment required", "credit", "quota", "insufficient", "limit reached"]):
            result["error"] = "⚠️ Tavily 积分已用尽，请等待下个月重置或充值。"
            return result

        # 3. 网络超时
        if any(kw in err_msg for kw in ["timeout", "timed out"]) or "timeout" in type(e).__name__.lower():
            result["error"] = "⏱️ 请求超时，请稍后重试。"
            return result

        # 4. 网络连接错误
        if any(kw in err_msg for kw in ["connection", "network", "unreachable", "refused"]):
            result["error"] = "❌ 网络连接失败，请检查网络后重试。"
            return result

        # 5. 其他未知错误
        result["error"] = f"❌ Tavily 请求失败: {type(e).__name__}: {str(e)}"
        return result


# ==================== 单例引擎 ====================

_engine_instance: TavilyEngine = None


def get_engine() -> TavilyEngine:
    """获取全局 TavilyEngine 单例（延迟初始化）

    使用单例避免重复创建客户端，并集中统计积分消耗
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = TavilyEngine()
    return _engine_instance
