from pydantic import BaseModel
from typing import Optional, List


class KnowledgeStatusResponse(BaseModel):
    """知识库状态响应"""
    total_files: int           # knowledge/ 目录下的文件总数
    total_chunks: int          # 向量库中的 chunk 总数
    last_build: Optional[str] = None  # 最后构建时间（ISO 格式字符串）
    hash_changed: bool         # 当前哈希是否与上次构建一致（True=有变化待重建）


class KnowledgeFileItem(BaseModel):
    """单个文件信息"""
    name: str
    size: int                  # 字节
    modified_at: str           # ISO 格式
    is_indexed: bool           # 是否已被索引


class KnowledgeFileListResponse(BaseModel):
    files: List[KnowledgeFileItem]
    total: int


class KnowledgeSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3


class KnowledgeSearchResultItem(BaseModel):
    content: str
    metadata: dict             # 包含 source, line, section 等


class KnowledgeSearchResponse(BaseModel):
    results: List[KnowledgeSearchResultItem]


class KnowledgeRebuildResponse(BaseModel):
    success: bool
    message: str
    chunks_added: Optional[int] = None


class KnowledgeFileContentResponse(BaseModel):
    """文件原始内容响应"""
    name: str
    content: str
    size: int