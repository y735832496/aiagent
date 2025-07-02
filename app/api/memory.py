from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.services.memory_context import MemoryContext
from app.models.document import QueryRequest

router = APIRouter(prefix="/api/memory", tags=["memory"])

memory_context = MemoryContext()

@router.post("/sessions")
async def create_session(user_id: str = "default", title: str = None):
    """创建新会话"""
    try:
        session_id = memory_context.create_session(user_id=user_id, title=title)
        return {
            "session_id": session_id,
            "user_id": user_id,
            "title": title or f"会话_{session_id[:8]}",
            "message": "会话创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")

@router.get("/sessions")
async def list_sessions(
    user_id: str = Query("default", description="用户ID"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """获取用户会话列表"""
    try:
        sessions = memory_context.list_sessions(user_id=user_id, limit=limit)
        return {
            "user_id": user_id,
            "sessions": sessions,
            "total_count": len(sessions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """获取会话详情"""
    try:
        session = memory_context.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话详情失败: {str_e}")

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        success = memory_context.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        return {
            "session_id": session_id,
            "message": "会话删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")

@router.get("/sessions/{session_id}/history")
async def get_conversation_history(
    session_id: str,
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """获取会话对话历史"""
    try:
        history = memory_context.get_conversation_history(session_id, limit=limit)
        return {
            "session_id": session_id,
            "message": history,
            "total_count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话历史失败: {str(e)}")

@router.delete("/sessions/{session_id}/memories")
async def clear_session_memories(session_id: str):
    """清空会话记忆"""
    try:
        success = memory_context.clear_session_memories(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        return {
            "session_id": session_id,
            "message": "会话记忆清空成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空会话记忆失败: {str(e)}")

@router.get("/sessions/{session_id}/memories/relevant")
async def get_relevant_memories(
    session_id: str,
    query: str = Query(..., description="查询内容"),
    top_k: int = Query(5, ge=1, le=20, description="返回数量"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="相似度阈值")
):
    """获取相关记忆"""
    try:
        memories = memory_context.get_relevant_memories(
            session_id=session_id,
            query=query,
            top_k=top_k,
            threshold=threshold
        )
        return {
            "session_id": session_id,
            "query": query,
            "memories": memories,
            "total_count": len(memories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取相关记忆失败: {str(e)}")

@router.get("/stats")
async def get_memory_stats():
    """获取记忆统计信息"""
    try:
        stats = memory_context.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.post("/test")
async def test_memory():
    """测试记忆功能"""
    try:
        # 创建测试会话
        session_id = memory_context.create_session(user_id="test", title="测试会话")
        
        # 添加测试记忆
        memory_context.add_memory(session_id, "user", "你好")
        memory_context.add_memory(session_id, "assistant", "你好！有什么可以帮助你的吗？")
        memory_context.add_memory(session_id, "user", "今天天气怎么样？")
        memory_context.add_memory(session_id, "assistant", "抱歉，我无法获取实时天气信息。")
        
        # 获取历史
        history = memory_context.get_conversation_history(session_id)
        
        # 获取相关记忆
        relevant = memory_context.get_relevant_memories(session_id, "天气", top_k=2)
        
        return {
            "session_id": session_id,
            "test_history": history,
            "relevant_memories": relevant,
            "message": "记忆功能测试成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试记忆功能失败: {str(e)}")
