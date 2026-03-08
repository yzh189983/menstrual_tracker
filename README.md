# 🌸 月经记录小助手

一个美观实用的经期记录 Web 应用，帮助女性用户追踪和管理生理周期。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-2.0+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ 核心功能

### 📅 日历视图
- 直观的 FullCalendar 日历展示
- 通过颜色区分经量（少量/中等/大量）
- 点击日期即可查看或删除记录
- 支持月视图和列表视图切换

### 📝 记录管理
- 添加经期开始和结束日期
- 记录经量（少量/中等/大量）
- 添加备注信息
- 查看和删除历史记录

### 📊 数据统计
- 本月记录次数统计
- 平均经期天数计算
- 最近一次经期日期
- 经期趋势图表可视化
- 间隔天数分析（平均/最长/最短）

### 🔐 用户系统
- 用户注册和登录
- 个人资料管理
- 数据隔离（每个用户只能看到自己的记录）

### 📚 多功能支持
- 经期记录（主要功能）
- 学习记录
- 工作记录
- 总日历视图（整合所有记录）

## 🛠️ 技术栈

- **后端**: Python + Flask
- **数据库**: SQLite（轻量级，无需配置）
- **前端**: HTML + CSS + JavaScript
- **日历**: FullCalendar
- **图表**: Chart.js

## 🚀 部署指南

### 环境要求

- Python 3.8 或更高版本
- pip 包管理器

### 本地运行

1. **克隆项目**
   ```bash
   git clone <项目地址>
   cd menstrual_tracker
   ```

2. **创建虚拟环境（推荐）**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **运行应用**
   ```bash
   python app.py
   ```

5. **访问应用**
   打开浏览器访问 http://127.0.0.1:5000

### 生产环境部署

#### 使用 Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### 使用 Docker

1. 创建 Dockerfile：
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   EXPOSE 5000
   
   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
   ```

2. 构建和运行：
   ```bash
   docker build -t menstrual-tracker .
   docker run -d -p 5000:5000 --name menstrual-tracker menstrual-tracker
   ```

#### 使用 Nginx + Gunicorn

1. 安装 Nginx
2. 配置 Nginx 反向代理：
   ```nginx
   server {
       listen 80;
       server_name your_domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### 云平台部署

#### Railway
```bash
railway init
railway up
```

#### Render
- 连接到 GitHub 仓库
- 选择 Flask 模板
- 配置启动命令：`gunicorn app:app`

#### Fly.io
```bash
fly launch
fly deploy
```

## 📁 项目结构

```
menstrual_tracker/
├── app.py                 # 主应用文件
├── requirements.txt       # Python 依赖
├── templates/            # HTML 模板
│   ├── index.html       # 月经记录页面
│   ├── calendar.html    # 日历页面
│   ├── all_calendar.html
│   ├── study.html       # 学习记录
│   ├── work.html        # 工作记录
│   ├── profile.html     # 个人资料
│   ├── login.html       # 登录
│   ├── register.html   # 注册
│   └── forgot.html     # 忘记密码
└── static/              # 静态文件（如有）
```

## 🔧 配置说明

### 修改密钥

在 `app.py` 中修改 SECRET_KEY：
```python
app.secret_key = 'your-secret-key-here'
```

### 数据库

默认使用 SQLite，数据保存在 `menstrual.db` 文件中。

### 端口

默认运行在 5000 端口，可通过环境变量修改：
```bash
export PORT=8080
```

## 📝 使用说明

1. 首次访问需要注册账号
2. 登录后进入月经记录页面
3. 点击侧边栏"添加记录"，选择开始和结束日期
4. 选择经量，添加备注（可选）
5. 点击保存，记录会自动显示在日历上
6. 可以通过点击日历上的事件删除记录

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

Made with 🌸 by 杨梓泓
