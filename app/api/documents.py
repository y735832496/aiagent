from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import List, Optional
from app.models.document import DocumentUploadRequest, DocumentListResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["documents"])

document_service = DocumentService()

@router.post("/upload", response_model=dict)
async def upload_document(request: DocumentUploadRequest):
    """上传文档"""
    try:
        document = await document_service.upload_document(request)
        return {
            "document_id": document.id,
            "title": document.title,
            "message": "文档上传成功",
            "processing_time": 0.0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-text", response_model=dict)
async def upload_text_document(
    title: str = Form(...),
    content: str = Form(...),
    metadata: Optional[str] = Form(None)
):
    """上传文本文档"""
    try:
        import json
        metadata_dict = json.loads(metadata) if metadata else {}
        
        document = await document_service.upload_text_document(
            title=title,
            content=content,
            metadata=metadata_dict
        )
        
        return {
            "document_id": document.id,
            "title": document.title,
            "message": "文本文档上传成功",
            "processing_time": 0.0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """获取文档列表"""
    try:
        return await document_service.list_documents(page, page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}")
async def get_document(document_id: str):
    """获取单个文档"""
    try:
        document = await document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """删除文档"""
    try:
        success = await document_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在或删除失败")
        return {"message": "文档删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_document_stats():
    """获取文档统计信息"""
    try:
        return await document_service.get_document_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/status")
async def health_check():
    """健康检查"""
    try:
        return await document_service.health_check()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 