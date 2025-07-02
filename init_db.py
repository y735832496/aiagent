#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
import sys

def init_database():
    """初始化数据库和表结构"""
    
    # 数据库连接配置
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'Zpmc@3261',
        'charset': 'utf8mb4'
    }
    
    try:
        # 连接MySQL（不指定数据库）
        print("🔌 连接MySQL服务器...")
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        
        # 创建数据库
        print("📦 创建数据库 memory_langchain...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS memory_langchain CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✅ 数据库创建成功")
        
        # 切换到目标数据库
        cursor.execute("USE memory_langchain")
        
        # 创建会话表
        print("📋 创建会话表...")
        create_sessions_table = """
        CREATE TABLE IF NOT EXISTS sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL UNIQUE,
            user_id VARCHAR(255) NOT NULL,
            title VARCHAR(500) NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            INDEX idx_user_id (user_id),
            INDEX idx_session_id (session_id),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        cursor.execute(create_sessions_table)
        print("✅ 会话表创建成功")
        
        # 创建对话记忆表
        print("📝 创建对话记忆表...")
        create_memories_table = """
        CREATE TABLE IF NOT EXISTS conversation_memories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL,
            role ENUM('user', 'assistant', 'system') NOT NULL,
            content TEXT NOT NULL,
            query_vector JSON NULL,
            response_vector JSON NULL,
            similarity_score FLOAT DEFAULT 0.0,
            created_at DATETIME NOT NULL,
            INDEX idx_session_id (session_id),
            INDEX idx_role (role),
            INDEX idx_created_at (created_at),
            INDEX idx_similarity (similarity_score),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        cursor.execute(create_memories_table)
        print("✅ 对话记忆表创建成功")
        
        # 插入测试数据
        print("🧪 插入测试数据...")
        
        # 测试会话
        test_sessions = [
            ('test-session-001', 'default', '测试会话1'),
            ('test-session-002', 'default', '测试会话2')
        ]
        
        for session_id, user_id, title in test_sessions:
            cursor.execute("""
                INSERT INTO sessions (session_id, user_id, title, created_at, updated_at) 
                VALUES (%s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE updated_at = NOW()
            """, (session_id, user_id, title))
        
        # 测试记忆
        test_memories = [
            ('test-session-001', 'user', '你好'),
            ('test-session-001', 'assistant', '你好！有什么可以帮助你的吗？'),
            ('test-session-001', 'user', '今天天气怎么样？'),
            ('test-session-001', 'assistant', '抱歉，我无法获取实时天气信息。')
        ]
        
        for session_id, role, content in test_memories:
            cursor.execute("""
                INSERT INTO conversation_memories (session_id, role, content, created_at) 
                VALUES (%s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE created_at = NOW()
            """, (session_id, role, content))
        
        print("✅ 测试数据插入成功")
        
        # 提交事务
        conn.commit()
        
        # 验证表结构
        print("\n📊 验证表结构...")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✅ 数据库中的表: {[table[0] for table in tables]}")
        
        # 显示表结构
        print("\n📋 sessions表结构:")
        cursor.execute("DESCRIBE sessions")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} {row[2]} {row[3]} {row[4]} {row[5]}")
        
        print("\n📋 conversation_memories表结构:")
        cursor.execute("DESCRIBE conversation_memories")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} {row[2]} {row[3]} {row[4]} {row[5]}")
        
        # 显示测试数据
        print("\n📄 测试数据:")
        cursor.execute("SELECT session_id, user_id, title FROM sessions")
        sessions = cursor.fetchall()
        print("sessions表:")
        for session in sessions:
            print(f"  {session[0]}: {session[1]} - {session[2]}")
        
        cursor.execute("SELECT session_id, role, content FROM conversation_memories LIMIT 5")
        memories = cursor.fetchall()
        print("conversation_memories表:")
        for memory in memories:
            print(f"  {memory[0]} [{memory[1]}]: {memory[2][:50]}...")
        
        print("\n🎉 数据库初始化完成！")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)
    
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔌 数据库连接已关闭")

if __name__ == "__main__":
    init_database()
