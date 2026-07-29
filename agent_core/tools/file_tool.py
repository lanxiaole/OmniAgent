# 文件系统工具模块
# 提供基础的文件读写、目录浏览和文件搜索能力

import os
import fnmatch
from pathlib import Path
from langchain_core.tools import tool
from agent_core.config.settings import SYSTEM_DIRS
from agent_core.logger import get_logger

logger = get_logger(__name__)

# 默认系统目录黑名单
DEFAULT_SYSTEM_DIRS = [
    "/etc",
    "/System",
    "/boot",
    "/usr",
    "/bin",
    "/sbin",
    "/var",
    "/Library",
    "/Applications",
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\ProgramData",
    "C:\\Users\\Public",
    "C:\\Windows\\System32",
]

# 支持的文本文件扩展名
TEXT_EXTENSIONS = {".txt", ".py", ".md", ".json", ".csv", ".yaml", ".yml", ".xml", ".html", ".css", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".cpp", ".h", ".sql", ".log"}

# 需要跳过的隐藏目录和文件
HIDDEN_PATTERNS = {".git", "__pycache__", ".venv", "node_modules", ".egg-info", ".dist-info", ".idea", ".vscode", ".pytest_cache", ".tox", ".mypy_cache"}


def _get_system_dirs() -> list[str]:
    """获取系统目录黑名单"""
    if SYSTEM_DIRS:
        return [d.strip() for d in SYSTEM_DIRS.split(",")]
    return DEFAULT_SYSTEM_DIRS


def _is_system_directory(path: str) -> bool:
    """检查路径是否在系统目录内"""
    system_dirs = _get_system_dirs()
    abs_path = os.path.abspath(path).lower()
    for sys_dir in system_dirs:
        if abs_path.startswith(sys_dir.lower()):
            return True
    return False


def _safe_path(path: str) -> dict:
    """
    将路径转换为绝对路径并进行安全检查

    支持 `~` 作为用户主目录的缩写（如 ~/Desktop、~\Downloads 等）。

    返回:
        dict: {"absolute_path": str, "exists": bool, "is_file": bool, "is_dir": bool, "is_system": bool, "warning": str}
    """
    try:
        # 先展开 ~ 为用户主目录，再转绝对路径
        # 这样 ~/Desktop 会被正确解析为 C:\Users\xxx\Desktop，而不是项目根目录\~\Desktop
        expanded = os.path.expanduser(path)
        abs_path = os.path.abspath(expanded)
        exists = os.path.exists(abs_path)
        is_file = os.path.isfile(abs_path)
        is_dir = os.path.isdir(abs_path)
        is_system = _is_system_directory(abs_path)
        warning = ""
        
        if is_system:
            warning = f"警告：该路径位于系统目录内，操作前请确认。"
        
        return {
            "absolute_path": abs_path,
            "exists": exists,
            "is_file": is_file,
            "is_dir": is_dir,
            "is_system": is_system,
            "warning": warning,
        }
    
    except Exception as e:
        logger.error(f"路径解析失败: {e}")
        return {
            "absolute_path": path,
            "exists": False,
            "is_file": False,
            "is_dir": False,
            "is_system": False,
            "warning": f"❌ 路径解析失败: {e}",
        }


