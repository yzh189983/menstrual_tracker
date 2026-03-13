# 🌸 日历记录小助手

一个美观实用的经期记录 Web 应用，帮助女性用户追踪和管理生理周期。同时支持学习记录、工作记录和即时聊天功能。集成AI智能助手，支持经期预测、学习计划生成、错题辅导等功能。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-2.0+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ 核心功能

### 🌸 月经记录
- 直观的 FullCalendar 日历展示
- 通过颜色区分经量（少量/中等/大量）
- 点击日期即可查看或删除记录
- 支持月视图和列表视图切换
- 开始日期选择后，结束日期自动同步年月

### 🤖 AI 经期助手 (DeepSeek)
- 🔮 AI 预测经期 - 基于历史数据预测下次经期日期
- 📊 AI 健康报告 - 生成详细经期健康分析报告
- 💬 AI 小经聊天 - 随时问答经期健康问题

### 📚 学习记录
- 记录学习科目和时长
- 查看学习趋势统计

### 🤖 AI 学习助手 (DeepSeek)
- 📝 AI 学习计划 - 输入科目和目标，生成7-90天学习计划
- 📈 AI 效率分析 - 分析学习数据，提供效率评分和建议
- ❌ AI 错题辅导 - 输入错题，AI分析讲解并提供练习题
- 📚 错题集 - 保存整理错题，支持编辑、删除、学科分类

### 💼 工作记录
- 记录工作任务和时长
- 记录上班/下班时间
- 统计加班时长

### 💬 即时聊天
- 好友添加与管理
- 好友请求处理（接受/拒绝）
- 实时一对一聊天
- 聊天记录存储

### 📊 数据统计
- 本月记录次数统计
- 平均经期天数计算
- 最近一次经期日期
- 经期趋势图表可视化
- 间隔天数分析（平均/最长/最短）

### 📅 总日历
- 整合所有类型的记录
- 点击记录查看详细信息（弹窗展示）
- 按颜色区分不同类型记录

### 💬 用户反馈
- 提交改进建议、错误反馈等
- 查看反馈历史和回复状态

### 👑 管理员后台
- 查看所有用户列表
- 管理用户（修改密码、删除用户）
- 查看和回复用户反馈
- 查看所有记录详情

### 🔐 用户系统
- 用户注册和登录
- 个人资料管理（含头像上传）
- 数据隔离（每个用户只能看到自己的记录）
- 管理员账号登录

## 🛠️ 技术栈

- **后端**: Python + Flask
- **数据库**: SQLite（轻量级，无需配置）
- **前端**: HTML + CSS + JavaScript
- **日历**: FullCalendar
- **图表**: Chart.js
- **AI**: DeepSeek API

## 🚀 部署指南

### 环境要求

- Python 3.8 或更高版本
- pip 包管理器
- 或者使用 Anaconda

### 本地运行

1. **克隆项目**
   ```bash
   git clone https://github.com/yzh189983/menstrual_tracker.git
   cd menstrual_tracker
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行应用**
   ```bash
   python app.py
   ```

4. **访问应用**
   打开浏览器访问 http://127.0.0.1:5000

### 使用 Anaconda

```bash
conda create -n flask_app python=3.10
conda activate flask_app
pip install -r requirements.txt
python app.py
```

### 生产环境部署

#### 使用 Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### 使用 Docker

1. 创建 Dockerfile：
   ```dockerfile
   FROM python:3.10-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   EXPOSE 5000
   
   CMD ["gunicorn", "-w 4", "-b 0.0.0.0:5000", "app:app"]
   ```

2. 构建和运行：
   ```bash
   docker build -t menstrual-tracker .
   docker run -d -p 5000:5000 --name menstrual-tracker menstrual-tracker
   ```

## 📁 项目结构

```
menstrual_tracker/
├── app.py                 # 主应用文件
├── README.md              # 项目说明文档
├── requirements.txt       # Python 依赖
├── periods.json           # 经期数据文件
├── templates/            # HTML 模板
│   ├── index.html        # 月经记录页面
│   ├── calendar.html     # 月经日历页面
│   ├── all_calendar.html # 总日历页面
│   ├── study.html         # 学习记录
│   ├── wrong_questions.html # 错题集
│   ├── work.html          # 工作记录
│   ├── chat.html         # 聊天主页
│   ├── chat_room.html    # 聊天房间
│   ├── profile.html      # 个人资料
│   ├── login.html        # 登录
│   ├── register.html     # 注册
│   ├── forgot.html       # 忘记密码
│   ├── feedback.html     # 用户反馈
│   ├── admin_login.html  # 管理员登录
│   └── admin.html        # 管理后台
├── static/               # 静态文件
│   ├── css/             # 样式文件
│   ├── js/              # JavaScript 文件
│   └── images/          # 图片资源
└── instance/            # 数据库文件
```

## 🔧 管理员说明

### 管理员账号
- 用户名：`admin`
- 密码：`yzh18998301631`（建议首次登录后修改）

### 访问管理员后台
1. 登录页面底部点击「管理员登录」
2. 或直接访问 `/admin/login`

### 管理员功能
- 查看所有用户及记录统计
- 修改用户密码
- 删除用户（需二次确认）
- 回复用户反馈
- 查看所有记录详情

## 📝 使用说明

### 月经记录
1. 首次访问需要注册账号
2. 登录后进入月经记录页面
3. 点击侧边栏"添加记录"，选择开始和结束日期
4. 选择经量，添加备注（可选）
5. 点击保存，记录会自动显示在日历上
6. 可以通过点击日历上的事件查看详情或删除记录

### AI 经期助手
1. 在月经记录页面侧边栏点击 AI 按钮
2. 可以使用预测、健康报告、聊天功能
3. AI 会根据你的历史数据分析并给出建议

### AI 学习助手
1. 进入学习记录页面
2. 点击"AI 学习计划"生成学习计划
3. 点击"AI 效率分析"查看学习数据分析
4. 点击"AI 错题辅导"输入错题获取讲解
5. 错题可保存到错题集，支持编辑整理

### 错题集
1. 从学习记录页面导航进入错题集
2. 可以按学科筛选错题
3. 支持批量删除和单个编辑
4. 查看每道错题的完整解答和知识点

### 聊天功能
1. 进入聊天页面
2. 点击"添加好友"输入好友用户名发送请求
3. 好友接受请求后即可开始聊天
4. 在聊天房间中发送和接收消息

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

Made with 🌸 by 杨梓泓
