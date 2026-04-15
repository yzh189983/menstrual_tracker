#!/bin/bash
# 日历记录小助手健康检查脚本

APP_DIR="/root/.openclaw/workspace/calendar_app"
LOG_FILE="$APP_DIR/app.log"

# 检查进程是否在运行
if ! pgrep -f "python3 app.py" > /dev/null 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] 进程已挂掉，正在重启..." >> $LOG_FILE
    cd $APP_DIR
    nohup python3 app.py > $LOG_FILE 2>&1 &
    sleep 2
    if pgrep -f "python3 app.py" > /dev/null 2>&1; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [OK] 服务已重新启动" >> $LOG_FILE
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] 重启失败" >> $LOG_FILE
    fi
else
    # 尝试访问服务
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200"; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [OK] 服务健康" >> $LOG_FILE
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] 进程在运行但HTTP无响应，重启..." >> $LOG_FILE
        pkill -f "python3 app.py"
        cd $APP_DIR
        nohup python3 app.py > $LOG_FILE 2>&1 &
    fi
fi