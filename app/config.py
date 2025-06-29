"""
配置管理
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

# 加载环境变量
load_dotenv()

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    app_name: str = "Tag Demo"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 向量数据库配置
    vector_backend: str = "faiss"  # 支持: local, chromadb, faiss
    vector_dimension: int = 768
    
    # 文档存储配置
    document_backend: str = "faiss"  # 支持: local, mysql, mongodb, elasticsearch, faiss
    
    # 向量化配置
    embedding_model: str = "shibing624/text2vec-base-chinese"  # 中文模型，适合中文检索
    embedding_device: str = "cpu"  # cpu, cuda
    
    # LLM 配置
    llm_provider: str = "mock"  # 支持: mock, openai, anthropic, local
    llm_model: str = "gpt-3.5-turbo"
    llm_api_key: Optional[str] = None
    llm_api_base: Optional[str] = None
    
    # 文档处理配置
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_tokens: int = 4000
    
    # 搜索配置
    similarity_threshold: float = 0.3  # 降低相似度阈值，提高召回率
    top_k: int = 10  # 返回前10个最相关结果
    max_results: int = 20  # 最大返回结果数
    
    # 数据目录
    data_dir: str = "data"
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # DeepSeek API key
    deepseek_api_key: Optional[str] = "sk-498e5c6d3af8478ca19cfa4f2a4047ed"
    
    # DeepSeek API URL
    deepseek_api_url: Optional[str] = "https://api.deepseek.com/v1/chat/completions"
    
    # DeepSeek model
    deepseek_model: Optional[str] = "deepseek-chat"
    
    # ChromaDB 配置
    chroma_persist_directory: str = "./data/chroma"
    chroma_collection_name: str = "documents"
    
    # 数据库配置（从环境变量读取）
    storage_backend: Optional[str] = None
    mysql_host: Optional[str] = None
    mysql_port: Optional[str] = None
    mysql_user: Optional[str] = None
    mysql_password: Optional[str] = None
    mysql_database: Optional[str] = None
    mongodb_uri: Optional[str] = None
    mongodb_database: Optional[str] = None
    mongodb_collection: Optional[str] = None
    elasticsearch_host: Optional[str] = None
    elasticsearch_port: Optional[str] = None
    elasticsearch_index: Optional[str] = None
    upload_dir: Optional[str] = None
    max_file_size: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 允许额外字段
    
    @property
    def vector_backend_config(self) -> dict:
        """获取向量数据库配置"""
        configs = {
            "local": {
                "type": "local",
                "data_dir": f"{self.data_dir}/local"
            },
            "chromadb": {
                "type": "chromadb", 
                "data_dir": f"{self.data_dir}/chroma"
            },
            "faiss": {
                "type": "faiss",
                "data_dir": f"{self.data_dir}/faiss"
            }
        }
        return configs.get(self.vector_backend, configs["faiss"])
    
    @property
    def document_backend_config(self) -> dict:
        """获取文档存储配置"""
        configs = {
            "local": {
                "type": "local",
                "data_dir": f"{self.data_dir}/documents"
            },
            "mysql": {
                "type": "mysql",
                "host": self.mysql_host or os.getenv("MYSQL_HOST", "localhost"),
                "port": int(self.mysql_port or os.getenv("MYSQL_PORT", "3306")),
                "database": self.mysql_database or os.getenv("MYSQL_DATABASE", "tagdemo"),
                "username": self.mysql_user or os.getenv("MYSQL_USERNAME", "root"),
                "password": self.mysql_password or os.getenv("MYSQL_PASSWORD", "")
            },
            "mongodb": {
                "type": "mongodb",
                "uri": self.mongodb_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
                "database": self.mongodb_database or os.getenv("MONGODB_DATABASE", "tagdemo")
            },
            "elasticsearch": {
                "type": "elasticsearch",
                "hosts": (self.elasticsearch_host or os.getenv("ELASTICSEARCH_HOSTS", "localhost:9200")).split(","),
                "index": self.elasticsearch_index or os.getenv("ELASTICSEARCH_INDEX", "tagdemo")
            }
        }
        return configs.get(self.document_backend, configs["local"])


# 全局配置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.vector_backend_config["data_dir"], exist_ok=True)
os.makedirs(settings.document_backend_config["data_dir"], exist_ok=True)
os.makedirs("./data", exist_ok=True) 