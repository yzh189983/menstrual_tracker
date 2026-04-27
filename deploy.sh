#!/bin/bash
# 日历记录小助手部署脚本

cd /root/.openclaw/workspace/calendar_app

# 拉取最新代码
git pull origin main

# 安装依赖（使用 python3，添加 --break-system-packages 解决 PEP 668 问题）
pip3 install -r requirements.txt -q --break-system-packages

# 杀掉旧的 python 进程
pkill -f "python3 app.py" 2>/dev/null

# 启动服务
nohup python3 app.py > app.log 2>&1 &

# 等待几秒
sleep 3

# 检查是否启动成功
if ps aux | grep -q "[p]ython3 app.py"; then
    echo "✅ 服务启动成功！"
    curl -s http://localhost:5000 | head -5
else
    echo "❌ 服务启动失败，查看日志："
    tail -50 app.log
fi
