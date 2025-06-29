import numpy as np
import pickle
import os
import uuid
from typing import List, Dict, Any, Optional
from app.models.document import Document, DocumentChunk
from app.config import settings
import logging
from datetime import datetime
import random
from app.utils.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class FAISSStorage:
    """基于numpy的简单向量数据库实现"""
    
    def __init__(self):
        self.vectors_file = "./data/faiss_vectors.pkl"
        self.metadata_file = "./data/faiss_metadata.pkl"
        self.vectors: np.ndarray = np.array([])
        self.metadata: List[Dict[str, Any]] = []
        self.document_ids: List[str] = []
        
        # 初始化向量化服务
        self.embedding_service = EmbeddingService()
        
        # 动态获取向量维度，而不是硬编码
        self.vector_dim = self.embedding_service.model.get_sentence_embedding_dimension()
        print(f"[DEBUG] FAISS存储初始化，使用向量维度: {self.vector_dim}")
        
        # 确保数据目录存在
        os.makedirs("./data", exist_ok=True)
        
        # 加载现有数据
        self._load_data()
    
    def _load_data(self):
        """加载现有数据"""
        try:
            if os.path.exists(self.vectors_file):
                with open(self.vectors_file, 'rb') as f:
                    self.vectors = pickle.load(f)
                logger.info(f"加载了 {len(self.vectors)} 个向量")
            
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'rb') as f:
                    data = pickle.load(f)
                    self.metadata = data.get('metadata', [])
                    self.document_ids = data.get('document_ids', [])
                logger.info(f"加载了 {len(self.metadata)} 个文档元数据")
        except Exception as e:
            logger.warning(f"加载数据失败: {e}")
            self.vectors = np.array([])
            self.metadata = []
            self.document_ids = []
    
    def _save_data(self):
        """保存数据到文件"""
        try:
            with open(self.vectors_file, 'wb') as f:
                pickle.dump(self.vectors, f)
            
            with open(self.metadata_file, 'wb') as f:
                pickle.dump({
                    'metadata': self.metadata,
                    'document_ids': self.document_ids
                }, f)
            logger.info("数据保存成功")
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            raise
    
    def _cosine_similarity(self, query_vector: np.ndarray, vectors: np.ndarray) -> np.ndarray:
        """计算余弦相似度"""
        # 归一化向量
        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0:
            return np.zeros(len(vectors))
        
        query_normalized = query_vector / query_norm
        
        # 计算每个向量的范数
        vector_norms = np.linalg.norm(vectors, axis=1)
        # 避免除零
        vector_norms[vector_norms == 0] = 1
        
        # 归一化所有向量
        vectors_normalized = vectors / vector_norms[:, np.newaxis]
        
        # 计算余弦相似度
        similarities = np.dot(vectors_normalized, query_normalized)
        return similarities
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """添加文档到存储"""
        try:
            for doc in documents:
                # 生成文档ID
                doc_id = doc.get('id', str(uuid.uuid4()))
                
                # 检查是否已存在
                if doc_id in self.document_ids:
                    logger.warning(f"文档ID {doc_id} 已存在，跳过")
                    continue
                
                # 获取向量
                vector = doc.get('vector')
                if vector is None:
                    # 如果没有向量，使用向量化服务生成真正的语义向量
                    logger.warning(f"文档 {doc_id} 缺少向量数据，使用向量化服务生成语义向量")
                    vector = self.embedding_service.get_embedding(doc.get('content', ''))
                
                # 转换为numpy数组
                if not isinstance(vector, np.ndarray):
                    vector = np.array(vector, dtype=np.float32)
                
                # 确保向量维度正确
                if len(vector) != self.vector_dim:
                    logger.warning(f"向量维度不匹配: 期望 {self.vector_dim}, 实际 {len(vector)}")
                    # 如果维度不匹配，尝试调整
                    if len(vector) > self.vector_dim:
                        vector = vector[:self.vector_dim]
                    else:
                        # 用零填充
                        padded_vector = np.zeros(self.vector_dim, dtype=np.float32)
                        padded_vector[:len(vector)] = vector
                        vector = padded_vector
                
                # 添加到向量数组
                if len(self.vectors) == 0:
                    self.vectors = vector.reshape(1, -1)
                else:
                    self.vectors = np.vstack([self.vectors, vector.reshape(1, -1)])
                
                # 添加元数据
                metadata = {
                    'id': doc_id,
                    'content': doc.get('content', ''),
                    'metadata': doc.get('metadata', {}),
                    'created_at': doc.get('created_at'),
                    'updated_at': doc.get('updated_at')
                }
                self.metadata.append(metadata)
                self.document_ids.append(doc_id)
                
                logger.info(f"添加文档 {doc_id}，当前总文档数: {len(self.metadata)}")
            
            # 保存数据
            self._save_data()
            return True
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False
    
    def search_documents(self, query_vector: np.ndarray, top_k: int = None, similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        try:
            if len(self.vectors) == 0:
                logger.warning("向量数据库为空")
                return []
            
            # 使用配置参数
            if top_k is None:
                top_k = settings.top_k
            if similarity_threshold is None:
                similarity_threshold = settings.similarity_threshold
            
            # 确保查询向量是numpy数组
            if not isinstance(query_vector, np.ndarray):
                query_vector = np.array(query_vector, dtype=np.float32)
            
            # 计算相似度
            similarities = self._cosine_similarity(query_vector, self.vectors)
            
            # 获取top_k个最相似的文档
            top_indices = np.argsort(similarities)[::-1][:min(top_k, len(similarities))]
            
            results = []
            for idx in top_indices:
                similarity = float(similarities[idx])
                # 使用配置的相似度阈值过滤
                if similarity >= similarity_threshold:
                    result = {
                        'id': self.metadata[idx]['id'],
                        'content': self.metadata[idx]['content'],
                        'metadata': self.metadata[idx]['metadata'],
                        'similarity': similarity,
                        'created_at': self.metadata[idx]['created_at'],
                        'updated_at': self.metadata[idx]['updated_at']
                    }
                    results.append(result)
            
            logger.info(f"搜索完成，找到 {len(results)} 个相关文档 (阈值: {similarity_threshold})")
            return results
            
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        try:
            if document_id not in self.document_ids:
                logger.warning(f"文档ID {document_id} 不存在")
                return False
            
            # 找到文档索引
            idx = self.document_ids.index(document_id)
            
            # 删除向量
            self.vectors = np.delete(self.vectors, idx, axis=0)
            
            # 删除元数据
            del self.metadata[idx]
            del self.document_ids[idx]
            
            # 保存数据
            self._save_data()
            
            logger.info(f"删除文档 {document_id} 成功")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def update_document(self, document_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """更新文档"""
        try:
            if document_id not in self.document_ids:
                logger.warning(f"文档ID {document_id} 不存在")
                return False
            
            # 找到文档索引
            idx = self.document_ids.index(document_id)
            
            # 更新元数据
            self.metadata[idx]['content'] = content
            self.metadata[idx]['metadata'].update(metadata)
            self.metadata[idx]['updated_at'] = metadata.get('updated_at')
            
            # 保存数据
            self._save_data()
            
            logger.info(f"更新文档 {document_id} 成功")
            return True
            
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """获取单个文档，返回Document对象"""
        try:
            if document_id not in self.document_ids:
                return None
            idx = self.document_ids.index(document_id)
            meta = self.metadata[idx]
            # 还原chunks（如果有）
            chunks = []
            if 'chunks' in meta:
                for chunk_dict in meta['chunks']:
                    chunks.append(DocumentChunk(**chunk_dict))
            doc = Document(
                id=meta.get('id'),
                title=meta.get('metadata', {}).get('document_title', ''),
                content=meta.get('content', ''),
                file_path=meta.get('file_path'),
                file_type=meta.get('file_type'),
                file_size=meta.get('file_size'),
                chunks=chunks,
                metadata=meta.get('metadata', {}),
                created_at=meta.get('created_at'),
                updated_at=meta.get('updated_at')
            )
            return doc
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None
    
    async def list_documents(self, page: int = 1, page_size: int = 10) -> List[Document]:
        """分页列出所有文档，返回Document对象列表"""
        start = (page - 1) * page_size
        end = start + page_size
        docs = []
        for meta in self.metadata[start:end]:
            # 还原chunks（如果有）
            chunks = []
            if 'chunks' in meta:
                for chunk_dict in meta['chunks']:
                    chunks.append(DocumentChunk(**chunk_dict))
            doc = Document(
                id=meta.get('id'),
                title=meta.get('metadata', {}).get('document_title', ''),
                content=meta.get('content', ''),
                file_path=meta.get('file_path'),
                file_type=meta.get('file_type'),
                file_size=meta.get('file_size'),
                chunks=chunks,
                metadata=meta.get('metadata', {}),
                created_at=meta.get('created_at'),
                updated_at=meta.get('updated_at')
            )
            docs.append(doc)
        return docs
    
    def clear_all(self) -> bool:
        """清空所有数据"""
        try:
            self.vectors = np.array([])
            self.metadata = []
            self.document_ids = []
            
            # 删除文件
            if os.path.exists(self.vectors_file):
                os.remove(self.vectors_file)
            if os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)
            
            logger.info("清空所有数据成功")
            return True
            
        except Exception as e:
            logger.error(f"清空数据失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            return {
                'total_documents': len(self.metadata),
                'vector_dimension': self.vector_dim,
                'vectors_shape': self.vectors.shape if len(self.vectors) > 0 else (0, 0),
                'storage_size_mb': self._get_storage_size(),
                'document_ids': self.document_ids[:10]  # 只返回前10个ID
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def _get_storage_size(self) -> float:
        """获取存储大小（MB）"""
        try:
            total_size = 0
            if os.path.exists(self.vectors_file):
                total_size += os.path.getsize(self.vectors_file)
            if os.path.exists(self.metadata_file):
                total_size += os.path.getsize(self.metadata_file)
            return round(total_size / (1024 * 1024), 2)
        except:
            return 0.0
    
    async def save_document(self, document: Document) -> bool:
        """保存文档到存储"""
        try:
            # 将文档转换为字典格式
            doc_dict = {
                'id': document.id,
                'content': document.content,
                'metadata': document.metadata,
                'created_at': document.created_at,
                'updated_at': document.updated_at
            }
            
            # 使用add_documents方法保存
            return self.add_documents([doc_dict])
            
        except Exception as e:
            logger.error(f"保存文档失败: {e}")
            return False
    
    async def save_chunk_embeddings(self, chunks: List[DocumentChunk]) -> bool:
        """保存文档块的向量嵌入"""
        try:
            documents = []
            for chunk in chunks:
                if chunk.embedding is not None:
                    doc_dict = {
                        'id': chunk.id,
                        'content': chunk.content,
                        'vector': chunk.embedding,
                        'metadata': chunk.metadata,
                        'created_at': datetime.now(),  # 使用当前时间
                        'updated_at': datetime.now()   # 使用当前时间
                    }
                    documents.append(doc_dict)
            
            return self.add_documents(documents)
            
        except Exception as e:
            logger.error(f"保存向量嵌入失败: {e}")
            return False
    
    async def search_similar_chunks(self, query_vector: List[float], top_k: int = 5, threshold: float = 0.7) -> List[DocumentChunk]:
        """搜索相似文档块"""
        try:
            if len(self.vectors) == 0:
                logger.warning("向量数据库为空")
                return []
            
            # 确保查询向量是numpy数组
            if not isinstance(query_vector, np.ndarray):
                query_vector = np.array(query_vector, dtype=np.float32)
            
            # 计算相似度
            similarities = self._cosine_similarity(query_vector, self.vectors)
            
            # 获取top_k个最相似的文档
            top_indices = np.argsort(similarities)[::-1][:min(top_k, len(similarities))]
            
            chunks = []
            for idx in top_indices:
                similarity = float(similarities[idx])
                # 使用配置的相似度阈值过滤
                if similarity >= threshold:
                    metadata = self.metadata[idx]
                    chunk = DocumentChunk(
                        id=metadata['id'],
                        content=metadata['content'],
                        metadata={
                            **metadata['metadata'],
                            'similarity': similarity,
                            'document_id': metadata['id']
                        }
                    )
                    chunks.append(chunk)
            
            logger.info(f"搜索完成，找到 {len(chunks)} 个相关文档块 (阈值: {threshold})")
            return chunks
            
        except Exception as e:
            logger.error(f"搜索相似文档块失败: {e}")
            return []
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查数据目录是否存在
            data_dir = os.path.dirname(self.vectors_file)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)
            
            # 检查向量和元数据是否一致
            if len(self.vectors) != len(self.metadata):
                logger.warning("向量和元数据数量不一致")
                return False
            
            # 尝试保存数据（测试写入权限）
            self._save_data()
            
            return True
        except Exception as e:
            logger.error(f"FAISS存储健康检查失败: {e}")
            return False 