# Tag Demo 项目

这是一个基于向量数据库的文档检索和问答系统，支持多种存储后端。

## 功能特性

### 1. 文档存储
- **向量数据库**: ChromaDB (核心存储)
- **结构化存储**: MySQL, MongoDB, Elasticsearch
- **本地存储**: JSON/CSV 文件

### 2. 文档处理流程
- **文档预处理**: 分块、清洗
- **向量化**: 使用 sentence-transformers 模型
- **存储与索引**: 向量和原始文本关联存储

### 3. 检索问答
- **向量检索**: 相似度搜索
- **上下文构建**: 原始文本拼接
- **问答生成**: 调用 DeepSeek 大模型

## 项目结构

```
tagDemo/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 主应用
│   ├── config.py            # 配置管理
│   ├── models/              # 数据模型
│   ├── services/            # 业务逻辑
│   ├── api/                 # API 路由
│   └── utils/               # 工具函数
├── data/                    # 数据存储目录
├── docs/                    # 文档目录
├── requirements.txt         # 依赖包
└── README.md               # 项目说明
```

## 安装和运行

1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 配置环境变量:
```bash
cp .env.example .env
# 编辑 .env 文件配置数据库连接等
```

3. 运行应用:
```bash
uvicorn app.main:app --reload
```

## API 接口

- `POST /api/documents/upload` - 上传文档
- `POST /api/documents/query` - 查询问答
- `GET /api/documents/list` - 获取文档列表
- `DELETE /api/documents/{doc_id}` - 删除文档

## 配置说明

支持多种存储后端配置:
- ChromaDB (向量数据库)
- MySQL (关系数据库)
- MongoDB (文档数据库)
- Elasticsearch (搜索引擎) 