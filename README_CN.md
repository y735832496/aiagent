# 🏷️ Tag Demo - 基于向量数据库的文档检索系统

这是一个完整的基于向量数据库的文档检索和问答系统，支持多种存储后端，集成了现代AI技术栈。

## ✨ 功能特性

### 📚 文档存储
- **向量数据库**: ChromaDB (核心存储)
- **结构化存储**: MySQL, MongoDB, Elasticsearch
- **本地存储**: JSON/CSV 文件
- **混合存储**: 向量+结构化数据

### 🔧 文档处理流程
- **文档预处理**: 智能分块、内容清洗
- **向量化**: 使用 sentence-transformers 模型
- **存储与索引**: 向量和原始文本关联存储
- **元数据提取**: 自动提取文档特征

### 🔍 检索问答
- **向量检索**: 高精度相似度搜索
- **上下文构建**: 智能文本拼接
- **问答生成**: 调用 DeepSeek 大模型
- **置信度评估**: 基于相似度的质量评估

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   文档输入      │    │   查询输入      │    │   结果输出      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▲
┌─────────────────┐    ┌─────────────────┐              │
│   文本处理      │    │   查询处理      │              │
│   - 分块        │    │   - 向量化      │              │
│   - 清洗        │    │   - 检索        │              │
└─────────┬───────┘    └─────────┬───────┘              │
          │                      │                      │
          ▼                      ▼                      │
┌─────────────────┐    ┌─────────────────┐              │
│   向量化        │    │   向量检索      │              │
│   - Embedding   │    │   - 相似度计算  │              │
│   - 存储        │    │   - Top-K 检索  │              │
└─────────┬───────┘    └─────────┬───────┘              │
          │                      │                      │
          ▼                      ▼                      │
┌─────────────────┐    ┌─────────────────┐              │
│   存储后端      │    │   上下文构建    │              │
│   - ChromaDB    │    │   - 文本拼接    │              │
│   - MySQL       │    │   - 格式化      │              │
│   - MongoDB     │    └─────────┬───────┘              │
│   - ES          │              │                      │
└─────────────────┘              ▼                      │
                         ┌─────────────────┐            │
                         │   LLM 生成      │            │
                         │   - DeepSeek    │            │
                         │   - 答案生成    │            │
                         └─────────────────┘            │
                                  │                      │
                                  └──────────────────────┘
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd tagDemo

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境

```bash
# 复制环境配置文件
cp env.example .env

# 编辑配置文件（可选）
# 主要配置项：
# - STORAGE_BACKEND: 存储后端选择
# - DEEPSEEK_API_KEY: DeepSeek API密钥
# - EMBEDDING_MODEL: 向量化模型
```

### 3. 启动服务

```bash
# 使用启动脚本（推荐）
python run.py

# 或直接使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问系统

- **主页**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc

### 5. 运行测试

```bash
# 运行完整测试
python run.py --test

# 或单独运行测试脚本
python test_demo.py
```

## 📖 API 接口

### 文档管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/documents/upload` | 上传文档 |
| POST | `/api/documents/upload-text` | 上传文本文档 |
| GET | `/api/documents/list` | 获取文档列表 |
| GET | `/api/documents/{id}` | 获取单个文档 |
| DELETE | `/api/documents/{id}` | 删除文档 |
| GET | `/api/documents/stats/summary` | 获取统计信息 |

### 查询问答

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/query/ask` | 问答接口 |
| GET | `/api/query/search` | 搜索文档 |
| GET | `/api/query/suggestions` | 获取查询建议 |
| GET | `/api/query/health` | 查询服务健康检查 |

### 健康检查

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/health` | 系统健康检查 |
| GET | `/api/health/storage` | 存储后端健康检查 |

## 🔧 配置说明

### 存储后端配置

支持多种存储后端，可通过 `STORAGE_BACKEND` 环境变量选择：

#### ChromaDB (默认)
```env
STORAGE_BACKEND=chroma
CHROMA_PERSIST_DIRECTORY=./data/chroma
CHROMA_COLLECTION_NAME=documents
```

#### MySQL
```env
STORAGE_BACKEND=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=tag_demo
```

#### MongoDB
```env
STORAGE_BACKEND=mongodb
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=tag_demo
MONGODB_COLLECTION=documents
```

