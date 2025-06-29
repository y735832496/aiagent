#!/usr/bin/env python3
"""
分析ainvoke的具体实现过程
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


async def analyze_ainvoke_process():
    """分析ainvoke的完整实现过程"""
    print("🔍 分析ainvoke的具体实现过程")
    print("=" * 60)
    
    # 初始化服务
    print("🚀 初始化LangChain服务...")
    langchain_service = LangChainRAGService()
    
    if not langchain_service.vector_store:
        print("❌ 向量存储未初始化")
        return
    
    # 测试查询
    test_query = "什么是向量数据库？"
    print(f"\n📝 测试查询: '{test_query}'")
    
    # 详细分析ainvoke的执行过程
    print("\n🔄 ainvoke执行过程分析:")
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
    
    # 2. 创建QA链
    print("\n2️⃣ 创建QA链...")
    qa_chain = langchain_service.chain_type(
        llm=langchain_service.llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={
            "prompt": langchain_service._get_qa_prompt()
        }
    )
    print("   ✅ QA链创建完成")
    
    # 3. 执行ainvoke
    print("\n3️⃣ 执行ainvoke...")
    start_time = time.time()
    
    try:
        # 这里模拟ainvoke的内部执行过程
        result = await simulate_ainvoke_process(
            qa_chain, 
            test_query, 
            langchain_service
        )
        
        end_time = time.time()
        print(f"   ✅ ainvoke执行完成，耗时: {(end_time - start_time) * 1000:.2f} 毫秒")
        
        # 4. 分析结果
        print("\n4️⃣ 结果分析:")
        print(f"   - 答案: {result.get('result', '')[:100]}...")
        print(f"   - 来源文档数: {len(result.get('source_documents', []))}")
        
        # 显示来源文档
        source_docs = result.get('source_documents', [])
        for i, doc in enumerate(source_docs):
            print(f"   - 来源 {i+1}: {doc.page_content[:50]}...")
            print(f"     元数据: {doc.metadata}")
        
    except Exception as e:
        print(f"   ❌ ainvoke执行失败: {e}")
        import traceback
        traceback.print_exc()


async def simulate_ainvoke_process(qa_chain, query: str, langchain_service):
    """模拟ainvoke的内部执行过程"""
    print("   🔍 模拟ainvoke内部执行过程:")
    
    # 步骤1: 检索相关文档
    print("   📄 步骤1: 检索相关文档...")
    retriever = qa_chain.retriever
    source_documents = await retriever.aget_relevant_documents(query)
    print(f"      - 检索到 {len(source_documents)} 个相关文档")
    
    # 步骤2: 构建上下文
    print("   📝 步骤2: 构建上下文...")
    context = ""
    if source_documents:
        # 使用stuff方法：将所有文档内容拼接
        context_parts = [doc.page_content for doc in source_documents]
        context = "\n\n".join(context_parts)
        print(f"      - 上下文长度: {len(context)} 字符")
    
    # 步骤3: 构建提示词
    print("   🎯 步骤3: 构建提示词...")
    prompt_template = qa_chain.combine_documents_chain.prompt
    formatted_prompt = prompt_template.format(
        context=context,
        question=query
    )
    print(f"      - 提示词长度: {len(formatted_prompt)} 字符")
    
    # 步骤4: 调用LLM
    print("   🤖 步骤4: 调用LLM...")
    llm_response = await langchain_service.llm._acall(
        formatted_prompt,
        max_tokens=1000
    )
    print(f"      - LLM响应长度: {len(llm_response)} 字符")
    
    # 步骤5: 构建最终结果
    print("   📊 步骤5: 构建最终结果...")
    result = {
        "result": llm_response,
        "source_documents": source_documents
    }
    
    return result


def analyze_chain_types():
    """分析不同的chain_type"""
    print("\n📚 分析不同的chain_type:")
    print("=" * 40)
    
    chain_types = {
        "stuff": {
            "description": "将所有检索到的文档内容直接拼接",
            "优点": "简单直接，保留所有信息",
            "缺点": "可能超出LLM的上下文长度限制",
            "适用场景": "文档数量少，内容简短"
        },
        "map_reduce": {
            "description": "先对每个文档单独处理，再合并结果",
            "优点": "可以处理大量文档，并行处理",
            "缺点": "可能丢失文档间的关联信息",
            "适用场景": "文档数量多，需要并行处理"
        },
        "refine": {
            "description": "迭代式处理，逐步完善答案",
            "优点": "答案质量高，可以处理复杂问题",
            "缺点": "处理时间长，成本高",
            "适用场景": "需要高质量答案的复杂查询"
        }
    }
    
    for chain_type, info in chain_types.items():
        print(f"\n🔗 {chain_type.upper()}:")
        print(f"   - 描述: {info['description']}")
        print(f"   - 优点: {info['优点']}")
        print(f"   - 缺点: {info['缺点']}")
        print(f"   - 适用场景: {info['适用场景']}")


def analyze_retriever_methods():
    """分析检索器的方法"""
    print("\n🔍 分析检索器的方法:")
    print("=" * 40)
    
    methods = {
        "aget_relevant_documents": {
            "description": "异步获取相关文档",
            "参数": "query: str",
            "返回": "List[Document]",
            "用途": "在ainvoke中用于检索相关文档"
        },
        "get_relevant_documents": {
            "description": "同步获取相关文档",
            "参数": "query: str", 
            "返回": "List[Document]",
            "用途": "在invoke中用于检索相关文档"
        },
        "aget_relevant_documents_with_score": {
            "description": "异步获取相关文档及相似度分数",
            "参数": "query: str",
            "返回": "List[Tuple[Document, float]]",
            "用途": "需要相似度分数时使用"
        }
    }
    
    for method, info in methods.items():
        print(f"\n📋 {method}:")
        print(f"   - 描述: {info['description']}")
        print(f"   - 参数: {info['参数']}")
        print(f"   - 返回: {info['返回']}")
        print(f"   - 用途: {info['用途']}")


async def test_actual_ainvoke():
    """测试实际的ainvoke调用"""
    print("\n🧪 测试实际的ainvoke调用:")
    print("=" * 40)
    
    langchain_service = LangChainRAGService()
    
    if not langchain_service.vector_store:
        print("❌ 向量存储未初始化")
        return
    
    test_query = "向量数据库有什么优势？"
    print(f"📝 测试查询: '{test_query}'")
    
    try:
        # 创建检索器
        retriever = langchain_service.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 3,
                "score_threshold": 0.3
            }
        )
        
        # 创建QA链
        qa_chain = langchain_service.chain_type(
            llm=langchain_service.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={
                "prompt": langchain_service._get_qa_prompt()
            }
        )
        
        # 执行ainvoke
        start_time = time.time()
        print(f"test_query is :{test_query}")
        result = await qa_chain.ainvoke({"query": test_query})
        end_time = time.time()
        
        print(f"✅ ainvoke执行成功，耗时: {(end_time - start_time) * 1000:.2f} 毫秒")
        print(f"📄 答案: {result.get('result', '')[:200]}...")
        print(f"📚 来源文档数: {len(result.get('source_documents', []))}")
        
    except Exception as e:
        print(f"❌ ainvoke执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(analyze_ainvoke_process())
        analyze_chain_types()
        analyze_retriever_methods()
        asyncio.run(test_actual_ainvoke())
        print("\n✅ 分析完成")
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc() 