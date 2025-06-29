#!/usr/bin/env python3
"""
调试模式启动脚本
"""

import os
import sys
import uvicorn
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    print("🐛 启动调试模式...")
    print("📁 项目根目录:", project_root)
    print("🔧 调试配置:")
    print("   - 端口: 8000")
    print("   - 主机: 127.0.0.1")
    print("   - 重载: 启用")
    print("   - 日志: 详细")
    
    # 启动调试服务器
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # 启用热重载
        log_level="debug",  # 详细日志
        access_log=True,
        use_colors=True
    ) 