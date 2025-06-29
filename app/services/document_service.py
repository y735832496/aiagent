import uuid
import time
from typing import List, Dict, Any, Optional
from app.models.document import Document, DocumentChunk, DocumentUploadRequest, DocumentListResponse
from app.models.storage import StorageBackend
from app.utils.text_processor import TextProcessor
from app.utils.embedding_service import EmbeddingService
from app.services.storage_factory import StorageFactory
from app.services.langchain_service import LangChainRAGService
from app.config import settings

class DocumentService:
    """文档服务 - 集成LangChain"""
    
    def __init__(self):
        self.storage = StorageFactory.create_storage()
        self.text_processor = TextProcessor()
        self.embedding_service = EmbeddingService()
        self.langchain_service = LangChainRAGService()
    
    async def upload_document(self, request: DocumentUploadRequest) -> Document:
        """上传文档 - 同时更新原有存储和LangChain存储"""
        try:
            # 生成文档ID
            document_id = str(uuid.uuid4())
            
            # 创建文档对象
            document = Document(
                id=document_id,
                title=request.title,
                content=request.content,
                file_type=request.file_type,
                file_size=len(request.content.encode('utf-8')),
                created_at=time.time(),
                updated_at=time.time(),
                metadata=request.metadata or {}
            )
            
            # 1. 更新原有存储系统
            # print("📝 更新原有存储系统...")
            # success = await self.storage.save_document(document)
            # if not success:
            #     raise Exception("保存到原有存储失败")
            
            # 2. 更新LangChain存储系统
            print("🤖 更新LangChain存储系统...")
            langchain_docs = [{
                "id": document.id,
                "title": document.title,
                "content": document.content,
                "created_at": document.created_at,
                "file_type": document.file_type
            }]
            
            langchain_success = self.langchain_service.add_documents(langchain_docs)
            if not langchain_success:
                print("⚠️ 警告：LangChain存储更新失败，但原有存储已成功")
            
            print(f"✅ 文档上传完成: {document.title}")
            return document
            
        except Exception as e:
            print(f"❌ 文档上传失败: {e}")
            raise
    
    async def upload_text_document(self, title: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        """上传文本文档"""
        request = DocumentUploadRequest(
            title=title,
            content=content,
            file_type="text",
            metadata=metadata or {}
        )
        return await self.upload_document(request)
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """获取文档"""
        try:
            return await self.storage.get_document(document_id)
        except Exception as e:
            print(f"获取文档失败: {e}")
            return None
    
    async def list_documents(self, page: int = 1, page_size: int = 10) -> DocumentListResponse:
        """获取文档列表"""
        try:
            documents = await self.storage.list_documents(page, page_size)
            
            # 将Document对象转换为字典
            doc_dicts = []
            for doc in documents:
                doc_dict = {
                    "id": doc.id,
                    "title": doc.title,
                    "content": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,  # 截断长内容
                    "file_type": doc.file_type,
                    "file_size": doc.file_size,
                    "created_at": doc.created_at.isoformat() if hasattr(doc.created_at, 'isoformat') else str(doc.created_at),
                    "updated_at": doc.updated_at.isoformat() if hasattr(doc.updated_at, 'isoformat') else str(doc.updated_at),
                    "chunks_count": len(doc.chunks),
                    "metadata": doc.metadata
                }
                doc_dicts.append(doc_dict)
            
            # 获取总数（这里简化处理，实际应该从存储获取）
            total_count = len(doc_dicts) + (page - 1) * page_size  # 估算总数
            
            return DocumentListResponse(
                documents=doc_dicts,
                total_count=total_count,
                page=page,
                page_size=page_size
            )
        except Exception as e:
            print(f"获取文档列表失败: {e}")
            return DocumentListResponse(documents=[], total_count=0, page=page, page_size=page_size)
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        try:
            # 从原有存储删除
            success = await self.storage.delete_document(document_id)
            
            # 从LangChain存储删除向量数据
            langchain_success = self.langchain_service.delete_document(document_id)
            
            if success and langchain_success:
                print(f"✅ 成功删除文档 {document_id} 及其向量数据")
                return True
            elif success:
                print(f"⚠️ 文档 {document_id} 删除成功，但向量数据删除失败")
                return True
            else:
                print(f"❌ 删除文档 {document_id} 失败")
                return False
                
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False
    
    async def get_document_stats(self) -> Dict[str, Any]:
        """获取文档统计信息"""
        try:
            # 获取原有存储统计
            legacy_stats = await self.storage.get_stats()
            
            # 获取LangChain统计
            langchain_stats = self.langchain_service.get_stats()
            
            return {
                "legacy_storage": legacy_stats,
                "langchain_storage": langchain_stats,
                "total_documents": legacy_stats.get("total_documents", 0),
                "total_chunks": langchain_stats.get("total_chunks", 0)
            }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {
                "legacy_storage": {},
                "langchain_storage": {},
                "total_documents": 0,
                "total_chunks": 0
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查原有存储
            legacy_health = await self.storage.health_check()
            
            # 检查LangChain存储
            langchain_health = await self.langchain_service.health_check()
            
            return {
                "status": "healthy" if legacy_health and langchain_health.get("status") == "healthy" else "unhealthy",
                "legacy_storage": {
                    "backend": type(self.storage).__name__,
                    "healthy": legacy_health
                },
                "langchain_storage": langchain_health
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            } 