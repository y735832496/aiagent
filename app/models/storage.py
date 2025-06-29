from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .document import Document, DocumentChunk

class StorageBackend(ABC):
    """存储后端抽象基类"""
    
    @abstractmethod
    async def save_document(self, document: Document) -> bool:
        """保存文档"""
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Document]:
        """获取文档"""
        pass
    
    @abstractmethod
    async def list_documents(self, page: int = 1, page_size: int = 10) -> List[Document]:
        """列出文档"""
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        pass
    
    @abstractmethod
    async def search_similar_chunks(self, query_vector: List[float], top_k: int = 5, threshold: float = 0.7) -> List[DocumentChunk]:
        """搜索相似文档块"""
        pass
    
    @abstractmethod
    async def save_chunk_embeddings(self, chunks: List[DocumentChunk]) -> bool:
        """保存文档块向量"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass 