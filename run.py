#!/usr/bin/env python3
"""
Tag Demo 启动脚本
"""

import os
import sys
import subprocess
import uvicorn
from pathlib import Path

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    required_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"), 
        # ("chromadb", "chromadb"),  # 临时禁用
        ("sentence_transformers", "sentence_transformers"),
        # ("pydantic", "pydantic"),  # 临时禁用
        ("python_dotenv", "dotenv")
    ]
    
    missing_packages = []
    for package, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements-minimal.txt")
        return False
    
    print("✅ 依赖检查通过")
    return True

def create_env_file():
    """创建环境配置文件"""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 创建环境配置文件...")
        try:
            with open(env_example, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ 环境配置文件创建成功")
            print("⚠️  请根据需要编辑 .env 文件")
        except Exception as e:
            print(f"❌ 创建环境配置文件失败: {e}")
    elif env_file.exists():
        print("✅ 环境配置文件已存在")

def create_directories():
    """创建必要的目录"""
    print("📁 创建必要目录...")
    
    directories = [
        "data",
        "data/chroma", 
        "data/local",
        "data/uploads",
        "docs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ 目录创建完成")

def start_server(host="0.0.0.0", port=8000, reload=True):
    """启动服务器"""
    print(f"🚀 启动 Tag Demo 服务...")
    print(f"   地址: http://{host}:{port}")
    print(f"   热重载: {'开启' if reload else '关闭'}")
    print(f"   API文档: http://{host}:{port}/docs")
    print()
    
    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动服务失败: {e}")

def main():
    """主函数"""
    print("🏷️  Tag Demo 启动脚本")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 创建环境配置文件
    create_env_file()
    
    # 创建必要目录
    create_directories()
    
    print("=" * 50)
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="Tag Demo 启动脚本")
    parser.add_argument("--host", default="0.0.0.0", help="服务器地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--no-reload", action="store_true", help="禁用热重载")
    parser.add_argument("--test", action="store_true", help="运行测试")
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 运行测试...")
        try:
            subprocess.run([sys.executable, "test_demo.py"], check=True)
        except subprocess.CalledProcessError:
            print("❌ 测试失败")
            sys.exit(1)
        except FileNotFoundError:
            print("❌ 测试脚本未找到")
            sys.exit(1)
        return
    
    # 启动服务器
    start_server(
        host=args.host,
        port=args.port,
        reload=not args.no_reload
    )

if __name__ == "__main__":
    main() 