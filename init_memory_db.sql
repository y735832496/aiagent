-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS memory_langchain CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE memory_langchain;

-- 创建会话表
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建对话记忆表
CREATE TABLE IF NOT EXISTS conversation_memories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    query_vector JSON NULL,
    response_vector JSON NULL,
    similarity_score FLOAT DEFAULT 0.0,
    created_at DATETIME NOT NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_role (role),
    INDEX idx_created_at (created_at),
    INDEX idx_similarity (similarity_score),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入一些测试数据（可选）
INSERT INTO sessions (session_id, user_id, title, created_at, updated_at) VALUES
('test-session-001', 'default', '测试会话1', NOW(), NOW()),
('test-session-002', 'default', '测试会话2', NOW(), NOW())
ON DUPLICATE KEY UPDATE updated_at = NOW();

INSERT INTO conversation_memories (session_id, role, content, created_at) VALUES
('test-session-001', 'user', '你好', NOW()),
('test-session-001', 'assistant', '你好！有什么可以帮助你的吗？', NOW()),
('test-session-001', 'user', '今天天气怎么样？', NOW()),
('test-session-001', 'assistant', '抱歉，我无法获取实时天气信息。', NOW())
ON DUPLICATE KEY UPDATE created_at = NOW();

-- 显示表结构
DESCRIBE sessions;
DESCRIBE conversation_memories;

-- 显示测试数据
SELECT * FROM sessions;
SELECT * FROM conversation_memories;
