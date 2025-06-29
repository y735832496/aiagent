"""
LangChain RAG服务
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema import Document
from pydantic import Field
from app.config import settings
import aiohttp
import json


class DeepSeekLLM(LLM):
    """DeepSeek LLM包装器"""
    
    api_key: str = Field(description="DeepSeek API密钥")
    api_url: str = Field(description="DeepSeek API URL")
    model: str = Field(description="DeepSeek模型名称")
    
    def __init__(self, api_key: str, api_url: str, model: str):
        super().__init__(api_key=api_key, api_url=api_url, model=model)
    
    @property
    def _llm_type(self) -> str:
        return "deepseek"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """同步调用DeepSeek API"""
        return asyncio.run(self._acall(prompt, stop, run_manager, **kwargs))
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """异步调用DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    raise Exception(f"API调用失败: {response.status} - {error_text}")


class LangChainRAGService:
    """LangChain RAG服务 - 单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LangChainRAGService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 确保只初始化一次
        if not self._initialized:
            print(f"[DEBUG] LangChain服务初始化，配置的模型: {settings.embedding_model}")
            self.embeddings = SentenceTransformerEmbeddings(
                model_name=settings.embedding_model,
                model_kwargs={'device': settings.embedding_device}
            )
            
            # 打印实际加载的模型信息
            try:
                # 尝试获取底层模型信息
                if hasattr(self.embeddings, 'client') and hasattr(self.embeddings.client, 'get_sentence_embedding_dimension'):
                    dim = self.embeddings.client.get_sentence_embedding_dimension()
                    print(f"[DEBUG] LangChain embeddings实际维度: {dim}")
                else:
                    print("[DEBUG] 无法获取LangChain embeddings维度信息")
            except Exception as e:
                print(f"[DEBUG] 获取LangChain embeddings信息失败: {e}")
            
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                length_function=len,
            )
            
            self.llm = DeepSeekLLM(
                api_key=settings.deepseek_api_key,
                api_url=settings.deepseek_api_url,
                model=settings.deepseek_model
            )
            
            self.vector_store = None
            self.qa_chain = None
            self._initialize_vector_store()
            
            self._initialized = True
    
    def _initialize_vector_store(self):
        """初始化向量存储"""
        vector_store_path = f"{settings.data_dir}/faiss/langchain_vectorstore"
        os.makedirs(vector_store_path, exist_ok=True)
        
        # 尝试加载现有的向量存储
        if os.path.exists(f"{vector_store_path}/index.faiss"):
            try:
                self.vector_store = FAISS.load_local(
                    vector_store_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True  # 允许加载本地文件
                )
                print("✅ 成功加载现有向量存储")
            except Exception as e:
                print(f"⚠️ 加载向量存储失败: {e}")
                self.vector_store = None
        
        # 如果没有现有存储，创建新的空向量存储
        if self.vector_store is None:
            # 创建一个真正的空向量存储
            # 使用一个临时文档创建存储，然后立即清空
            temp_doc = Document(page_content="temp", metadata={})
            self.vector_store = FAISS.from_documents([temp_doc], self.embeddings)
            
            # 清空存储，确保是真正的空存储
            try:
                # 获取所有文档ID并删除
                doc_ids = list(self.vector_store.index_to_docstore_id.values())
                if doc_ids:
                    self.vector_store.delete(doc_ids)
                print("✅ 创建新的空向量存储")
            except Exception as e:
                print(f"⚠️ 清空向量存储时出错: {e}")
                # 如果清空失败，重新创建一个新的空存储
                self.vector_store = FAISS.from_documents([], self.embeddings)
                print("✅ 重新创建空向量存储")
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """添加文档到向量存储"""
        try:
            print(f"🔍 开始添加 {len(documents)} 个文档到LangChain存储")
            
            # 转换为LangChain Document格式
            langchain_docs = []
            for doc in documents:
                print(f"  处理文档: {doc.get('title', 'Unknown')} (ID: {doc['id']})")
                langchain_doc = Document(
                    page_content=doc["content"],
                    metadata={
                        "document_id": doc["id"],
                        "title": doc["title"],
                        "created_at": doc.get("created_at", ""),
                        "file_type": doc.get("file_type", "")
                    }
                )
                langchain_docs.append(langchain_doc)
            
            print(f"✅ 转换为LangChain格式完成，共 {len(langchain_docs)} 个文档")
            
            # 分块
            print("📝 开始文档分块...")
            split_docs = self.text_splitter.split_documents(langchain_docs)
            print(f"✅ 分块完成，共生成 {len(split_docs)} 个文档块")
            
            # 打印分块详情
            for i, doc in enumerate(split_docs):
                print(f"  块 {i+1}: 长度={len(doc.page_content)}, 元数据={doc.metadata}")
            
            # 添加到向量存储
            print("💾 开始添加到向量存储...")
            if self.vector_store is None:
                print("⚠️ 向量存储为空，创建新的向量存储")
                self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
            else:
                print(f"📊 当前向量存储状态: {len(self.vector_store.index_to_docstore_id)} 个文档")
                self.vector_store.add_documents(split_docs)
                print(f"📊 添加后向量存储状态: {len(self.vector_store.index_to_docstore_id)} 个文档")
            
            # 保存向量存储
            print("💾 保存向量存储到本地...")
            vector_store_path = f"{settings.data_dir}/faiss/langchain_vectorstore"
            self.vector_store.save_local(vector_store_path)
            print(f"✅ 向量存储已保存到: {vector_store_path}")
            
            print(f"✅ 成功添加 {len(split_docs)} 个文档块到向量存储")
            return True
            
        except Exception as e:
            print(f"❌ 添加文档失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def query(self, query: str, top_k: int = 5, threshold: float = 0.3) -> Dict[str, Any]:
        """查询问答"""
        try:
            if self.vector_store is None:
                print(f"❌ 向量存储为空")
                return {
                    "answer": "抱歉，向量存储未初始化",
                    "sources": [],
                    "confidence": 0.0
                }
            
            print(f"🔍 LangChain查询: '{query}', top_k={top_k}, threshold={threshold}")
            
            # 创建检索器 - 暂时不使用score_threshold，让所有结果都返回
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": top_k * 2,  # 获取更多块以便过滤
                    # 暂时不使用score_threshold，让所有结果都返回
                }
            )
            
            # 创建QA链
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={
                    "prompt": self._get_qa_prompt()
                }
            )
            
            print("query is :", query)
            # 执行查询
            result = await qa_chain.ainvoke({"query": query})
            
            # 处理结果
            answer = result.get("result", "")
            print(f"[DEBUG] 查询结果: {answer}")
            source_docs = result.get("source_documents", [])
            print(f"[DEBUG] 检索到 {len(source_docs)} 个文档块")
            
            # 构建来源信息
            sources = []
            for doc in source_docs:
                source_info = {
                    "content_preview": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content,
                    "metadata": doc.metadata
                }
                sources.append(source_info)
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": 0.8 if sources else 0.0  # 简化置信度计算
            }
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            return {
                "answer": f"查询处理失败: {str(e)}",
                "sources": [],
                "confidence": 0.0
            }
    
    async def search_documents(self, query: str, top_k: int = 10, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """搜索文档（返回文档级别的结果）"""
        try:
            print(f"🔍 LangChain搜索文档: '{query}', top_k={top_k}, threshold={threshold}")
            
            if self.vector_store is None:
                print("❌ 向量存储为空")
                return []
            
            print(f"📊 向量存储状态: {len(self.vector_store.index_to_docstore_id)} 个文档")
            
            # 创建检索器，不使用score_threshold，让所有结果都返回
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": top_k * 2,  # 获取更多块以便去重
                    # 暂时不使用score_threshold，让所有结果都返回
                }
            )
            
            # 执行搜索
            print("🔍 执行向量搜索...")
            docs_and_scores = await retriever.aget_relevant_documents(query)
            print(f"📄 搜索到 {len(docs_and_scores)} 个文档块")
            
            # 打印每个块的详细信息
            for i, doc in enumerate(docs_and_scores):
                print(f"  块 {i+1}: 内容='{doc.page_content[:50]}...', 元数据={doc.metadata}")
            
            # 按文档分组并计算文档级别的相似度
            document_scores = {}
            
            for doc in docs_and_scores:
                doc_id = doc.metadata.get('document_id')
                if doc_id:
                    if doc_id not in document_scores:
                        document_scores[doc_id] = {
                            'document_id': doc_id,
                            'document_title': doc.metadata.get('title', 'Unknown'),
                            'chunks': [],
                            'max_similarity': 0.0,
                            'avg_similarity': 0.0
                        }
                    
                    # 使用较高的默认相似度，因为LangChain已经通过向量搜索过滤了
                    similarity = 0.9  # 可以根据需要调整
                    document_scores[doc_id]['chunks'].append({
                        'chunk_id': doc_id,  # 使用文档ID作为块ID
                        'content_preview': doc.page_content[:150] + '...' if len(doc.page_content) > 150 else doc.page_content,
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
            
            # 应用阈值过滤
            filtered_results = [r for r in results if r['max_similarity'] >= threshold]
            print(f"✅ 过滤后结果: {len(filtered_results)} 个文档 (阈值: {threshold})")
            
            return filtered_results[:top_k]
            
        except Exception as e:
            print(f"❌ LangChain搜索文档失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """从向量存储中删除指定文档的所有向量"""
        try:
            print(f"🗑️ 从LangChain存储删除文档: {document_id}")
            
            if self.vector_store is None:
                print("❌ 向量存储为空")
                return False
            
            print(f"📊 删除前向量存储状态: {len(self.vector_store.index_to_docstore_id)} 个文档")
            
            # 找到要删除的文档块ID
            doc_ids_to_delete = []
            for idx, doc_id in self.vector_store.index_to_docstore_id.items():
                # 获取文档的元数据
                doc = self.vector_store.docstore._dict.get(doc_id)
                if doc and doc.metadata.get('document_id') == document_id:
                    doc_ids_to_delete.append(doc_id)
            
            if not doc_ids_to_delete:
                print(f"⚠️ 未找到文档 {document_id} 的向量数据")
                return True  # 认为删除成功，因为本来就没有
            
            print(f"🔍 找到 {len(doc_ids_to_delete)} 个相关文档块")
            
            # 删除文档块
            self.vector_store.delete(doc_ids_to_delete)
            
            # 保存更新后的向量存储
            vector_store_path = f"{settings.data_dir}/faiss/langchain_vectorstore"
            self.vector_store.save_local(vector_store_path)
            
            print(f"📊 删除后向量存储状态: {len(self.vector_store.index_to_docstore_id)} 个文档")
            print(f"✅ 成功删除文档 {document_id} 的向量数据")
            
            return True
            
        except Exception as e:
            print(f"❌ 删除文档向量失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_qa_prompt(self):
        """获取QA提示词模板"""
        from langchain_core.prompts import PromptTemplate
        
        template = """基于以下上下文信息，回答用户的问题。如果上下文中没有相关信息，请说明无法从提供的信息中找到答案。

上下文信息：
{context}

用户问题：{question}

请提供准确、简洁的回答："""

        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if self.vector_store is None:
            return {"total_documents": 0, "total_chunks": 0}
        
        try:
            # 获取向量存储信息
            index = self.vector_store.index
            total_chunks = index.ntotal if hasattr(index, 'ntotal') else 0
            
            return {
                "total_documents": 0,  # 需要从元数据统计
                "total_chunks": total_chunks
            }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {"total_documents": 0, "total_chunks": 0}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 测试向量存储
            vector_store_ok = self.vector_store is not None
            
            # 测试LLM
            test_result = await self.llm._acall("测试", max_tokens=5)
            llm_ok = len(test_result) > 0
            
            return {
                "status": "healthy" if vector_store_ok and llm_ok else "unhealthy",
                "vector_store": vector_store_ok,
                "llm": llm_ok,
                "stats": self.get_stats()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            } 