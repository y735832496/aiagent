import time
from typing import List, Dict, Any
from app.models.document import QueryRequest, QueryResponse, DocumentChunk
from app.utils.embedding_service import EmbeddingService
from app.utils.llm_service import LLMService
from app.services.storage_factory import StorageFactory
from app.services.langchain_service import LangChainRAGService
from app.services.memory_context import MemoryContext
from app.config import settings

class QueryService:
    """查询服务 - 集成LangChain RAG和MemoryContext历史记忆"""
    
    def __init__(self):
        # 保留原有服务作为备用
        self.storage = StorageFactory.create_storage()
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
        
        # 新增LangChain RAG服务
        self.langchain_service = LangChainRAGService()
        
        # 新增MemoryContext历史记忆服务
        self.memory_context = MemoryContext()
    
    async def query(self, request: QueryRequest) -> QueryResponse:
        """处理查询请求 - 使用LangChain RAG + MemoryContext历史记忆"""
        start_time = time.time()
        
        try:
            print(f"🔍 开始处理查询: '{request.query}'")
            print(f"📝 会话ID: {request.session_id}")
            
            # 使用配置默认值
            top_k = request.top_k if request.top_k is not None else settings.top_k
            threshold = request.threshold if request.threshold is not None else settings.similarity_threshold
            
            print(f"📊 参数: top_k={top_k}, threshold={threshold}")
            
            # 1. 获取历史记忆
            print("🧠 获取历史记忆...")
            history = self.memory_context.get_conversation_history(request.session_id, limit=10)
            history_text = ""
            if history:
                print(f"📚 找到 {len(history)} 条历史记录")
                for mem in history:
                    history_text += f"{mem['role']}: {mem['content']}\n"
                print(f"📖 历史上下文长度: {len(history_text)} 字符")
            else:
                print("📚 无历史记录，开始新会话")
            
            # 2. 构建带历史上下文的查询
            enhanced_query = request.query
            if history_text:
                # 将历史作为上下文添加到查询中
                enhanced_query = f"历史对话:\n{history_text}\n\n当前问题: {request.query}"
                print(f"🔗 已添加历史上下文，增强查询长度: {len(enhanced_query)} 字符")
            
            # 3. 使用LangChain RAG服务
            print("🤖 使用LangChain RAG服务...")
            result = await self.langchain_service.query(
                query=enhanced_query,
                top_k=top_k,
                threshold=threshold
            )
            print(f"result is :{result}")
            
            # 4. 处理结果
            answer = result.get("answer", "")
            print(f"answer is :{answer}")
            sources = result.get("sources", [])
            print(f"sources is :{sources}")
            confidence = result.get("confidence", 0.0)
            print(f"confidence is :{confidence}")
            
            # 5. 存储本轮对话到记忆
            print("💾 存储对话记忆...")
            try:
                # 存储用户问题
                self.memory_context.add_memory(
                    session_id=request.session_id,
                    role="user",
                    content=request.query
                )
                # 存储助手回答
                self.memory_context.add_memory(
                    session_id=request.session_id,
                    role="assistant",
                    content=answer
                )
                print("✅ 对话记忆存储成功")
            except Exception as e:
                print(f"⚠️ 存储对话记忆失败: {e}")
            
            # 6. 转换来源格式以保持API兼容性
            formatted_sources = []
            for source in sources:
                formatted_source = {
                    "content_preview": source.get("content_preview", ""),
                    "similarity": 0.8,  # LangChain不直接提供相似度，使用默认值
                    "metadata": source.get("metadata", {})
                }
                formatted_sources.append(formatted_source)
            
            processing_time = time.time() - start_time
            print(f"✅ LangChain RAG + Memory处理完成，耗时: {processing_time:.4f}秒")
            
            return QueryResponse(
                query=request.query,
                answer=answer,
                sources=formatted_sources if request.include_metadata else [],
                confidence=confidence,
                processing_time=processing_time,
                total_chunks_retrieved=len(sources)
            )
            
        except Exception as e:
            print(f"❌ LangChain RAG查询失败，回退到原有服务: {e}")
            return await self._fallback_query(request, start_time)
    
    async def _fallback_query(self, request: QueryRequest, start_time: float) -> QueryResponse:
        """回退到原有的查询服务（也包含记忆功能）"""
        try:
            print("🔄 使用原有查询服务...")
            
            # 使用配置默认值
            top_k = request.top_k if request.top_k is not None else settings.top_k
            threshold = request.threshold if request.threshold is not None else settings.similarity_threshold
            
            # 1. 获取历史记忆
            print("🧠 获取历史记忆...")
            history = self.memory_context.get_conversation_history(request.session_id, limit=10)
            history_text = ""
            if history:
                print(f"📚 找到 {len(history)} 条历史记录")
                for mem in history:
                    history_text += f"{mem['role']}: {mem['content']}\n"
            
            # 2. 将查询转换为向量
            print("🔄 正在将查询转换为向量...")
            query_vector = self.embedding_service.encode_single_text(request.query)
            print(f"✅ 查询向量生成完成，维度: {len(query_vector)}")
            
            # 3. 向量检索相似文档块
            print("🔍 正在检索相似文档块...")
            similar_chunks = await self.storage.search_similar_chunks(
                query_vector=query_vector,
                top_k=top_k,
                threshold=threshold
            )
            print(f"📄 检索到 {len(similar_chunks)} 个相似文档块")
            
            # 打印每个块的详细信息
            for i, chunk in enumerate(similar_chunks):
                similarity = chunk.metadata.get('similarity', 0.0)
                print(f"  块 {i+1}: 相似度={similarity:.4f}, 内容预览='{chunk.content[:50]}...'")
            
            # 4. 构建上下文
            context_texts = []
            sources = []
            
            for chunk in similar_chunks:
                context_texts.append(chunk.content)
                
                # 构建来源信息
                source_info = {
                    'chunk_id': chunk.id,
                    'content_preview': chunk.content[:100] + '...' if len(chunk.content) > 100 else chunk.content,
                    'similarity': chunk.metadata.get('similarity', 0.0)
                }
                
                # 添加文档信息
                if 'document_id' in chunk.metadata:
                    source_info['document_id'] = chunk.metadata['document_id']
                if 'document_title' in chunk.metadata:
                    source_info['document_title'] = chunk.metadata['document_title']
                
                sources.append(source_info)
            
            # 5. 生成答案（包含历史上下文）
            if context_texts:
                print("🤖 正在生成答案...")
                
                # 构建包含历史的上下文
                full_context = context_texts
                if history_text:
                    full_context.insert(0, f"历史对话:\n{history_text}")
                
                answer = await self.llm_service.generate_answer(
                    query=request.query,
                    context=full_context
                )
                print(f"✅ 答案生成完成: '{answer[:100]}...'")
            else:
                answer = "抱歉，没有找到相关的文档内容来回答您的问题。请尝试使用不同的关键词或降低相似度阈值。"
                print("❌ 没有找到相关文档内容")
            
            # 6. 存储本轮对话到记忆
            print("💾 存储对话记忆...")
            try:
                self.memory_context.add_memory(
                    session_id=request.session_id,
                    role="user",
                    content=request.query
                )
                self.memory_context.add_memory(
                    session_id=request.session_id,
                    role="assistant",
                    content=answer
                )
                print("✅ 对话记忆存储成功")
            except Exception as e:
                print(f"⚠️ 存储对话记忆失败: {e}")
            
            # 7. 计算置信度（基于相似度）
            confidence = 0.0
            if sources:
                avg_similarity = sum(s['similarity'] for s in sources) / len(sources)
                confidence = min(avg_similarity, 1.0)
                print(f"📈 平均相似度: {avg_similarity:.4f}, 置信度: {confidence:.4f}")
            
            processing_time = time.time() - start_time
            print(f"⏱️ 处理完成，耗时: {processing_time:.4f}秒")
            
            return QueryResponse(
                query=request.query,
                answer=answer,
                sources=sources if request.include_metadata else [],
                confidence=confidence,
                processing_time=processing_time,
                total_chunks_retrieved=len(similar_chunks)
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ 回退查询处理失败: {e}")
            return QueryResponse(
                query=request.query,
                answer=f"查询处理失败: {str(e)}",
                sources=[],
                confidence=0.0,
                processing_time=processing_time,
                total_chunks_retrieved=0
            )
    
    async def search_documents(self, query: str, top_k: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """搜索文档（返回文档级别的结果）"""
        try:
            print(f"🔍 搜索文档: '{query}', top_k={top_k}, threshold={threshold}")
            
            # 优先使用LangChain存储系统
            try:
                print("🤖 使用LangChain存储系统搜索...")
                results = await self.langchain_service.search_documents(
                    query=query,
                    top_k=top_k,
                    threshold=threshold
                )
                print(f"✅ LangChain搜索完成，找到 {len(results)} 个结果")
                return results
                
            except Exception as e:
                print(f"❌ LangChain搜索失败，回退到原有存储系统: {e}")
                
                # 回退到原有存储系统
                print("🔄 使用原有存储系统搜索...")
                
                # 将查询转换为向量
                query_vector = self.embedding_service.encode_single_text(query)
                
                # 检索相似文档块
                similar_chunks = await self.storage.search_similar_chunks(
                    query_vector=query_vector,
                    top_k=top_k * 2,  # 获取更多块以便去重
                    threshold=threshold
                )
                
                # 按文档分组
                document_scores = {}
                
                for chunk in similar_chunks:
                    doc_id = chunk.metadata.get('document_id')
                    if doc_id:
                        if doc_id not in document_scores:
                            document_scores[doc_id] = {
                                'document_id': doc_id,
                                'document_title': chunk.metadata.get('document_title', 'Unknown'),
                                'chunks': [],
                                'max_similarity': 0.0,
                                'avg_similarity': 0.0
                            }
                        
                        similarity = chunk.metadata.get('similarity', 0.0)
                        document_scores[doc_id]['chunks'].append({
                            'chunk_id': chunk.id,
                            'content_preview': chunk.content[:150] + '...' if len(chunk.content) > 150 else chunk.content,
                            'similarity': similarity
                        })
                        
                        # 更新文档级别的相似度
                        doc_scores = document_scores[doc_id]
                        doc_scores['max_similarity'] = max(doc_scores['max_similarity'], similarity)
                
                # 计算平均相似度
                for doc_id, doc_info in document_scores.items():
                    similarities = [chunk['similarity'] for chunk in doc_info['chunks']]
                    doc_info['avg_similarity'] = sum(similarities) / len(similarities)
                    # 只保留前3个最相关的块
                    doc_info['chunks'] = sorted(doc_info['chunks'], key=lambda x: x['similarity'], reverse=True)[:3]
                
                # 按最大相似度排序
                results = list(document_scores.values())
                results.sort(key=lambda x: x['max_similarity'], reverse=True)
                
                print(f"✅ 原有存储系统搜索完成，找到 {len(results)} 个文档")
                return results
                
        except Exception as e:
            print(f"❌ 搜索文档失败: {e}")
            return []
    
    async def get_suggestions(self, query: str, max_suggestions: int = 5) -> List[str]:
        """获取查询建议"""
        try:
            print(f"💡 获取查询建议: '{query}', max_suggestions={max_suggestions}")
            
            # 简单的建议生成逻辑
            suggestions = []
            
            # 基于查询长度生成建议
            if len(query) < 5:
                suggestions.append(f"{query} 是什么？")
                suggestions.append(f"请详细介绍一下 {query}")
            else:
                suggestions.append(f"{query} 的相关信息")
                suggestions.append(f"{query} 的定义")
                suggestions.append(f"{query} 的特点")
            
            # 添加一些通用建议
            suggestions.extend([
                "请提供更多上下文信息",
                "能否举例说明？",
                "有什么相关的文档吗？"
            ])
            
            # 去重并限制数量
            unique_suggestions = list(dict.fromkeys(suggestions))
            return unique_suggestions[:max_suggestions]
            
        except Exception as e:
            print(f"❌ 获取查询建议失败: {e}")
            return []
    
    async def health_check(self) -> dict:
        """健康检查"""
        try:
            print("🏥 开始健康检查...")
            
            health_info = {
                "status": "healthy",
                "timestamp": time.time(),
                "services": {}
            }
            
            # 检查LangChain服务
            try:
                langchain_stats = self.langchain_service.get_stats()
                health_info["services"]["langchain"] = {
                    "status": "healthy" if langchain_stats.get("vector_store_ok") else "unhealthy",
                    "total_chunks": langchain_stats.get("total_chunks", 0),
                    "llm_ok": langchain_stats.get("llm_ok", False)
                }
            except Exception as e:
                health_info["services"]["langchain"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # 检查MemoryContext服务
            try:
                memory_stats = self.memory_context.get_stats()
                health_info["services"]["memory"] = {
                    "status": "healthy" if memory_stats.get("status") == "connected" else "unhealthy",
                    "session_count": memory_stats.get("session_count", 0),
                    "memory_count": memory_stats.get("memory_count", 0)
                }
            except Exception as e:
                health_info["services"]["memory"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # 检查存储服务
            try:
                # 简单的存储检查
                health_info["services"]["storage"] = {
                    "status": "healthy"
                }
            except Exception as e:
                health_info["services"]["storage"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # 检查向量化服务
            try:
                model_info = self.embedding_service.get_model_info()
                health_info["services"]["embedding"] = {
                    "status": "healthy" if model_info.get("status") == "loaded" else "unhealthy",
                    "model_name": model_info.get("model_name", "unknown"),
                    "embedding_dimension": model_info.get("embedding_dimension", 0)
                }
            except Exception as e:
                health_info["services"]["embedding"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # 整体状态判断
            all_healthy = all(
                service.get("status") == "healthy" 
                for service in health_info["services"].values()
            )
            health_info["status"] = "healthy" if all_healthy else "degraded"
            
            print(f"✅ 健康检查完成: {health_info['status']}")
            return health_info
            
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            }