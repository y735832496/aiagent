#!/usr/bin/env python3
"""
MySQL记忆数据库初始化脚本
"""

import pymysql
from pymysql.cursors import DictCursor

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Zpmc@3261',
    'charset': 'utf8mb4'
}

def create_database():
    """创建数据库"""
    try:
        # 连接MySQL（不指定数据库）
        connection = pymysql.connect(**DB_CONFIG, cursorclass=DictCursor)
        
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS memory_langchain CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ 数据库创建成功")
            
            # 使用数据库
            cursor.execute("USE memory_langchain")
            
            # 创建会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id VARCHAR(64) PRIMARY KEY COMMENT '会话ID',
                    user_id VARCHAR(64) DEFAULT 'default' COMMENT '用户ID',
                    title VARCHAR(255) COMMENT '会话标题',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    is_active BOOLEAN DEFAULT TRUE COMMENT '是否活跃',
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at)
                ) COMMENT '会话表'
            """)
            print("✅ 会话表创建成功")
            
            # 创建对话记忆表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_memories (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记忆ID',
                    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
                    role ENUM('user', 'assistant', 'system') NOT NULL COMMENT '角色',
                    content TEXT NOT NULL COMMENT '内容',
                    query_vector JSON COMMENT '查询向量（JSON格式）',
                    response_vector JSON COMMENT '响应向量（JSON格式）',
                    similarity_score FLOAT DEFAULT 0.0 COMMENT '相似度分数',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                    INDEX idx_session_id (session_id),
                    INDEX idx_role (role),
                    INDEX idx_created_at (created_at),
                    INDEX idx_similarity_score (similarity_score)
                ) COMMENT '对话记忆表'
            """)
            print("✅ 对话记忆表创建成功")
            
            # 插入默认会话
            cursor.execute("""
                INSERT IGNORE INTO sessions (id, user_id, title) 
                VALUES ('default', 'default', '默认会话')
            """)
            print("✅ 默认会话创建成功")
            
            connection.commit()
            print("🎉 数据库初始化完成！")
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise
    finally:
        if connection:
            connection.close()

def test_connection():
    """测试数据库连接"""
    try:
        connection = pymysql.connect(
            **DB_CONFIG,
            database='memory_langchain',
            cursorclass=DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM sessions")
            result = cursor.fetchone()
            print(f"✅ 数据库连接测试成功，会话数量: {result['count']}")
            
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        raise
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    print("🚀 开始初始化MySQL记忆数据库...")
    create_database()
    test_connection()
    print("✨ 初始化完成！")
