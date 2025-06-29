#!/usr/bin/env python3
"""
分析FAISS文件的内容和结构
"""

import os
import sys
import faiss
import pickle
import numpy as np
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings


def analyze_faiss_files():
    """分析FAISS文件的内容"""
    print("🔍 分析FAISS文件内容")
    print("=" * 50)
    
    vector_store_path = f"{settings.data_dir}/faiss/langchain_vectorstore"
    
    # 检查文件是否存在
    index_faiss_path = f"{vector_store_path}/index.faiss"
    index_pkl_path = f"{vector_store_path}/index.pkl"
    
    print(f"📁 向量存储路径: {vector_store_path}")
    print(f"📄 index.faiss 文件: {'✅ 存在' if os.path.exists(index_faiss_path) else '❌ 不存在'}")
    print(f"📄 index.pkl 文件: {'✅ 存在' if os.path.exists(index_pkl_path) else '❌ 不存在'}")
    
    if not os.path.exists(index_faiss_path):
        print("❌ index.faiss 文件不存在")
        return
    
    # 分析 index.faiss 文件
    print(f"\n📊 index.faiss 文件分析:")
    print(f"   - 文件大小: {os.path.getsize(index_faiss_path) / 1024:.2f} KB")
    
    try:
        # 直接读取FAISS索引
        index = faiss.read_index(index_faiss_path)
        print(f"   - 索引类型: {type(index).__name__}")
        print(f"   - 向量维度: {index.d}")
        print(f"   - 向量数量: {index.ntotal}")
        print(f"   - 是否已训练: {index.is_trained}")
        
        # 计算实际存储的向量数据大小
        actual_vector_size = index.ntotal * index.d * 4  # float32 = 4字节
        print(f"   - 向量数据大小: {actual_vector_size / 1024:.2f} KB")
        
        # 获取一些向量样本
        if index.ntotal > 0:
            vectors = index.reconstruct_n(0, min(3, index.ntotal))
            print(f"   - 前{min(3, index.ntotal)}个向量的形状: {vectors.shape}")
            print(f"   - 向量数据类型: {vectors.dtype}")
            
            # 显示第一个向量的前10个值
            if vectors.size > 0:
                first_vector = vectors[0]
                print(f"   - 第一个向量前10个值: {first_vector[:10]}")
        
    except Exception as e:
        print(f"   - 读取FAISS索引失败: {e}")
    
    # 分析 index.pkl 文件
    if os.path.exists(index_pkl_path):
        print(f"\n📊 index.pkl 文件分析:")
        print(f"   - 文件大小: {os.path.getsize(index_pkl_path) / 1024:.2f} KB")
        
        try:
            with open(index_pkl_path, 'rb') as f:
                pkl_data = pickle.load(f)
            
            print(f"   - 数据类型: {type(pkl_data)}")
            
            if isinstance(pkl_data, dict):
                print(f"   - 字典键: {list(pkl_data.keys())}")
                
                # 分析文档存储
                if 'docstore' in pkl_data:
                    docstore = pkl_data['docstore']
                    print(f"   - 文档存储类型: {type(docstore)}")
                    
                    if hasattr(docstore, '_dict'):
                        doc_count = len(docstore._dict)
                        print(f"   - 文档数量: {doc_count}")
                        
                        # 显示前几个文档的信息
                        for i, (doc_id, doc) in enumerate(list(docstore._dict.items())[:3]):
                            print(f"     - 文档 {i+1}: ID={doc_id}")
                            if hasattr(doc, 'page_content'):
                                content_preview = doc.page_content[:50] + "..." if len(doc.page_content) > 50 else doc.page_content
                                print(f"       内容预览: {content_preview}")
                            if hasattr(doc, 'metadata'):
                                print(f"       元数据: {doc.metadata}")
                
                # 分析索引映射
                if 'index_to_docstore_id' in pkl_data:
                    mapping = pkl_data['index_to_docstore_id']
                    print(f"   - 索引映射类型: {type(mapping)}")
                    print(f"   - 映射数量: {len(mapping)}")
                    print(f"   - 映射示例: {dict(list(mapping.items())[:3])}")
            
        except Exception as e:
            print(f"   - 读取PKL文件失败: {e}")
    
    print(f"\n💡 FAISS文件说明:")
    print(f"   - index.faiss: 存储向量索引数据（二进制格式）")
    print(f"   - index.pkl: 存储文档内容和元数据（Python序列化格式）")
    print(f"   - 两个文件配合使用，实现完整的向量存储")


def compare_memory_vs_disk():
    """比较内存和磁盘中的数据"""
    print(f"\n🔄 比较内存和磁盘中的数据")
    print("=" * 50)
    
    # 导入LangChain服务
    from app.services.langchain_service import LangChainRAGService
    
    # 初始化服务（从磁盘加载）
    print("🚀 从磁盘加载FAISS数据到内存...")
    langchain_service = LangChainRAGService()
    
    if langchain_service.vector_store:
        # 内存中的数据
        memory_index = langchain_service.vector_store.index
        memory_docstore = langchain_service.vector_store.docstore
        
        print(f"📊 内存中的数据:")
        print(f"   - 向量数量: {memory_index.ntotal}")
        print(f"   - 向量维度: {memory_index.d}")
        print(f"   - 文档数量: {len(memory_docstore._dict) if hasattr(memory_docstore, '_dict') else 'N/A'}")
        
        # 磁盘中的数据
        vector_store_path = f"{settings.data_dir}/faiss/langchain_vectorstore"
        disk_index = faiss.read_index(f"{vector_store_path}/index.faiss")
        
        print(f"📊 磁盘中的数据:")
        print(f"   - 向量数量: {disk_index.ntotal}")
        print(f"   - 向量维度: {disk_index.d}")
        
        # 比较
        print(f"📊 比较结果:")
        print(f"   - 向量数量一致: {'✅' if memory_index.ntotal == disk_index.ntotal else '❌'}")
        print(f"   - 向量维度一致: {'✅' if memory_index.d == disk_index.d else '❌'}")
        
        # 验证向量内容是否一致
        if memory_index.ntotal > 0 and disk_index.ntotal > 0:
            memory_vectors = memory_index.reconstruct_n(0, min(3, memory_index.ntotal))
            disk_vectors = disk_index.reconstruct_n(0, min(3, disk_index.ntotal))
            
            vectors_match = np.array_equal(memory_vectors, disk_vectors)
            print(f"   - 向量内容一致: {'✅' if vectors_match else '❌'}")


if __name__ == "__main__":
    try:
        analyze_faiss_files()
        compare_memory_vs_disk()
        print("\n✅ 分析完成")
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc() 