def _format_size(bytes_size: int) -> str:
    """格式化文件大小"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    else:
        return f"{bytes_size / (1024 * 1024):.2f} MB"


def _is_hidden(name: str) -> bool:
    """检查是否是隐藏文件或目录"""
    return name in HIDDEN_PATTERNS or name.startswith(".")


@tool
def read_file(file_path: str, start_line: int = 0, end_line: int | None = None) -> str:
    """读取文本文件的内容，支持分页。
    
    参数:
        file_path: 文件路径
        start_line: 起始行（从0开始），默认0
        end_line: 结束行（不包含），默认None表示全部读取
        
    调用示例:
    - 用户: "读取 agent_core/config/settings.py" -> 调用 read_file("agent_core/config/settings.py")
    - 用户: "继续读取第500行之后的内容" -> 调用 read_file("agent_core/config/settings.py", start_line=500)
    - 用户: "读取第100到200行" -> 调用 read_file("agent_core/config/settings.py", start_line=100, end_line=200)
    """
    try:
        safe_info = _safe_path(file_path)
        
        if safe_info["warning"]:
            return f"⚠️ {safe_info['warning']}"
        
        if not safe_info["exists"]:
            return f"❌ 文件不存在: {safe_info['absolute_path']}"
        
        if not safe_info["is_file"]:
            return f"❌ 不是文件: {safe_info['absolute_path']}"
        
        file_ext = os.path.splitext(safe_info["absolute_path"])[1].lower()
        if file_ext not in TEXT_EXTENSIONS:
            return f"❌ 该文件不是纯文本格式（扩展名: {file_ext}），请使用专用文档解析工具。"
        
        with open(safe_info["absolute_path"], "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        if end_line is None:
            if total_lines <= 500:
                content = "".join(lines)
                return f"✅ 文件内容 ({safe_info['absolute_path']}, 共 {total_lines} 行):\n\n{content}"
            else:
                content = "".join(lines[:500])
                return f"✅ 文件内容 ({safe_info['absolute_path']}, 共 {total_lines} 行，已返回前 500 行):\n\n{content}\n\n📌 文件共 {total_lines} 行，已返回前 500 行。你可以通过 start_line 和 end_line 参数阅读其他部分。"
        else:
            start_line = max(0, start_line)
            end_line = min(total_lines, end_line)
            
            if start_line >= end_line:
                return f"❌ 无效的行范围：start_line ({start_line}) >= end_line ({end_line})"
            
            content = "".join(lines[start_line:end_line])
            return f"✅ 文件内容 ({safe_info['absolute_path']}, 第 {start_line + 1} 到 {end_line} 行):\n\n{content}"
    
    except UnicodeDecodeError:
        return f"❌ 该文件不是纯文本格式，无法解码。"
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return f"❌ 读取文件失败: {e}"


@tool
def write_file(file_path: str, content: str) -> str:
    """将内容写入文件，如果文件已存在则覆盖。
    
    参数:
        file_path: 文件路径
        content: 要写入的内容
        
    调用示例:
    - 用户: "在下载目录写一个 test.txt，内容是 Hello" -> 调用 write_file("~/Downloads/test.txt", "Hello")
    - 用户: "把这段代码保存到 main.py" -> 调用 write_file("main.py", "代码内容")
    """
    try:
        safe_info = _safe_path(file_path)
        
        if safe_info["is_system"]:
            return f"⚠️ 警告：目标路径位于系统目录内（{safe_info['absolute_path']}），禁止写入操作。"
        
        parent_dir = os.path.dirname(safe_info["absolute_path"])
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            logger.info(f"创建目录: {parent_dir}")
        
        with open(safe_info["absolute_path"], "w", encoding="utf-8") as f:
            f.write(content)
        
        char_count = len(content)
        logger.info(f"写入文件成功: {safe_info['absolute_path']}, {char_count} 字符")
        return f"✅ 文件写入成功: {safe_info['absolute_path']}（{char_count} 字符）"
    
    except Exception as e:
        logger.error(f"写入文件失败: {e}")
        return f"❌ 写入文件失败: {e}"


@tool
def list_directory(dir_path: str = ".", recursive: bool = False, max_depth: int = 1) -> str:
    """列出目录内容，支持浅层或递归遍历。
    
    参数:
        dir_path: 目录路径，默认当前目录
        recursive: 是否递归遍历，默认False
        max_depth: 递归最大深度，默认1
        
    调用示例:
    - 用户: "看看桌面有什么" -> 调用 list_directory("~/Desktop")
    - 用户: "递归列出项目目录下的所有文件" -> 调用 list_directory(".", recursive=True, max_depth=3)
    - 用户: "查看下载目录的第一层" -> 调用 list_directory("~/Downloads")
    """
    try:
        safe_info = _safe_path(dir_path)
        
        if safe_info["warning"]:
            return f"⚠️ {safe_info['warning']}"
        
        if not safe_info["exists"]:
            return f"❌ 目录不存在: {safe_info['absolute_path']}"
        
        if not safe_info["is_dir"]:
            return f"❌ 不是目录: {safe_info['absolute_path']}"
        
        entries = []
        
        def scan(current_path: str, current_depth: int):
            if current_depth > max_depth:
                return
            
            try:
                with os.scandir(current_path) as it:
                    dirs = []
                    files = []
                    
                    for entry in it:
                        if _is_hidden(entry.name):
                            continue
                        
                        if entry.is_dir(follow_symlinks=False):
                            dirs.append(entry)
                        elif entry.is_file(follow_symlinks=False):
                            files.append(entry)
                    
                    for d in sorted(dirs, key=lambda x: x.name.lower()):
                        rel_path = os.path.relpath(d.path, safe_info["absolute_path"])
                        entries.append(f"📁 {rel_path}/")
                        if recursive and current_depth < max_depth:
                            scan(d.path, current_depth + 1)
                    
                    for f in sorted(files, key=lambda x: x.name.lower()):
                        rel_path = os.path.relpath(f.path, safe_info["absolute_path"])
                        size = _format_size(f.stat().st_size)
                        entries.append(f"📄 {rel_path} ({size})")
            except PermissionError:
                entries.append(f"🔒 权限不足，无法访问: {os.path.relpath(current_path, safe_info['absolute_path'])}")
            except Exception as e:
                logger.error(f"扫描目录失败: {e}")
        
        scan(safe_info["absolute_path"], 1)
        
        if not entries:
            return f"📂 该目录为空: {safe_info['absolute_path']}"
        
        result = f"📂 目录内容 ({safe_info['absolute_path']}):\n\n" + "\n".join(entries)
        return result
    
    except Exception as e:
        logger.error(f"列出目录失败: {e}")
        return f"❌ 列出目录失败: {e}"


@tool
def search_files(query: str, directory: str = ".", limit: int = 50, offset: int = 0) -> str:
    """在指定目录及子目录中搜索文件名匹配的文件。
    
    参数:
        query: 搜索模式，支持通配符（如 *.py、*test*）
        directory: 搜索目录，默认当前目录
        limit: 返回结果数量限制，默认50
        offset: 结果偏移量，默认0
        
    调用示例:
    - 用户: "在下载目录找一下所有 .pdf 文件" -> 调用 search_files("*.pdf", "~/Downloads")
    - 用户: "搜一下所有包含 config 的文件" -> 调用 search_files("*config*")
    - 用户: "看更多结果" -> 调用 search_files("*config*", offset=50)
    """
    try:
        safe_info = _safe_path(directory)
        
        if safe_info["warning"]:
            return f"⚠️ {safe_info['warning']}"
        
        if not safe_info["exists"]:
            return f"❌ 目录不存在: {safe_info['absolute_path']}"
        
        if not safe_info["is_dir"]:
            return f"❌ 不是目录: {safe_info['absolute_path']}"
        
        matches = []
        
        def search(current_path: str):
            if len(matches) >= offset + limit:
                return
            
            try:
                with os.scandir(current_path) as it:
                    for entry in it:
                        if _is_hidden(entry.name):
                            continue
                        
                        if entry.is_dir(follow_symlinks=False):
                            search(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            if fnmatch.fnmatch(entry.name, query):
                                rel_path = os.path.relpath(entry.path, safe_info["absolute_path"])
                                matches.append(rel_path)
                                if len(matches) >= offset + limit:
                                    return
            except PermissionError:
                pass
            except Exception as e:
                logger.debug(f"搜索目录失败: {e}")
        
        search(safe_info["absolute_path"])
        
        total = len(matches)
        start = offset
        end = min(offset + limit, total)
        page_matches = matches[start:end]
        
        if total == 0:
            return f"📭 未找到匹配文件: {query} (在 {safe_info['absolute_path']})"
        
        result = f"🔍 找到 {total} 个匹配文件，显示第 {start + 1}-{end} 个（共 {total} 个）:\n\n"
        result += "\n".join(page_matches)
        
        if end < total:
            result += f"\n\n📌 还有 {total - end} 个结果未显示，你可以调整 offset 参数查看更多。"
        
        return result
    
    except Exception as e:
        logger.error(f"搜索文件失败: {e}")
        return f"❌ 搜索文件失败: {e}"