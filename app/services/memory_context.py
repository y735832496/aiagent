import pymysql
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import settings

class MemoryContext:
    def __init__(self):
        try:
            self.conn = pymysql.connect(
                host="localhost",
                port=3306,
                user="root",
                password="Zpmc@3261",
                database="memory_langchain",
                charset="utf8mb4",
                autocommit=True
            )
            print("✅ MySQL连接成功")
        except Exception as e:
            print(f"❌ MySQL连接失败: {e}")
            self.conn = None

    def create_session(self, user_id: str = "default", title: str = None) -> str:
        """创建新会话"""
        try:
            session_id = str(uuid.uuid4())
            title = title or f"会话_{session_id[:8]}"
            
            with self.conn.cursor() as cursor:
                sql = """
                INSERT INTO sessions (session_id, user_id, title, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    session_id, user_id, title, 
                    datetime.now(), datetime.now()
                ))
            
            print(f"✅ 会话创建成功: {session_id}")
            return session_id
            
        except Exception as e:
            print(f"❌ 创建会话失败: {e}")
            raise Exception(f"创建会话失败: {e}")

    def list_sessions(self, user_id: str = "default", limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户会话列表"""
        try:
            with self.conn.cursor() as cursor:
                sql = """
                SELECT session_id, user_id, title, created_at, updated_at,
                       (SELECT COUNT(*) FROM conversation_memories WHERE session_id = s.session_id) as memory_count
                FROM sessions s
                WHERE user_id = %s
                ORDER BY updated_at DESC
                LIMIT %s
                """
                cursor.execute(sql, (user_id, limit))
                rows = cursor.fetchall()
                
                sessions = []
                for row in rows:
                    sessions.append({
                        "session_id": row[0],
                        "user_id": row[1],
                        "title": row[2],
                        "created_at": row[3].isoformat() if row[3] else None,
                        "updated_at": row[4].isoformat() if row[4] else None,
                        "memory_count": row[5]
                    })
                
                return sessions
                
        except Exception as e:
            print(f"❌ 获取会话列表失败: {e}")
            return []

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话详情"""
        try:
            with self.conn.cursor() as cursor:
                sql = """
                SELECT session_id, user_id, title, created_at, updated_at,
                       (SELECT COUNT(*) FROM conversation_memories WHERE session_id = s.session_id) as memory_count
                FROM sessions s
                WHERE session_id = %s
                """
                cursor.execute(sql, (session_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "session_id": row[0],
                        "user_id": row[1],
                        "title": row[2],
                        "created_at": row[3].isoformat() if row[3] else None,
                        "updated_at": row[4].isoformat() if row[4] else None,
                        "memory_count": row[5]
                    }
                return None
                
        except Exception as e:
            print(f"❌ 获取会话详情失败: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            with self.conn.cursor() as cursor:
                # 先删除会话相关的记忆
                cursor.execute("DELETE FROM conversation_memories WHERE session_id = %s", (session_id,))
                # 再删除会话
                cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"❌ 删除会话失败: {e}")
            return False

    def add_memory(self, session_id: str, role: str, content: str, 
                   query_vector: List[float] = None, response_vector: List[float] = None, 
                   similarity_score: float = 0.0):
        """添加记忆"""
        try:
            with self.conn.cursor() as cursor:
                sql = """
                INSERT INTO conversation_memories
                (session_id, role, content, query_vector, response_vector, similarity_score, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    session_id, role, content,
                    json.dumps(query_vector) if query_vector else None,
                    json.dumps(response_vector) if response_vector else None,
                    similarity_score, datetime.now()
                ))
                
                # 更新会话的更新时间
                cursor.execute("UPDATE sessions SET updated_at = %s WHERE session_id = %s", 
                             (datetime.now(), session_id))
                
            print(f"✅ 记忆添加成功: {session_id} - {role}")
            
        except Exception as e:
            print(f"❌ 添加记忆失败: {e}")
            raise Exception(f"添加记忆失败: {e}")

    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取会话对话历史"""
        try:
            with self.conn.cursor() as cursor:
                sql = """
                SELECT role, content, created_at
                FROM conversation_memories
                WHERE session_id = %s
                ORDER BY created_at ASC
                LIMIT %s
                """
                cursor.execute(sql, (session_id, limit))
                rows = cursor.fetchall()
                
                history = []
                for row in rows:
                    history.append({
                        "role": row[0],
                        "content": row[1],
                        "created_at": row[2].isoformat() if row[2] else None
                    })
                
                return history
                
        except Exception as e:
            print(f"❌ 获取对话历史失败: {e}")
            return []

    def clear_session_memories(self, session_id: str) -> bool:
        """清空会话记忆"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM conversation_memories WHERE session_id = %s", (session_id,))
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"❌ 清空会话记忆失败: {e}")
            return False

    def get_relevant_memories(self, session_id: str, query: str, 
                            top_k: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """获取相关记忆（简单实现，基于关键词匹配）"""
        try:
            with self.conn.cursor() as cursor:
                # 简单的关键词匹配，实际项目中可以使用向量相似度搜索
                sql = """
                SELECT role, content, similarity_score, created_at
                FROM conversation_memories
                WHERE session_id = %s AND content LIKE %s
                ORDER BY similarity_score DESC, created_at DESC
                LIMIT %s
                """
                cursor.execute(sql, (session_id, f"%{query}%", top_k))
                rows = cursor.fetchall()
                
                memories = []
                for row in rows:
                    memories.append({
                        "role": row[0],
                        "content": row[1],
                        "similarity_score": row[2],
                        "created_at": row[3].isoformat() if row[3] else None
                    })
                
                return memories
                
        except Exception as e:
            print(f"❌ 获取相关记忆失败: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            with self.conn.cursor() as cursor:
                # 会话数量
                cursor.execute("SELECT COUNT(*) FROM sessions")
                session_count = cursor.fetchone()[0]
                
                # 记忆数量
                cursor.execute("SELECT COUNT(*) FROM conversation_memories")
                memory_count = cursor.fetchone()[0]
                
                # 用户数量
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM sessions")
                user_count = cursor.fetchone()[0]
                
                return {
                    "status": "connected" if self.conn else "disconnected",
                    "session_count": session_count,
                    "memory_count": memory_count,
                    "user_count": user_count,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def __del__(self):
        """析构函数，关闭数据库连接"""
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
                print("✅ MySQL连接已关闭")
            except:
                pass
