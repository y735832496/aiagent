#!/usr/bin/env python3
"""
检查FAISS向量存储的内存使用情况
"""

import os
import sys
import psutil
import gc
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.langchain_service import LangChainRAGService


def get_memory_usage() -> Dict[str, Any]:
    """获取当前进程的内存使用情况"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        "rss_mb": memory_info.rss / 1024 / 1024,  # 物理内存使用量(MB)
        "vms_mb": memory_info.vms / 1024 / 1024,  # 虚拟内存使用量(MB)
        "percent": process.memory_percent()  # 内存使用百分比
    }


def check_faiss_memory():
    """检查FAISS向量存储的内存使用情况"""
    print("🔍 检查FAISS向量存储内存使用情况")
    print("=" * 50)
    
    # 获取初始内存使用
    initial_memory = get_memory_usage()
    print(f"📊 初始内存使用: {initial_memory['rss_mb']:.2f} MB")
    
    # 初始化LangChain服务
    print("\n🚀 初始化LangChain服务...")
    langchain_service = LangChainRAGService()
    
    # 获取初始化后内存使用
    after_init_memory = get_memory_usage()
    print(f"📊 初始化后内存使用: {after_init_memory['rss_mb']:.2f} MB")
    print(f"📈 内存增长: {after_init_memory['rss_mb'] - initial_memory['rss_mb']:.2f} MB")
    
    # 获取向量存储统计信息
    stats = langchain_service.get_stats()
    print(f"\n📊 向量存储统计:")
    print(f"   - 文档块数量: {stats['total_chunks']}")
    
    if langchain_service.vector_store:
        # 获取FAISS索引信息
        index = langchain_service.vector_store.index
        print(f"   - FAISS索引类型: {type(index).__name__}")
        
        # 尝试获取向量维度
        try:
            if hasattr(index, 'd'):
                print(f"   - 向量维度: {index.d}")
            if hasattr(index, 'ntotal'):
                print(f"   - 向量数量: {index.ntotal}")
        except Exception as e:
            print(f"   - 无法获取索引详细信息: {e}")
        
        # 估算内存使用
        if hasattr(index, 'ntotal') and hasattr(index, 'd'):
            # 假设每个向量是float32类型(4字节)
            estimated_vector_memory = index.ntotal * index.d * 4 / 1024 / 1024  # MB
            print(f"   - 估算向量内存: {estimated_vector_memory:.2f} MB")
    
    # 检查文档存储
    if langchain_service.vector_store and hasattr(langchain_service.vector_store, 'docstore'):
        docstore = langchain_service.vector_store.docstore
        if hasattr(docstore, '_dict'):
            doc_count = len(docstore._dict)
            print(f"   - 文档存储数量: {doc_count}")
            
            # 估算文档存储内存
            total_text_length = 0
            for doc_id, doc in docstore._dict.items():
                if hasattr(doc, 'page_content'):
                    total_text_length += len(doc.page_content)
            
            estimated_doc_memory = total_text_length * 2 / 1024 / 1024  # 假设每个字符2字节
            print(f"   - 估算文档内存: {estimated_doc_memory:.2f} MB")
    
    print("\n💡 内存使用说明:")
    print("   - RSS: 物理内存使用量(实际占用)")
    print("   - VMS: 虚拟内存使用量(包括共享库)")
    print("   - 向量内存: FAISS索引中存储的向量数据")
    print("   - 文档内存: 文档文本和元数据")
    
    return langchain_service


if __name__ == "__main__":
    try:
        service = check_faiss_memory()
        print("\n✅ 内存检查完成")
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc() 