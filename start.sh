#!/bin/bash

echo "🚀 启动 Tag Demo 项目..."

# 激活conda环境
echo "📦 激活conda环境..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate tagdemo310

# 设置环境变量
echo "🔧 设置环境变量..."
export KMP_DUPLICATE_LIB_OK=TRUE

# 检查Python版本
echo "🐍 检查Python版本..."
python --version

# 启动服务
echo "🚀 启动服务..."
python run.py 