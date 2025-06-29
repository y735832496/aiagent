#!/usr/bin/env python3
"""
调试向量数据库查询过程
"""

import os
import sys
import asyncio
import time
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.langchain_service import LangChainRAGService


async def debug_vector_query_process():
    """调试向量数据库查询过程"""
    print("🔍 调试向量数据库查询过程")
    print("=" * 60)
    
    # 初始化服务
    print("🚀 初始化LangChain服务...")
    langchain_service = LangChainRAGService()
    
    if not langchain_service.vector_store:
        print("❌ 向量存储未初始化")
        return
    
    # 测试查询
    test_query = "什么是向量数据库？"
    print(f"\n📝 用户输入的自然语言查询: '{test_query}'")
    
    # 详细展示向量查询过程
    print("\n🔄 向量数据库查询过程:")
    print("=" * 40)
    
    # 1. 创建检索器
    print("1️⃣ 创建检索器...")
    retriever = langchain_service.vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 5,
            "score_threshold": 0.3
        }
    )
    print("   ✅ 检索器创建完成")
    
    # 2. 执行向量查询
    print("\n2️⃣ 执行向量数据库查询...")
    start_time = time.time()
    
    try:
        # 这里就是向量数据库查询！
        source_documents = await retriever.aget_relevant_documents(test_query)
        
        end_time = time.time()
        print(f"   ✅ 向量查询完成，耗时: {(end_time - start_time) * 1000:.2f} 毫秒")
        print(f"   📄 检索到 {len(source_documents)} 个相关文档")
        
        # 3. 显示查询结果
        print("\n3️⃣ 向量查询结果:")
        for i, doc in enumerate(source_documents):
            print(f"   📄 文档 {i+1}:")
            print(f"      - 内容: {doc.page_content[:100]}...")
            print(f"      - 元数据: {doc.metadata}")
        
        # 4. 展示完整的RAG流程
        print("\n4️⃣ 完整的RAG流程:")
        print("   📝 构建上下文...")
        context_parts = [doc.page_content for doc in source_documents]
        context = "\n\n".join(context_parts)
        print(f"      - 上下文长度: {len(context)} 字符")
        
        print("   🎯 构建提示词...")
        prompt_template = langchain_service._get_qa_prompt()
        formatted_prompt = prompt_template.format(
            context=context,
            question=test_query
        )
        print(f"      - 提示词长度: {len(formatted_prompt)} 字符")
        
        print("   🤖 调用LLM生成答案...")
        llm_response = await langchain_service.llm._acall(
            formatted_prompt,
            max_tokens=1000
        )
        print(f"      - LLM响应: {llm_response[:200]}...")
        
        print("\n✅ 完整的RAG流程完成！")
        
    except Exception as e:
        print(f"   ❌ 向量查询失败: {e}")
        import traceback
        traceback.print_exc()


async def debug_retriever_internals():
    """调试检索器内部实现"""
    print("\n🔧 调试检索器内部实现:")
    print("=" * 40)
    
    langchain_service = LangChainRAGService()
    
    if not langchain_service.vector_store:
        print("❌ 向量存储未初始化")
        return
    
    test_query = "向量数据库的优势"
    print(f"📝 测试查询: '{test_query}'")
    
    # 创建检索器
    retriever = langchain_service.vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 3,
            "score_threshold": 0.3
        }
    )
    
    print("\n🔍 检索器内部执行过程:")
    
    # 1. 查询向量化
    print("1️⃣ 查询向量化...")
    query_vector = langchain_service.embeddings.embed_query(test_query)
    print(f"   - 查询向量维度: {len(query_vector)}")
    print(f"   - 查询向量前5个值: {query_vector[:5]}")
    
    # 2. 向量相似度搜索
    print("\n2️⃣ 向量相似度搜索...")
    # 这里模拟FAISS的搜索过程
    index = langchain_service.vector_store.index
    print(f"   - FAISS索引中的向量数量: {index.ntotal}")
    print(f"   - FAISS索引维度: {index.d}")
    
    # 3. 执行搜索
    print("\n3️⃣ 执行向量搜索...")
    source_documents = await retriever.aget_relevant_documents(test_query)
    print(f"   - 搜索到 {len(source_documents)} 个相关文档")
    
    # 4. 显示搜索结果
    print("\n4️⃣ 搜索结果详情:")
    for i, doc in enumerate(source_documents):
        print(f"   📄 结果 {i+1}:")
        print(f"      - 内容预览: {doc.page_content[:80]}...")
        print(f"      - 文档ID: {doc.metadata.get('document_id', 'N/A')}")
        print(f"      - 标题: {doc.metadata.get('title', 'N/A')}")


