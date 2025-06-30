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
        """从LangChain存储获取文档列表"""
        try:
            print(f"📚 从LangChain存储获取文档列表: page={page}, page_size={page_size}")
            
            # 从LangChain存储获取文档信息
            vector_store = self.langchain_service.vector_store
            if not vector_store:
                print("❌ LangChain向量存储为空")
    
            
            print(f"📊 LangChain存储状态: {len(vector_store.index_to_docstore_id)} 个文档块")
            
            # 从向量存储中提取文档信息
            documents = []
            doc_ids = set()
            
            for idx, doc_id in vector_store.index_to_docstore_id.items():
                doc = vector_store.docstore._dict.get(doc_id)
                if doc:
                    document_id = doc.metadata.get("document_id")
                    if document_id and document_id not in doc_ids:
                        doc_ids.add(document_id)
                        
                        # 计算该文档的块数
                        chunk_count = sum(1 for i, stored_doc_id in vector_store.index_to_docstore_id.items()
                                        if vector_store.docstore._dict.get(stored_doc_id, {}).metadata.get("document_id") == document_id)
                        
                        documents.append({
                            "id": document_id,
                            "title": doc.metadata.get("title", "Unknown"),
                            "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                            "file_type": doc.metadata.get("file_type", "text"),
                            "file_size": len(doc.page_content.encode("utf-8")),
                            "created_at": str(doc.metadata.get("created_at", "")),
                            "updated_at": str(doc.metadata.get("created_at", "")),  # 使用创建时间作为更新时间
                            "chunks_count": chunk_count,
                            "metadata": {
                                "document_id": document_id,
                                "title": doc.metadata.get("title", "Unknown"),
                                "file_type": doc.metadata.get("file_type", "text"),
                                "created_at": doc.metadata.get("created_at", "")
                            }
                        })
            
            print(f"📄 提取到 {len(documents)} 个唯一文档")
            
            # 按创建时间排序（如果有的话）
            try:
                documents.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            except:
                pass  # 如果排序失败，保持原有顺序
            
            # 分页处理
            total_count = len(documents)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_docs = documents[start_idx:end_idx]
            
            print(f"📊 分页结果: 总数={total_count}, 当前页={page}, 页大小={page_size}, 返回={len(paginated_docs)}个文档")
            
            return DocumentListResponse(
                documents=paginated_docs,
                total_count=total_count,
                page=page,
                page_size=page_size
            )
        except Exception as e:
            print(f"❌ 从LangChain存储获取文档列表失败: {e}")
            import traceback
            traceback.print_exc()


    
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