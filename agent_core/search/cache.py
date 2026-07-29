# cache.py - Tavily 搜索结果与网页内容缓存
# 缓存命中时不消耗 Tavily 积分，避免重复调用 API
#
# 缓存目录结构：
#   web_cache/
#   ├── search/          # 搜索结果缓存
#   │   └── {query_md5}.json
#   └── pages/           # 网页内容缓存
#       └── {url_md5}.md
#
# 缓存有效期：
#   - 搜索结果：7 天
#   - 网页内容：30 天

import os
import json
import hashlib
import time
from typing import Optional, Any
from agent_core.config.settings import BASE_DIR
from agent_core.logger import get_logger

logger = get_logger(__name__)

# 缓存根目录（项目根目录下的 web_cache/）
CACHE_ROOT = os.path.join(BASE_DIR, "web_cache")
SEARCH_CACHE_DIR = os.path.join(CACHE_ROOT, "search")
PAGES_CACHE_DIR = os.path.join(CACHE_ROOT, "pages")

# 缓存有效期（秒）
SEARCH_CACHE_TTL = 7 * 24 * 3600   # 搜索结果 7 天
PAGES_CACHE_TTL = 30 * 24 * 3600   # 网页内容 30 天


def _ensure_dirs() -> None:
    """确保缓存目录存在"""
    os.makedirs(SEARCH_CACHE_DIR, exist_ok=True)
    os.makedirs(PAGES_CACHE_DIR, exist_ok=True)


def _md5(text: str) -> str:
    """计算字符串的 MD5 哈希，用作缓存文件名"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _is_expired(file_path: str, ttl: int) -> bool:
    """判断缓存文件是否过期

    判断依据：文件修改时间 + TTL 是否小于当前时间
    """
    if not os.path.exists(file_path):
        return True
    mtime = os.path.getmtime(file_path)
    return (time.time() - mtime) > ttl


# ==================== 搜索结果缓存 ====================

def get_search_cache(query: str) -> Optional[dict]:
    """读取搜索结果缓存

    参数:
        query: 搜索关键词

    返回:
        缓存的搜索结果字典；未命中或已过期返回 None
    """
    _ensure_dirs()
    cache_file = os.path.join(SEARCH_CACHE_DIR, f"{_md5(query)}.json")
    if _is_expired(cache_file, SEARCH_CACHE_TTL):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"搜索缓存命中: {query[:30]}")
        return data
    except Exception as e:
        logger.warning(f"读取搜索缓存失败: {e}")
        return None


def set_search_cache(query: str, data: dict) -> None:
    """写入搜索结果缓存

    参数:
        query: 搜索关键词
        data: 搜索结果字典
    """
    _ensure_dirs()
    cache_file = os.path.join(SEARCH_CACHE_DIR, f"{_md5(query)}.json")
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"搜索结果已缓存: {query[:30]}")
    except Exception as e:
        logger.warning(f"写入搜索缓存失败: {e}")


# ==================== 网页内容缓存 ====================

def get_page_cache(url: str) -> Optional[str]:
    """读取网页内容缓存

    参数:
        url: 网页 URL

    返回:
        缓存的网页内容（Markdown 字符串）；未命中或已过期返回 None
    """
    _ensure_dirs()
    cache_file = os.path.join(PAGES_CACHE_DIR, f"{_md5(url)}.md")
    if _is_expired(cache_file, PAGES_CACHE_TTL):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            content = f.read()
        logger.debug(f"网页缓存命中: {url[:50]}")
        return content
    except Exception as e:
        logger.warning(f"读取网页缓存失败: {e}")
        return None


def set_page_cache(url: str, content: str) -> None:
    """写入网页内容缓存

    参数:
        url: 网页 URL
        content: 网页内容（Markdown 字符串）
    """
    _ensure_dirs()
    cache_file = os.path.join(PAGES_CACHE_DIR, f"{_md5(url)}.md")
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(content)
        logger.debug(f"网页内容已缓存: {url[:50]}")
    except Exception as e:
        logger.warning(f"写入网页缓存失败: {e}")
