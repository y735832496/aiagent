#!/usr/bin/env python3
"""
调试print语句测试
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


async def debug_test_actual_ainvoke():
    """调试版本的test_actual_ainvoke"""
    print("🧪 开始调试test_actual_ainvoke函数")
    print("=" * 50)
    
    try:
        print("1️⃣ 初始化LangChain服务...")
        langchain_service = LangChainRAGService()
        print("   ✅ LangChain服务初始化成功")
        
        print("\n2️⃣ 检查向量存储...")
        if not langchain_service.vector_store:
            print("   ❌ 向量存储未初始化")
            return
        print("   ✅ 向量存储已初始化")
        
        print("\n3️⃣ 设置测试查询...")
        test_query = "向量数据库有什么优势？"
        print(f"   📝 测试查询: '{test_query}'")
        
        print("\n4️⃣ 创建检索器...")
        retriever = langchain_service.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 3,
                "score_threshold": 0.3
            }
        )
        print("   ✅ 检索器创建成功")
        
        print("\n5️⃣ 创建QA链...")
        qa_chain = langchain_service.chain_type(
            llm=langchain_service.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={
                "prompt": langchain_service._get_qa_prompt()
            }
        )
        print("   ✅ QA链创建成功")
        
        print("\n6️⃣ 准备执行ainvoke...")
        print(f"   🔍 test_query is: {test_query}")  # 这行应该会打印
        print("   🚀 开始执行ainvoke...")
        
        start_time = time.time()
        result = await qa_chain.ainvoke({"query": test_query})
        end_time = time.time()
        
        print(f"   ✅ ainvoke执行成功，耗时: {(end_time - start_time) * 1000:.2f} 毫秒")
        print(f"   📄 答案: {result.get('result', '')[:200]}...")
        print(f"   📚 来源文档数: {len(result.get('source_documents', []))}")
        
    except Exception as e:
        print(f"   ❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("🐛 开始调试print语句问题")
    print("=" * 50)
    
    await debug_test_actual_ainvoke()
    
    print("\n✅ 调试完成")


if __name__ == "__main__":
    asyncio.run(main()) 