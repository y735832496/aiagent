from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.config import settings
from app.api import documents_router, query_router, health_router

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于向量数据库的文档检索和问答系统",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(documents_router)
app.include_router(query_router)
app.include_router(health_router)

@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径，返回简单的HTML页面"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tag Demo - 文档检索系统</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .api-section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
            .endpoint {{ background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 3px; }}
            .method {{ font-weight: bold; color: #007bff; }}
            .url {{ font-family: monospace; color: #28a745; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏷️ Tag Demo</h1>
                <p>基于向量数据库的文档检索和问答系统</p>
            </div>
            
            <div class="api-section">
                <h2>📚 文档管理 API</h2>
                <div class="endpoint">
                    <span class="method">POST</span> <span class="url">/api/documents/upload</span>
                    <p>上传文档</p>
                </div>
                <div class="endpoint">
                    <span class="method">POST</span> <span class="url">/api/documents/upload-text</span>
                    <p>上传文本文档</p>
                </div>
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/api/documents/list</span>
                    <p>获取文档列表</p>
                </div>
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/api/documents/{{document_id}}</span>
                    <p>获取单个文档</p>
                </div>
                <div class="endpoint">
                    <span class="method">DELETE</span> <span class="url">/api/documents/{{document_id}}</span>
                    <p>删除文档</p>
                </div>
            </div>
            
            <div class="api-section">
                <h2>🔍 查询问答 API</h2>
                <div class="endpoint">
                    <span class="method">POST</span> <span class="url">/api/query/ask</span>
                    <p>问答接口</p>
                </div>
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/api/query/search</span>
                    <p>搜索文档</p>
                </div>
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/api/query/suggestions</span>
                    <p>获取查询建议</p>
                </div>
            </div>
            
            <div class="api-section">
                <h2>💚 健康检查 API</h2>
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/api/health</span>
                    <p>系统健康检查</p>
                </div>
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/api/health/storage</span>
                    <p>存储后端健康检查</p>
                </div>
            </div>
            
            <div class="api-section">
                <h2>📖 API 文档</h2>
                <p>
                    <a href="/docs" target="_blank">📋 Swagger UI 文档</a> | 
                    <a href="/redoc" target="_blank">📖 ReDoc 文档</a>
                </p>
            </div>
            
            <div class="api-section">
                <h2>⚙️ 配置信息</h2>
                <p><strong>向量后端:</strong> {settings.vector_backend}</p>
                <p><strong>文档后端:</strong> {settings.document_backend}</p>
                <p><strong>向量化模型:</strong> {settings.embedding_model}</p>
                <p><strong>版本:</strong> {settings.app_version}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/info")
async def get_info():
    """获取系统信息"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "vector_backend": settings.vector_backend,
        "document_backend": settings.document_backend,
        "embedding_model": settings.embedding_model,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 