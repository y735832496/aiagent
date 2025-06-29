#!/usr/bin/env python3
"""
快速测试脚本
"""

import os
import sys
import asyncio
import requests
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

BASE_URL = "http://127.0.0.1:8000"


async def test_health():
    """测试健康检查"""
    print("🏥 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False


async def test_upload_document():
    """测试文档上传"""
    print("\n📤 测试文档上传...")
    
    # 创建测试文档
    test_content = """
    向量数据库是一种专门用于存储和检索向量数据的数据库系统。
    它能够高效地处理高维向量数据，支持相似性搜索和最近邻查询。
    
    主要特点：
    1. 高维向量存储：支持数百到数千维的向量数据
    2. 相似性搜索：基于向量相似度进行快速检索
    3. 高性能：优化的索引结构，支持大规模数据
    4. 多种距离度量：支持余弦相似度、欧几里得距离等
    
    应用场景：
    - 图像检索
    - 文本相似性搜索
    - 推荐系统
    - 机器学习模型服务
    """
    
    document = {
        "title": "向量数据库介绍",
        "content": test_content,
        "document_id": "test_vector_db_intro"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/documents",
            json=document,
            headers={"Content-Type": "application/json"}
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False


async def test_query():
    """测试查询功能"""
    print("\n🔍 测试查询功能...")
    
    query = {
        "query": "向量数据库有什么特点？",
        "top_k": 3,
        "threshold": 0.3
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json=query,
            headers={"Content-Type": "application/json"}
        )
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   答案: {result.get('answer', '')[:200]}...")
            print(f"   来源数: {len(result.get('sources', []))}")
            return True
        else:
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False


async def test_search():
    """测试搜索功能"""
    print("\n🔍 测试搜索功能...")
    
    query = {
        "query": "向量数据库",
        "top_k": 5,
        "threshold": 0.1
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/search",
            json=query,
            headers={"Content-Type": "application/json"}
        )
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"   结果数: {len(results)}")
            for i, result in enumerate(results):
                print(f"   结果 {i+1}: {result.get('document_title', 'Unknown')}")
            return True
        else:
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False


async def test_documents_list():
    """测试文档列表"""
    print("\n📚 测试文档列表...")
    
    try:
        response = requests.get(f"{BASE_URL}/documents")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            documents = response.json()
            print(f"   文档数: {len(documents)}")
            for doc in documents:
                print(f"   - {doc.get('title', 'Unknown')} (ID: {doc.get('document_id', 'Unknown')})")
            return True
        else:
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False


async def main():
    """主函数"""
    print("🧪 Tag Demo 快速测试")
    print("=" * 50)
    
    # 检查服务是否运行
    print("🔍 检查服务状态...")
    if not await test_health():
        print("❌ 服务未运行，请先启动服务")
        print("   运行命令: python run_debug.py")
        return
    
    print("✅ 服务运行正常")
    
    # 执行测试
    tests = [
        ("文档列表", test_documents_list),
        ("文档上传", test_upload_document),
        ("查询功能", test_query),
        ("搜索功能", test_search),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = await test_func()
            results[test_name] = success
            print(f"   {'✅ 通过' if success else '❌ 失败'}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            results[test_name] = False
    
    # 显示测试结果
    print(f"\n{'='*50}")
    print("📊 测试结果汇总:")
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\n🎯 总体结果: {passed}/{total} 通过")


if __name__ == "__main__":
    asyncio.run(main()) 