async def compare_with_direct_search():
    """与直接搜索对比"""
    print("\n⚖️ 与直接搜索对比:")
    print("=" * 40)
    
    langchain_service = LangChainRAGService()
    
    if not langchain_service.vector_store:
        print("❌ 向量存储未初始化")
        return
    
    test_query = "向量数据库"
    print(f"📝 测试查询: '{test_query}'")
    
    # 方法1: 使用检索器（ainvoke内部使用的方法）
    print("\n🔍 方法1: 使用检索器 (ainvoke内部方法)")
    retriever = langchain_service.vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )
    
    start_time = time.time()
    retriever_results = await retriever.aget_relevant_documents(test_query)
    retriever_time = time.time() - start_time
    
    print(f"   - 检索器方法耗时: {retriever_time * 1000:.2f} 毫秒")
    print(f"   - 检索到 {len(retriever_results)} 个文档")
    
    # 方法2: 直接使用向量存储搜索
    print("\n🔍 方法2: 直接向量存储搜索")
    start_time = time.time()
    direct_results = langchain_service.vector_store.similarity_search(test_query, k=3)
    direct_time = time.time() - start_time
    
    print(f"   - 直接搜索耗时: {direct_time * 1000:.2f} 毫秒")
    print(f"   - 检索到 {len(direct_results)} 个文档")
    
    # 对比结果
    print("\n📊 结果对比:")
    print(f"   - 检索器方法: {len(retriever_results)} 个文档")
    print(f"   - 直接搜索: {len(direct_results)} 个文档")
    print(f"   - 时间差异: {abs(retriever_time - direct_time) * 1000:.2f} 毫秒")
    
    # 验证结果是否一致
    retriever_contents = [doc.page_content[:50] for doc in retriever_results]
    direct_contents = [doc.page_content[:50] for doc in direct_results]
    
    print(f"   - 结果一致性: {'✅ 一致' if retriever_contents == direct_contents else '❌ 不一致'}")


async def test_full_query_flow():
    """测试完整的query流程"""
    print("\n🧪 测试完整的query流程:")
    print("=" * 40)
    
    langchain_service = LangChainRAGService()
    
    if not langchain_service.vector_store:
        print("❌ 向量存储未初始化")
        return
    
    test_query = "向量数据库有什么特点？"
    print(f"📝 测试查询: '{test_query}'")
    
    try:
        # 使用完整的query方法
        start_time = time.time()
        result = await langchain_service.query(
            query=test_query,
            top_k=3,
            threshold=0.3
        )
        end_time = time.time()
        
        print(f"✅ 完整query流程完成，耗时: {(end_time - start_time) * 1000:.2f} 毫秒")
        print(f"📄 生成的答案: {result.get('answer', '')[:200]}...")
        print(f"📚 来源文档数: {len(result.get('sources', []))}")
        
        # 显示来源信息
        sources = result.get('sources', [])
        for i, source in enumerate(sources):
            print(f"   📄 来源 {i+1}: {source.get('content_preview', '')[:80]}...")
        
    except Exception as e:
        print(f"❌ query流程失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(debug_vector_query_process())
        asyncio.run(debug_retriever_internals())
        asyncio.run(compare_with_direct_search())
        asyncio.run(test_full_query_flow())
        print("\n✅ 调试完成")
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc() 