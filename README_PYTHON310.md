# Tag Demo - Python 3.10 环境配置指南

## 🎯 目标
解决ChromaDB + FastAPI + pydantic的兼容性问题，确保向量数据库功能100%可用。

## 🚀 快速开始

### 方法1：使用自动化脚本（推荐）

#### macOS/Linux用户：
```bash
# 给脚本执行权限
chmod +x setup_python310.sh

# 运行安装脚本
./setup_python310.sh
```

#### Windows用户：
```cmd
# 运行安装脚本
setup_python310.bat
```

### 方法2：手动安装

#### 1. 创建conda环境
```bash
# 创建Python 3.10环境
conda create -n tagdemo310 python=3.10 -y

# 激活环境
conda activate tagdemo310
```

#### 2. 安装依赖
```bash
# 升级pip
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

#### 3. 启动服务
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## 📋 环境要求

- **Python**: 3.10.x
- **Conda**: Anaconda或Miniconda
- **操作系统**: macOS, Linux, Windows

## 🔧 关键依赖版本

| 包名 | 版本 | 说明 |
|------|------|------|
| pydantic | 1.10.13 | 兼容ChromaDB |
| fastapi | 0.95.2 | 兼容pydantic 1.x |
| chromadb | 0.4.22 | 向量数据库 |
| uvicorn | 0.24.0 | ASGI服务器 |

## 🎮 使用脚本

### 启动服务
```bash
# macOS/Linux
./start_server.sh

# Windows
start_server.bat
```

### 测试API
```bash
# macOS/Linux
./test_api.sh

# Windows
test_api.bat
```

### 查看环境信息
```bash
# macOS/Linux
./env_info.sh

# Windows
env_info.bat
```

## 🌐 服务地址

- **API文档**: http://localhost:8001/docs
- **主页**: http://localhost:8001
- **健康检查**: http://localhost:8001/health

## 🧪 API测试示例

### 1. 上传文档
```bash
curl -X POST "http://localhost:8001/documents/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "这是一个测试文档，用于验证向量数据库功能。",
    "metadata": {
      "title": "测试文档",
      "author": "测试用户",
      "tags": ["测试", "向量数据库"]
    }
  }'
```

### 2. 搜索文档
```bash
curl -X POST "http://localhost:8001/query/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "向量数据库",
    "top_k": 5
  }'
```

### 3. 问答
```bash
curl -X POST "http://localhost:8001/query/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是向量数据库？",
    "top_k": 3
  }'
```

## 🔍 故障排除

### 问题1：conda命令未找到
**解决方案**: 安装Anaconda或Miniconda
```bash
# 下载地址
https://docs.conda.io/en/latest/miniconda.html
```

### 问题2：依赖安装失败
**解决方案**: 使用国内镜像源
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 问题3：端口被占用
**解决方案**: 更换端口
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

### 问题4：ChromaDB启动失败
**解决方案**: 检查Python版本
```bash
python --version  # 应该是Python 3.10.x
```

## 📁 项目结构

```
tagDemo/
├── app/
│   ├── services/
│   │   ├── chroma_storage.py    # ChromaDB存储后端
│   │   ├── faiss_storage.py     # FAISS存储后端（备用）
│   │   └── storage_factory.py   # 存储工厂
│   ├── api/
│   └── main.py
├── requirements.txt              # 依赖文件
├── setup_python310.sh           # 自动化安装脚本
├── setup_python310.bat          # Windows安装脚本
├── start_server.sh              # 启动脚本
├── test_api.sh                  # 测试脚本
└── env_info.sh                  # 环境信息脚本
```

## 🎉 成功标志

当看到以下输出时，说明环境配置成功：

```
✅ Python版本: Python 3.10.x
✅ pydantic版本: 1.10.13
✅ fastapi版本: 0.95.2
✅ chromadb版本: 0.4.22
✅ ChromaDB向量数据库已准备就绪！
```

## 🔄 切换回原环境

如果需要切换回原来的Python 3.13环境：

```bash
# 退出当前环境
conda deactivate

# 激活原环境
conda activate .venv  # 或其他环境名
```

## 📞 技术支持

如果遇到问题，请检查：
1. Python版本是否为3.10.x
2. 是否激活了正确的conda环境
3. 依赖版本是否匹配
4. 端口8001是否被占用

---

**🎯 现在您可以享受完整的ChromaDB向量数据库功能了！** 