#### Elasticsearch
```env
STORAGE_BACKEND=elasticsearch
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=documents
```

#### 本地文件
```env
STORAGE_BACKEND=local
```

### 向量化模型配置

```env
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

### DeepSeek API 配置

```env
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat
```

## 📊 使用示例

### 1. 上传文档

```python
import requests

# 上传文本文档
response = requests.post("http://localhost:8000/api/documents/upload-text", json={
    "title": "人工智能介绍",
    "content": "人工智能是计算机科学的一个分支..."
})

print(response.json())
```

### 2. 查询问答

```python
# 问答查询
response = requests.post("http://localhost:8000/api/query/ask", json={
    "query": "什么是人工智能？",
    "top_k": 5,
    "threshold": 0.7,
    "include_metadata": True
})

result = response.json()
print(f"答案: {result['answer']}")
print(f"置信度: {result['confidence']}")
```

### 3. 搜索文档

```python
# 搜索文档
response = requests.get("http://localhost:8000/api/query/search", params={
    "q": "机器学习",
    "top_k": 10,
    "threshold": 0.5
})

results = response.json()
for doc in results['results']:
    print(f"文档: {doc['document_title']}, 相似度: {doc['max_similarity']}")
```

## 🛠️ 开发指南

### 项目结构

```
tagDemo/
├── app/                    # 主应用目录
│   ├── __init__.py
│   ├── main.py            # FastAPI 主应用
│   ├── config.py          # 配置管理
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── document.py    # 文档模型
│   │   └── storage.py     # 存储接口
│   ├── services/          # 业务逻辑
│   │   ├── __init__.py
│   │   ├── storage_factory.py    # 存储工厂
│   │   ├── document_service.py   # 文档服务
│   │   ├── query_service.py      # 查询服务
│   │   ├── chroma_storage.py     # ChromaDB 存储
│   │   └── local_storage.py      # 本地存储
│   ├── api/               # API 路由
│   │   ├── __init__.py
│   │   ├── documents.py   # 文档管理 API
│   │   ├── query.py       # 查询 API
│   │   └── health.py      # 健康检查 API
│   └── utils/             # 工具函数
│       ├── __init__.py
│       ├── text_processor.py     # 文本处理
│       ├── embedding_service.py  # 向量化服务
│       └── llm_service.py        # LLM 服务
├── data/                  # 数据存储目录
├── docs/                  # 文档目录
├── requirements.txt       # 依赖包
├── env.example           # 环境变量示例
├── run.py                # 启动脚本
├── test_demo.py          # 测试脚本
└── README_CN.md          # 中文说明文档
```

### 添加新的存储后端

1. 在 `app/services/` 目录下创建新的存储类
2. 继承 `StorageBackend` 抽象基类
3. 实现所有抽象方法
4. 在 `StorageFactory` 中注册新的后端

### 自定义向量化模型

1. 修改 `EMBEDDING_MODEL` 环境变量
2. 或在代码中直接指定模型名称
3. 支持 Hugging Face 上的所有 sentence-transformers 模型

## 🔍 性能优化

### 向量检索优化

- 调整 `CHUNK_SIZE` 和 `CHUNK_OVERLAP` 参数
- 选择合适的向量化模型
- 使用更高效的索引结构

### 存储优化

- 选择合适的存储后端
- 实施数据分片
- 使用缓存机制

### 查询优化

- 调整相似度阈值
- 优化 Top-K 参数
- 使用查询缓存

## 🐛 故障排除

### 常见问题

1. **依赖安装失败**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **ChromaDB 初始化失败**
   - 检查数据目录权限
   - 确保有足够的磁盘空间

3. **向量化模型加载失败**
   - 检查网络连接
   - 尝试使用本地模型

4. **DeepSeek API 调用失败**
   - 检查 API 密钥配置
   - 验证网络连接

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

## 📈 监控指标

系统提供以下监控指标：

- 文档数量统计
- 查询响应时间
- 向量检索准确率
- 存储后端状态
- API 调用统计

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [ChromaDB](https://github.com/chroma-core/chroma) - 向量数据库
- [Sentence Transformers](https://github.com/UKPLab/sentence-transformers) - 文本向量化
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [DeepSeek](https://www.deepseek.com/) - 大语言模型

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 参与讨论

---

**Tag Demo** - 让文档检索更智能！ 🚀 