from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

class DocumentChunk(BaseModel):
    """文档块模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    chunk_index: int = 0
    
class Document(BaseModel):
    """文档模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    chunks: List[DocumentChunk] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_chunk(self, content: str, metadata: Dict[str, Any] = None) -> DocumentChunk:
        """添加文档块"""
        chunk = DocumentChunk(
            content=content,
            metadata=metadata or {},
            chunk_index=len(self.chunks)
        )
        self.chunks.append(chunk)
        return chunk

class DocumentUploadRequest(BaseModel):
    """文档上传请求模型"""
    title: str
    content: str
    file_type: Optional[str] = "text"
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class QueryRequest(BaseModel):
    """查询请求模型"""
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    include_metadata: bool = True

class QueryResponse(BaseModel):
    """查询响应模型"""
    query: str
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    processing_time: float = 0.0
    total_chunks_retrieved: int = 0

class DocumentUploadResponse(BaseModel):
    """文档上传响应模型"""
    document_id: str
    title: str
    chunks_count: int
    message: str
    processing_time: float = 0.0

class DocumentListResponse(BaseModel):
    """文档列表响应模型"""
    documents: List[Dict[str, Any]]
    total_count: int
    page: int = 1
    page_size: int = 10

class LangChainStats(BaseModel):
    """LangChain统计信息模型"""
    total_documents: int = 0
    total_chunks: int = 0
    vector_store_status: str = "unknown"
    llm_status: str = "unknown" 