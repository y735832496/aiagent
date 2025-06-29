from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from app.models.document import QueryRequest, QueryResponse
from app.services.query_service import QueryService

router = APIRouter(prefix="/api/query", tags=["query"])

query_service = QueryService()

@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """问答接口"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        
        response = await query_service.query(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_documents(
    q: str = Query(..., description="搜索查询"),
    top_k: int = Query(10, ge=1, le=50, description="返回结果数量"),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="相似度阈值")
):
    """搜索文档"""
    try:
        if not q.strip():
            raise HTTPException(status_code=400, detail="搜索查询不能为空")
        
        results = await query_service.search_documents(
            query=q,
            top_k=top_k,
            threshold=threshold
        )
        
        return {
            "query": q,
            "results": results,
            "total_count": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions")
async def get_suggestions(
    q: str = Query(..., description="查询内容"),
    max_suggestions: int = Query(5, ge=1, le=10, description="最大建议数量")
):
    """获取查询建议"""
    try:
        suggestions = await query_service.get_suggestions(q, max_suggestions)
        return {
            "query": q,
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def query_health_check():
    """查询服务健康检查"""
    try:
        health_info = await query_service.health_check()
        return health_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 