# 文档加载器模块
# 提供抽象的 BaseLoader 接口和多种格式的具体加载器实现

import os
import re
from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document
from agent_core.errors import DocumentLoadError
from agent_core.logger import get_logger

logger = get_logger(__name__)


class BaseLoader(ABC):
    """文档加载器抽象基类

    所有具体的加载器（TxtLoader、MarkdownLoader 等）都需要实现 load() 方法。
    """

    @abstractmethod
    def load(self, file_path: str) -> List[Document]:
        """加载文档并返回 Document 列表

        Args:
            file_path: 文档文件的绝对路径

        Returns:
            List[Document]: 文档列表，每个 Document 代表一个可索引的片段

        Raises:
            DocumentLoadError: 文档加载失败时抛出
        """
        pass

    def _validate_file(self, file_path: str) -> None:
        """验证文件是否存在且可读

        Args:
            file_path: 文件路径

        Raises:
            DocumentLoadError: 文件不存在或不可读时抛出
        """
        if not os.path.exists(file_path):
            raise DocumentLoadError(f"文件不存在: {file_path}")

        if not os.path.isfile(file_path):
            raise DocumentLoadError(f"路径不是文件: {file_path}")

        if not os.access(file_path, os.R_OK):
            raise DocumentLoadError(f"文件不可读: {file_path}")


class TxtLoader(BaseLoader):
    """纯文本加载器

    按行分割文本，每行作为一个独立的 Document。
    适用于结构化文本（如每行一条知识点）。
    """

    def load(self, file_path: str) -> List[Document]:
        """加载 .txt 文件，按行分割

        Args:
            file_path: .txt 文件的路径

        Returns:
            List[Document]: 文档列表，每行一个 Document
        """
        self._validate_file(file_path)

        documents = []
        filename = os.path.basename(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:  # 跳过空行
                        doc = Document(
                            page_content=line,
                            metadata={
                                "source": filename,
                                "line": line_num
                            }
                        )
                        documents.append(doc)

            logger.debug(f"TxtLoader 加载 {filename} 成功，共 {len(documents)} 行")
            return documents

        except UnicodeDecodeError as e:
            raise DocumentLoadError(f"文件编码错误（需要 UTF-8）: {file_path}") from e
        except Exception as e:
            raise DocumentLoadError(f"读取文件失败: {file_path}") from e


class MarkdownLoader(BaseLoader):
    """Markdown 加载器

    按标题（# 一级标题、## 二级标题等）分割文档，
    每个章节作为一个独立的 Document，保留章节的上下文信息。
    """

    # 匹配 Markdown 标题的正则：# 标题
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    def load(self, file_path: str) -> List[Document]:
        """加载 .md 文件，按标题分段

        Args:
            file_path: .md 文件的路径

        Returns:
            List[Document]: 文档列表，每个标题下的内容作为一个 Document
        """
        self._validate_file(file_path)

        filename = os.path.basename(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 查找所有标题及其位置
            matches = list(self.HEADING_PATTERN.finditer(content))

            # 如果没有标题，整个文件作为一个 Document
            if not matches:
                if content.strip():
                    doc = Document(
                        page_content=content.strip(),
                        metadata={"source": filename, "section": "root"}
                    )
                    logger.debug(f"MarkdownLoader 加载 {filename} 成功，无标题，整体作为一个文档")
                    return [doc]
                return []

            documents = []

            # 按标题分段
            for i, match in enumerate(matches):
                # 获取标题级别和标题文本
                heading_level = len(match.group(1))  # # 的数量表示级别
                heading_text = match.group(2).strip()

                # 计算本段内容的起止位置
                start_pos = match.start()

                # 下一个标题的位置（如果没有下一个标题，则到文件末尾）
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)

                # 提取本段内容（包含标题本身）
                section_content = content[start_pos:end_pos].strip()

                if section_content:
                    doc = Document(
                        page_content=section_content,
                        metadata={
                            "source": filename,
                            "section": heading_text,
                            "level": heading_level
                        }
                    )
                    documents.append(doc)

            logger.debug(f"MarkdownLoader 加载 {filename} 成功，共 {len(documents)} 个章节")
            return documents

        except UnicodeDecodeError as e:
            raise DocumentLoadError(f"文件编码错误（需要 UTF-8）: {file_path}") from e
        except Exception as e:
            raise DocumentLoadError(f"读取 Markdown 文件失败: {file_path}") from e


# 加载器注册表：文件扩展名 -> 加载器类
LOADER_REGISTRY = {
    ".txt": TxtLoader,
    ".md": MarkdownLoader,
}


def get_loader(file_path: str) -> BaseLoader:
    """根据文件扩展名获取对应的加载器

    Args:
        file_path: 文件路径

    Returns:
        BaseLoader: 对应的加载器实例

    Raises:
        DocumentLoadError: 不支持的文件格式时抛出
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    loader_class = LOADER_REGISTRY.get(ext)
    if loader_class is None:
        raise DocumentLoadError(
            f"不支持的文件格式: {ext}。"
            f"支持的格式: {', '.join(LOADER_REGISTRY.keys())}"
        )

    return loader_class()


__all__ = [
    "BaseLoader",
    "TxtLoader",
    "MarkdownLoader",
    "get_loader",
    "LOADER_REGISTRY",
]