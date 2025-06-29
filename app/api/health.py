from fastapi import APIRouter
from app.services.document_service import DocumentService
from app.services.query_service import QueryService
from app.services.storage_factory import StorageFactory

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("/")
async def health_check():
    """系统健康检查"""
    try:
        # 检查各个服务
        document_service = DocumentService()
        query_service = QueryService()
        
        doc_health = await document_service.health_check()
        query_health = await query_service.health_check()
        
        # 获取存储后端信息
        storage_backends = StorageFactory.get_available_backends()
        
        overall_status = "healthy"
        if doc_health.get('status') != 'healthy' or query_health.get('status') != 'healthy':
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": "2024-01-01T00:00:00Z",  # 这里可以添加实际时间戳
            "services": {
                "document_service": doc_health,
                "query_service": query_health
            },
            "storage_backends": storage_backends,
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }

@router.get("/storage")
async def storage_health_check():
    """存储后端健康检查"""
    try:
        storage = StorageFactory.create_storage()
        health_status = await storage.health_check()
        
        return {
            "backend": type(storage).__name__,
            "status": "healthy" if health_status else "unhealthy",
            "details": {
                "backend_type": type(storage).__name__,
                "healthy": health_status
            }
        }
    except Exception as e:
        return {
            "backend": "unknown",
            "status": "error",
            "error": str(e)
        } 