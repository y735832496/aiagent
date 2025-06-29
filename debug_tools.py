#!/usr/bin/env python3
"""
调试工具集合
"""

import os
import sys
import asyncio
import json
import time
from typing import Dict, Any, List
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.services.langchain_service import LangChainRAGService
from app.services.document_service import DocumentService
from app.services.query_service import QueryService


class DebugTools:
    """调试工具类"""
    
    def __init__(self):
        self.langchain_service = None
        self.document_service = None
        self.query_service = None
    
    async def init_services(self):
        """初始化所有服务"""
        print("🚀 初始化服务...")
        
        try:
            self.langchain_service = LangChainRAGService()
            self.document_service = DocumentService()
            self.query_service = QueryService()
            print("✅ 服务初始化成功")
        except Exception as e:
            print(f"❌ 服务初始化失败: {e}")
            raise
    
    def check_environment(self):
        """检查环境配置"""
        print("\n🔍 环境检查:")
        print("=" * 40)
        
        # 检查配置
        print(f"📁 数据目录: {settings.data_dir}")
        print(f"🔑 DeepSeek API URL: {settings.deepseek_api_url}")
        print(f"🤖 模型名称: {settings.model_name}")
        
        # 检查目录
        data_dir = Path(settings.data_dir)
        print(f"📂 数据目录存在: {data_dir.exists()}")
        
        # 检查FAISS文件
        faiss_dir = data_dir / "faiss" / "langchain_vectorstore"
        print(f"📄 FAISS目录存在: {faiss_dir.exists()}")
        if faiss_dir.exists():
            index_file = faiss_dir / "index.faiss"
            pkl_file = faiss_dir / "index.pkl"
            print(f"   - index.faiss: {index_file.exists()} ({index_file.stat().st_size if index_file.exists() else 0} bytes)")
            print(f"   - index.pkl: {pkl_file.exists()} ({pkl_file.stat().st_size if pkl_file.exists() else 0} bytes)")
    
    def check_vector_store(self):
        """检查向量存储状态"""
        print("\n📊 向量存储检查:")
        print("=" * 40)
        
        if not self.langchain_service or not self.langchain_service.vector_store:
            print("❌ 向量存储未初始化")
            return
        
        vector_store = self.langchain_service.vector_store
        print(f"📄 文档块数量: {len(vector_store.index_to_docstore_id)}")
        print(f"🔢 FAISS索引向量数: {vector_store.index.ntotal}")
        print(f"📏 向量维度: {vector_store.index.d}")
        
        # 显示文档列表
        print("\n📚 已索引的文档:")
        doc_ids = set()
        for idx, doc_id in vector_store.index_to_docstore_id.items():
            doc = vector_store.docstore._dict.get(doc_id)
            if doc:
                doc_id_real = doc.metadata.get('document_id', doc_id)
                doc_ids.add(doc_id_real)
        
        for doc_id in sorted(doc_ids):
            print(f"   - {doc_id}")
    
    async def test_upload(self, file_path: str):
        """测试文档上传"""
        print(f"\n📤 测试文档上传: {file_path}")
        print("=" * 40)
        
        if not Path(file_path).exists():
            print(f"❌ 文件不存在: {file_path}")
            return
        
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建文档对象
            document = {
                "title": Path(file_path).stem,
                "content": content,
                "document_id": f"test_{int(time.time())}"
            }
            
            # 上传到原有存储
            print("📝 上传到原有存储...")
            success = self.document_service.add_document(document)
            print(f"   结果: {'✅ 成功' if success else '❌ 失败'}")
            
            # 上传到LangChain存储
            print("🔗 上传到LangChain存储...")
            success = self.langchain_service.add_documents([document])
            print(f"   结果: {'✅ 成功' if success else '❌ 失败'}")
            
            # 检查上传后的状态
            self.check_vector_store()
            
        except Exception as e:
            print(f"❌ 上传失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_query(self, query: str):
        """测试查询功能"""
        print(f"\n🔍 测试查询: '{query}'")
        print("=" * 40)
        
        try:
            # 测试LangChain查询
            print("🤖 LangChain查询:")
            start_time = time.time()
            result = await self.langchain_service.query(query, top_k=3, threshold=0.3)
            end_time = time.time()
            
            print(f"   耗时: {(end_time - start_time) * 1000:.2f} 毫秒")
            print(f"   答案: {result.get('answer', '')[:200]}...")
            print(f"   来源数: {len(result.get('sources', []))}")
            
            # 显示来源
            sources = result.get('sources', [])
            for i, source in enumerate(sources):
                print(f"   来源 {i+1}: {source.get('content_preview', '')[:80]}...")
            
            # 测试搜索功能
            print("\n🔍 LangChain搜索:")
            start_time = time.time()
            search_results = await self.langchain_service.search_documents(query, top_k=3, threshold=0.1)
            end_time = time.time()
            
            print(f"   耗时: {(end_time - start_time) * 1000:.2f} 毫秒")
            print(f"   结果数: {len(search_results)}")
            
            for i, result in enumerate(search_results):
                print(f"   结果 {i+1}: {result.get('document_title', 'Unknown')} (相似度: {result.get('max_similarity', 0):.3f})")
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            import traceback
            traceback.print_exc()
    
    def check_memory_usage(self):
        """检查内存使用情况"""
        print("\n💾 内存使用检查:")
        print("=" * 40)
        
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            print(f"📊 物理内存: {memory_info.rss / 1024 / 1024:.2f} MB")
            print(f"📊 虚拟内存: {memory_info.vms / 1024 / 1024:.2f} MB")
            print(f"📊 内存使用率: {process.memory_percent():.2f}%")
            
            if self.langchain_service and self.langchain_service.vector_store:
                vector_store = self.langchain_service.vector_store
                # 估算向量内存
                vector_memory = vector_store.index.ntotal * vector_store.index.d * 4 / 1024 / 1024
                print(f"🔢 向量内存估算: {vector_memory:.2f} MB")
                
        except ImportError:
            print("⚠️ 需要安装 psutil: pip install psutil")
        except Exception as e:
            print(f"❌ 内存检查失败: {e}")
    
    def export_debug_info(self, filename: str = "debug_info.json"):
        """导出调试信息"""
        print(f"\n📤 导出调试信息到: {filename}")
        print("=" * 40)
        
        debug_info = {
            "timestamp": time.time(),
            "environment": {
                "data_dir": settings.data_dir,
                "deepseek_api_url": settings.deepseek_api_url,
                "model_name": settings.model_name
            },
            "vector_store": {}
        }
        
        if self.langchain_service and self.langchain_service.vector_store:
            vector_store = self.langchain_service.vector_store
            debug_info["vector_store"] = {
                "document_count": len(vector_store.index_to_docstore_id),
                "index_vectors": vector_store.index.ntotal,
                "vector_dimension": vector_store.index.d,
                "documents": []
            }
            
            # 收集文档信息
            doc_ids = set()
            for idx, doc_id in vector_store.index_to_docstore_id.items():
                doc = vector_store.docstore._dict.get(doc_id)
                if doc:
                    doc_id_real = doc.metadata.get('document_id', doc_id)
                    if doc_id_real not in doc_ids:
                        doc_ids.add(doc_id_real)
                        debug_info["vector_store"]["documents"].append({
                            "document_id": doc_id_real,
                            "title": doc.metadata.get('title', 'Unknown'),
                            "chunk_count": 0
                        })
            
            # 计算每个文档的块数
            for doc in debug_info["vector_store"]["documents"]:
                doc_id = doc["document_id"]
                chunk_count = sum(1 for idx, stored_doc_id in vector_store.index_to_docstore_id.items()
                                if vector_store.docstore._dict.get(stored_doc_id, {}).metadata.get('document_id') == doc_id)
                doc["chunk_count"] = chunk_count
        
        # 保存到文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(debug_info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 调试信息已保存到: {filename}")


async def main():
    """主函数"""
    print("🐛 Tag Demo 调试工具")
    print("=" * 50)
    
    debug_tools = DebugTools()
    
    try:
        # 初始化服务
        await debug_tools.init_services()
        
        # 环境检查
        debug_tools.check_environment()
        
        # 向量存储检查
        debug_tools.check_vector_store()
        
        # 内存使用检查
        debug_tools.check_memory_usage()
        
        # 导出调试信息
        debug_tools.export_debug_info()
        
        print("\n✅ 调试检查完成")
        
        # 交互式调试
        print("\n🔧 交互式调试选项:")
        print("1. 测试文档上传")
        print("2. 测试查询功能")
        print("3. 重新检查状态")
        print("4. 退出")
        
        while True:
            choice = input("\n请选择操作 (1-4): ").strip()
            
            if choice == "1":
                file_path = input("请输入文件路径: ").strip()
                if file_path:
                    await debug_tools.test_upload(file_path)
            
            elif choice == "2":
                query = input("请输入查询内容: ").strip()
                if query:
                    await debug_tools.test_query(query)
            
            elif choice == "3":
                debug_tools.check_vector_store()
                debug_tools.check_memory_usage()
            
            elif choice == "4":
                print("👋 退出调试工具")
                break
            
            else:
                print("❌ 无效选择，请重新输入")
    
    except Exception as e:
        print(f"❌ 调试工具运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 