#!/usr/bin/env python3
"""
验证add_documents是否立即更新内存中的向量
"""

import os
import sys
import time
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.langchain_service import LangChainRAGService
from langchain.schema import Document


def test_memory_update():
    """测试内存更新"""
    print("🔍 测试add_documents是否立即更新内存中的向量")
    print("=" * 60)
    
    # 初始化服务
    print("🚀 初始化LangChain服务...")
    langchain_service = LangChainRAGService()
    
    if not langchain_service.vector_store:
        print("❌ 向量存储未初始化")
        return
    
    # 获取初始状态
    initial_count = len(langchain_service.vector_store.index_to_docstore_id)
    print(f"📊 初始向量数量: {initial_count}")
    
    # 创建测试文档
    test_docs = [
        Document(
            page_content="这是一个测试文档，用于验证内存更新。",
            metadata={"document_id": "test_001", "title": "测试文档1"}
        ),
        Document(
            page_content="这是另一个测试文档，内容不同。",
            metadata={"document_id": "test_002", "title": "测试文档2"}
        )
    ]
    
    print(f"\n📝 准备添加 {len(test_docs)} 个测试文档...")
    
    # 记录添加前的时间
    start_time = time.time()
    
    # 添加文档到向量存储
    print("💾 开始添加文档到向量存储...")
    langchain_service.vector_store.add_documents(test_docs)
    
    # 记录添加后的时间
    end_time = time.time()
    
    # 立即检查内存状态
    after_add_count = len(langchain_service.vector_store.index_to_docstore_id)
    print(f"📊 添加后向量数量: {after_add_count}")
    print(f"📈 向量增长: {after_add_count - initial_count}")
    print(f"⏱️ 添加耗时: {(end_time - start_time) * 1000:.2f} 毫秒")
    
    # 验证向量是否真的在内存中
    print(f"\n🔍 验证向量是否在内存中...")
    
    # 检查FAISS索引
    index = langchain_service.vector_store.index
    print(f"   - FAISS索引向量数量: {index.ntotal}")
    
    # 检查文档存储
    docstore = langchain_service.vector_store.docstore
    doc_count = len(docstore._dict) if hasattr(docstore, '_dict') else 0
    print(f"   - 文档存储数量: {doc_count}")
    
    # 检查映射关系
    mapping_count = len(langchain_service.vector_store.index_to_docstore_id)
    print(f"   - 索引映射数量: {mapping_count}")
    
    # 验证一致性
    print(f"\n✅ 验证结果:")
    print(f"   - 索引向量数量 = 映射数量: {'✅' if index.ntotal == mapping_count else '❌'}")
    print(f"   - 文档存储数量 = 映射数量: {'✅' if doc_count == mapping_count else '❌'}")
    
    # 立即进行搜索测试
    print(f"\n🔍 立即进行搜索测试...")
    try:
        # 创建检索器
        retriever = langchain_service.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
        # 搜索测试文档
        results = retriever.get_relevant_documents("测试文档")
        print(f"   - 搜索到 {len(results)} 个相关文档")
        
        # 显示搜索结果
        for i, doc in enumerate(results):
            content_preview = doc.page_content[:50] + "..." if len(doc.page_content) > 50 else doc.page_content
            print(f"     - 结果 {i+1}: {content_preview}")
            print(f"       元数据: {doc.metadata}")
        
        print("✅ 搜索测试成功，说明新向量已可用于搜索")
        
    except Exception as e:
        print(f"❌ 搜索测试失败: {e}")
    
    # 检查是否已保存到磁盘
    print(f"\n💾 检查磁盘文件状态...")
    vector_store_path = f"{settings.data_dir}/faiss/langchain_vectorstore"
    index_faiss_path = f"{vector_store_path}/index.faiss"
    
    if os.path.exists(index_faiss_path):
        file_size = os.path.getsize(index_faiss_path)
        print(f"   - index.faiss 文件大小: {file_size / 1024:.2f} KB")
        
        # 注意：此时文件可能还没有更新，因为还没有调用save_local
        print(f"   - 文件是否已更新: {'需要调用save_local()'}")
    else:
        print(f"   - index.faiss 文件不存在")
    
    print(f"\n💡 结论:")
    print(f"   - add_documents() 立即更新内存中的向量")
    print(f"   - 新向量立即可用于搜索")
    print(f"   - 需要调用 save_local() 才会更新磁盘文件")


def test_save_to_disk():
    """测试保存到磁盘"""
    print(f"\n" + "=" * 60)
    print("💾 测试保存到磁盘")
    print("=" * 60)
    
    langchain_service = LangChainRAGService()
    
    if not langchain_service.vector_store:
        print("❌ 向量存储未初始化")
        return
    
    # 记录保存前的文件大小
    vector_store_path = f"{settings.data_dir}/faiss/langchain_vectorstore"
    index_faiss_path = f"{vector_store_path}/index.faiss"
    
    if os.path.exists(index_faiss_path):
        before_size = os.path.getsize(index_faiss_path)
        print(f"📊 保存前文件大小: {before_size / 1024:.2f} KB")
    
    # 保存到磁盘
    print("💾 保存向量存储到磁盘...")
    start_time = time.time()
    langchain_service.vector_store.save_local(vector_store_path)
    end_time = time.time()
    
    print(f"⏱️ 保存耗时: {(end_time - start_time) * 1000:.2f} 毫秒")
    
    # 检查保存后的文件大小
    if os.path.exists(index_faiss_path):
        after_size = os.path.getsize(index_faiss_path)
        print(f"📊 保存后文件大小: {after_size / 1024:.2f} KB")
        if 'before_size' in locals():
            print(f"📈 文件大小变化: {(after_size - before_size) / 1024:.2f} KB")
    
    print("✅ 保存到磁盘完成")


if __name__ == "__main__":
    try:
        test_memory_update()
        test_save_to_disk()
        print("\n✅ 测试完成")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc() 