from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import random
import string
import time
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'menstrual-tracker-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///menstrual.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 邮件配置
app.config['MAIL_SERVER'] = 'smtp.163.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'yzh189983@163.com'
app.config['MAIL_PASSWORD'] = 'yzh18998301631'
app.config['MAIL_DEFAULT_SENDER'] = 'yzh189983@163.com'

# 文件上传配置
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['AVATAR_FOLDER'] = 'static/avatars'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# DeepSeek API 配置
DEEPSEEK_API_KEY = "sk-438f7ee6c06f4f75b0eca2a7bb6106fa"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AVATAR_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 验证码存储 (临时存储)
verification_codes = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 用户模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True)
    nickname = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    birthday = db.Column(db.Date)
    avatar = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)  # 管理员标识
    created_at = db.Column(db.DateTime, default=datetime.now)
    periods = db.relationship('Period', backref='user', lazy=True)

# 月经记录模型
class Period(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    flow = db.Column(db.String(20), default='medium')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

# 学习记录模型
class StudyRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='study_records')
    date = db.Column(db.Date, nullable=False)
    subject = db.Column(db.String(100), nullable=False)  # 学习科目
    duration = db.Column(db.Integer, nullable=False)      # 学习时长（分钟）
    plan = db.Column(db.Text)                             # 学习计划/内容
    notes = db.Column(db.Text)                             # 备注
    created_at = db.Column(db.DateTime, default=datetime.now)

# 工作记录模型
class WorkRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='work_records')
    date = db.Column(db.Date, nullable=False)
    task = db.Column(db.String(200))                      # 工作任务
    task_duration = db.Column(db.Integer, default=0)      # 任务时长（分钟）
    work_start = db.Column(db.Time)                       # 上班时间
    work_end = db.Column(db.Time)                         # 下班时间
    overtime = db.Column(db.Integer, default=0)           # 加班时长（分钟）
    notes = db.Column(db.Text)                            # 备注
    created_at = db.Column(db.DateTime, default=datetime.now)

# 用户反馈模型
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='feedbacks')
    feedback_type = db.Column(db.String(20), nullable=False)  # suggest/bug/praise/other
    contact = db.Column(db.String(100))                        # 联系方式
    content = db.Column(db.Text, nullable=False)               # 反馈内容
    reply = db.Column(db.Text)                                 # 回复内容
    status = db.Column(db.String(20), default='pending')       # pending/replied
    created_at = db.Column(db.DateTime, default=datetime.now)

# 好友关系模型
class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/accepted
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='friends')
    friend = db.relationship('User', foreign_keys=[friend_id], backref='friend_of')

# 聊天消息模型
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text/record
    record_id = db.Column(db.Integer)  # 分享的记录ID
    record_type = db.Column(db.String(20))  # period/study/work
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

# 错题集模型
class WrongQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(50))  # 学科
    question = db.Column(db.Text, nullable=False)  # 错题题目
    user_answer = db.Column(db.Text)  # 用户的答案
    ai_explanation = db.Column(db.Text)  # AI的讲解
    knowledge_points = db.Column(db.Text)  # 知识点
    practice_question = db.Column(db.Text)  # 练习题
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='wrong_questions')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 首页 - 显示日历
@app.route('/')
@login_required
def index():
    periods = Period.query.filter_by(user_id=current_user.id).order_by(Period.start_date.desc()).all()
    return render_template('calendar.html', periods=periods, user=current_user, timedelta=timedelta)

# 学习记录页面
@app.route('/study')
@login_required
def study():
    records = StudyRecord.query.filter_by(user_id=current_user.id).order_by(StudyRecord.date.desc()).all()
    return render_template('study.html', records=records, user=current_user, timedelta=timedelta)

# 添加学习记录
@app.route('/study/add', methods=['POST'])
@login_required
def add_study():
    date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
    subject = request.form.get('subject')
    duration = int(request.form.get('duration'))
    plan = request.form.get('plan', '')
    notes = request.form.get('notes', '')
    
    record = StudyRecord(
        user_id=current_user.id,
        date=date,
        subject=subject,
        duration=duration,
        plan=plan,
        notes=notes
    )
    db.session.add(record)
    db.session.commit()
    
    flash('学习记录添加成功！', 'success')
    return redirect(url_for('study'))

# 删除学习记录
@app.route('/study/delete/<int:record_id>')
@login_required
def delete_study(record_id):
    record = StudyRecord.query.get_or_404(record_id)
    if record.user_id == current_user.id:
        db.session.delete(record)
        db.session.commit()
        flash('学习记录已删除', 'success')
    return redirect(url_for('study'))

# API: 获取学习记录数据
@app.route('/api/study_data')
@login_required
def api_study_data():
    records = StudyRecord.query.filter_by(user_id=current_user.id).all()
    data = []
    for r in records:
        data.append({
            'id': r.id,
            'date': r.date.strftime('%Y-%m-%d'),
            'subject': r.subject,
            'duration': r.duration,
            'plan': r.plan,
            'notes': r.notes
        })
    return jsonify(data)

# 错题集页面
@app.route('/wrong_questions')
@login_required
def wrong_questions():
    subject_filter = request.args.get('subject', '')
    query = WrongQuestion.query.filter_by(user_id=current_user.id)
    if subject_filter:
        query = query.filter_by(subject=subject_filter)
    questions = query.order_by(WrongQuestion.created_at.desc()).all()
    
    # 获取所有学科用于筛选
    all_subjects = db.session.query(WrongQuestion.subject).filter_by(user_id=current_user.id).distinct().all()
    subjects = [s[0] for s in all_subjects if s[0]]
    
    return render_template('wrong_questions.html', 
                           questions=questions, 
                           user=current_user,
                           subject_filter=subject_filter,
                           subjects=subjects)

# 删除错题
@app.route('/wrong_questions/delete/<int:qid>', methods=['POST'])
@login_required
def delete_wrong_question(qid):
    question = WrongQuestion.query.get_or_404(qid)
    if question.user_id == current_user.id:
        db.session.delete(question)
        db.session.commit()
        flash('错题已删除', 'success')
    return redirect(url_for('wrong_questions'))

# 批量删除错题
@app.route('/wrong_questions/batch_delete', methods=['POST'])
@login_required
def batch_delete_wrong_questions():
    ids = request.form.get('ids', '').split(',')
    deleted_count = 0
    for id_str in ids:
        if id_str.strip():
            try:
                qid = int(id_str.strip())
                question = WrongQuestion.query.filter_by(id=qid, user_id=current_user.id).first()
                if question:
                    db.session.delete(question)
                    deleted_count += 1
            except:
                pass
    db.session.commit()
    flash(f'已删除 {deleted_count} 道错题', 'success')
    return redirect(url_for('wrong_questions'))

# 编辑错题
@app.route('/wrong_questions/edit/<int:qid>', methods=['POST'])
@login_required
def edit_wrong_question(qid):
    question = WrongQuestion.query.get_or_404(qid)
    if question.user_id != current_user.id:
        return jsonify({'success': False, 'message': '无权修改'})
    
    question.subject = request.form.get('subject', question.subject)
    question.question = request.form.get('question', question.question)
    question.user_answer = request.form.get('user_answer', question.user_answer)
    question.ai_explanation = request.form.get('ai_explanation', question.ai_explanation)
    question.knowledge_points = request.form.get('knowledge_points', question.knowledge_points)
    question.practice_question = request.form.get('practice_question', question.practice_question)
    
    db.session.commit()
    return jsonify({'success': True, 'message': '更新成功'})

# 工作记录页面
@app.route('/work')
@login_required
def work():
    records = WorkRecord.query.filter_by(user_id=current_user.id).order_by(WorkRecord.date.desc()).all()
    return render_template('work.html', records=records, user=current_user, timedelta=timedelta)

# 添加工作记录
@app.route('/work/add', methods=['POST'])
@login_required
def add_work():
    date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
    task = request.form.get('task', '')
    task_duration = int(request.form.get('task_duration', 0))
    work_start = datetime.strptime(request.form.get('work_start'), '%H:%M').time() if request.form.get('work_start') else None
    work_end = datetime.strptime(request.form.get('work_end'), '%H:%M').time() if request.form.get('work_end') else None
    overtime = int(request.form.get('overtime', 0))
    notes = request.form.get('notes', '')
    
    record = WorkRecord(
        user_id=current_user.id,
        date=date,
        task=task,
        task_duration=task_duration,
        work_start=work_start,
        work_end=work_end,
        overtime=overtime,
        notes=notes
    )
    db.session.add(record)
    db.session.commit()
    
    flash('工作记录添加成功！', 'success')
    return redirect(url_for('work'))

# 删除工作记录
@app.route('/work/delete/<int:record_id>')
@login_required
def delete_work(record_id):
    record = WorkRecord.query.get_or_404(record_id)
    if record.user_id == current_user.id:
        db.session.delete(record)
        db.session.commit()
        flash('工作记录已删除', 'success')
    return redirect(url_for('work'))

# 总日历页面 - 查看所有记录
@app.route('/calendar')
@login_required
def all_calendar():
    periods = Period.query.filter_by(user_id=current_user.id).all()
    study_records = StudyRecord.query.filter_by(user_id=current_user.id).all()
    work_records = WorkRecord.query.filter_by(user_id=current_user.id).all()
    return render_template('all_calendar.html', 
                           periods=periods, 
                           study_records=study_records,
                           work_records=work_records,
                           user=current_user, 
                           timedelta=timedelta)

# 用户反馈页面
@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        feedback_type = request.form.get('feedback_type')
        contact = request.form.get('contact', '')
        content = request.form.get('content')
        
        if not content:
            flash('请填写反馈内容！', 'error')
            return redirect(url_for('feedback'))
        
        feedback = Feedback(
            user_id=current_user.id,
            feedback_type=feedback_type,
            contact=contact,
            content=content,
            status='pending'
        )
        db.session.add(feedback)
        db.session.commit()
        
        flash('感谢您的反馈！我们会尽快处理！', 'success')
        return redirect(url_for('feedback'))
    
    # 获取当前用户的反馈记录
    feedbacks = Feedback.query.filter_by(user_id=current_user.id).order_by(Feedback.created_at.desc()).all()
    return render_template('feedback.html', feedbacks=feedbacks, user=current_user)

# 聊天主页 - 好友列表
@app.route('/chat')
@login_required
def chat():
    # 获取好友列表（已接受的）
    friends = db.session.query(User).join(
        Friend, (Friend.friend_id == User.id) | (Friend.user_id == User.id)
    ).filter(
        ((Friend.user_id == current_user.id) | (Friend.friend_id == current_user.id)),
        Friend.status == 'accepted',
        User.id != current_user.id
    ).all()
    
    # 获取未读消息数
    unread_count = ChatMessage.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    
    # 获取好友请求
    friend_requests = db.session.query(User, Friend).join(
        Friend, Friend.user_id == User.id
    ).filter(
        Friend.friend_id == current_user.id,
        Friend.status == 'pending'
    ).all()
    
    return render_template('chat.html', friends=friends, friend_requests=friend_requests, 
                           unread_count=unread_count, user=current_user)

# 添加好友
@app.route('/chat/add_friend', methods=['POST'])
@login_required
def add_friend():
    username = request.form.get('username')
    if not username:
        flash('请输入用户名！', 'error')
        return redirect(url_for('chat'))
    
    # 查找用户
    friend_user = User.query.filter_by(username=username).first()
    if not friend_user:
        flash('用户不存在！', 'error')
        return redirect(url_for('chat'))
    
    if friend_user.id == current_user.id:
        flash('不能添加自己为好友！', 'error')
        return redirect(url_for('chat'))
    
    # 检查是否已经是好友
    existing = Friend.query.filter(
        ((Friend.user_id == current_user.id) & (Friend.friend_id == friend_user.id)) |
        ((Friend.user_id == friend_user.id) & (Friend.friend_id == current_user.id))
    ).first()
    
    if existing:
        if existing.status == 'accepted':
            flash('你们已经是好友了！', 'info')
        else:
            flash('已经发送过好友请求了！', 'info')
        return redirect(url_for('chat'))
    
    # 创建好友请求
    friend = Friend(user_id=current_user.id, friend_id=friend_user.id, status='pending')
    db.session.add(friend)
    db.session.commit()
    
    flash(f'已向 {username} 发送好友请求！', 'success')
    return redirect(url_for('chat'))

# 同意/拒绝好友请求
@app.route('/chat/friend_request/<int:request_id>/<action>')
@login_required
def friend_request(request_id, action):
    friend = Friend.query.get_or_404(request_id)
    
    if friend.friend_id != current_user.id:
        flash('无权操作！', 'error')
        return redirect(url_for('chat'))
    
    if action == 'accept':
        friend.status = 'accepted'
        db.session.commit()
        flash('已同意好友请求！', 'success')
    elif action == 'reject':
        db.session.delete(friend)
        db.session.commit()
        flash('已拒绝好友请求！', 'success')
    
    return redirect(url_for('chat'))

# 与好友聊天页面
@app.route('/chat/<int:friend_id>')
@login_required
def chat_room(friend_id):
    # 检查是否是好友
    friendship = Friend.query.filter(
        ((Friend.user_id == current_user.id) & (Friend.friend_id == friend_id)) |
        ((Friend.user_id == friend_id) & (Friend.friend_id == current_user.id))
    ).filter(Friend.status == 'accepted').first()
    
    if not friendship:
        flash('你们还不是好友！', 'error')
        return redirect(url_for('chat'))
    
    friend = User.query.get_or_404(friend_id)
    
    # 获取聊天记录
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == friend_id)) |
        ((ChatMessage.sender_id == friend_id) & (ChatMessage.receiver_id == current_user.id))
    ).order_by(ChatMessage.created_at.asc()).all()
    
    # 标记未读消息为已读
    ChatMessage.query.filter_by(sender_id=friend_id, receiver_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    # 获取所有记录用于分享（自己的记录）
    periods = Period.query.filter_by(user_id=current_user.id).all()
    study_records = StudyRecord.query.filter_by(user_id=current_user.id).all()
    work_records = WorkRecord.query.filter_by(user_id=current_user.id).all()
    
    # 获取好友的记录（用于显示对方分享的记录详情）
    friend_periods = Period.query.filter_by(user_id=friend_id).all()
    friend_study_records = StudyRecord.query.filter_by(user_id=friend_id).all()
    friend_work_records = WorkRecord.query.filter_by(user_id=friend_id).all()
    
    return render_template('chat_room.html', friend=friend, messages=messages,
                           periods=periods, study_records=study_records, 
                           work_records=work_records,
                           friend_periods=friend_periods,
                           friend_study_records=friend_study_records,
                           friend_work_records=friend_work_records,
                           user=current_user)

# 发送消息
@app.route('/chat/send', methods=['POST'])
@login_required
def send_message():
    receiver_id = request.form.get('receiver_id')
    message = request.form.get('message', '').strip()
    message_type = request.form.get('message_type', 'text')
    record_id = request.form.get('record_id')
    record_type = request.form.get('record_type')
    
    if not receiver_id:
        flash('请选择接收者！', 'error')
        return redirect(url_for('chat'))
    
    receiver_id = int(receiver_id)
    
    # 检查是否是好友
    friendship = Friend.query.filter(
        ((Friend.user_id == current_user.id) & (Friend.friend_id == receiver_id)) |
        ((Friend.user_id == receiver_id) & (Friend.friend_id == current_user.id))
    ).filter(Friend.status == 'accepted').first()
    
    if not friendship:
        flash('你们还不是好友！', 'error')
        return redirect(url_for('chat'))
    
    if message_type == 'text' and not message:
        flash('消息内容不能为空！', 'error')
        return redirect(url_for('chat_room', friend_id=receiver_id))
    
    # 创建消息
    chat_msg = ChatMessage(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        message=message,
        message_type=message_type,
        record_id=record_id,
        record_type=record_type
    )
    db.session.add(chat_msg)
    db.session.commit()
    
    return redirect(url_for('chat_room', friend_id=receiver_id))

# 注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('请填写用户名和密码！', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在！', 'error')
            return redirect(url_for('register'))
        
        user = User(
            username=username, 
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('index'))
    
    return render_template('register.html')

# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        
        flash('用户名或密码错误！', 'error')
    return render_template('login.html')

# 登出
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# 管理员登录
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 验证管理员账号
        if username == 'admin' and password == 'yzh18998301631':
            # 查找或创建管理员用户
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    password_hash=generate_password_hash('yzh18998301631'),
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
            else:
                admin.is_admin = True
                db.session.commit()
            
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        
        flash('管理员账号或密码错误！', 'error')
    return render_template('admin_login.html')

# 管理员后台
@app.route('/admin')
@login_required
def admin_dashboard():
    # 检查是否是管理员
    if not current_user.is_admin:
        flash('您没有权限访问该页面！', 'error')
        return redirect(url_for('index'))
    
    # 获取所有用户
    users = User.query.filter_by(is_admin=False).all()
    
    # 获取所有记录
    all_periods = Period.query.all()
    all_study = StudyRecord.query.all()
    all_work = WorkRecord.query.all()
    all_feedback = Feedback.query.order_by(Feedback.created_at.desc()).all()
    
    return render_template('admin.html', 
                           users=users,
                           all_periods=all_periods,
                           all_study=all_study,
                           all_work=all_work,
                           all_feedback=all_feedback,
                           user=current_user)

# 回复用户反馈
@app.route('/admin/feedback/reply/<int:feedback_id>', methods=['POST'])
@login_required
def admin_feedback_reply(feedback_id):
    if not current_user.is_admin:
        flash('您没有权限操作！', 'error')
        return redirect(url_for('index'))
    
    feedback = Feedback.query.get_or_404(feedback_id)
    feedback.reply = request.form.get('reply')
    feedback.status = 'replied'
    db.session.commit()
    
    flash('回复成功！', 'success')
    return redirect(url_for('admin_dashboard'))

# 删除用户
@app.route('/admin/delete_user', methods=['POST'])
@login_required
def admin_delete_user():
    if not current_user.is_admin:
        flash('您没有权限操作！', 'error')
        return redirect(url_for('index'))
    
    user_id = request.form.get('user_id')
    user = User.query.get_or_404(user_id)
    
    # 不能删除自己
    if user.id == current_user.id:
        flash('不能删除自己的账号！', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # 删除用户的所有记录
    Period.query.filter_by(user_id=user.id).delete()
    StudyRecord.query.filter_by(user_id=user.id).delete()
    WorkRecord.query.filter_by(user_id=user.id).delete()
    Feedback.query.filter_by(user_id=user.id).delete()
    
    # 删除用户
    db.session.delete(user)
    db.session.commit()
    
    flash(f'用户 {user.username} 已删除！', 'success')
    return redirect(url_for('admin_dashboard'))

# 重置用户密码
@app.route('/admin/reset_password', methods=['POST'])
@login_required
def admin_reset_password():
    if not current_user.is_admin:
        flash('您没有权限操作！', 'error')
        return redirect(url_for('index'))
    
    user_id = request.form.get('user_id')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password != confirm_password:
        flash('两次输入的密码不一致！', 'error')
        return redirect(url_for('admin_dashboard'))
    
    user = User.query.get_or_404(user_id)
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    flash(f'用户 {user.username} 的密码已重置！', 'success')
    return redirect(url_for('admin_dashboard'))

# 忘记密码页面
@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'send_code':
            # 发送验证码
            email = request.form.get('email')
            user = User.query.filter_by(email=email).first()
            
            if not user:
                flash('该邮箱未注册！', 'error')
            else:
                # 生成6位验证码
                code = ''.join(random.choices(string.digits, k=6))
                verification_codes[email] = {
                    'code': code,
                    'time': time.time(),
                    'user_id': user.id
                }
                
                try:
                    msg = Message('🌸 月经记录本 - 验证码', recipients=[email])
                    msg.body = f'''您好 {user.username}！

您的验证码是：{code}

验证码有效期为10分钟，请尽快完成验证。

如果这不是您的操作，请忽略此邮件。

---
月经记录本'''
                    mail.send(msg)
                    flash('验证码已发送到您的邮箱！', 'success')
                except Exception as e:
                    flash(f'发送失败: {str(e)}', 'error')
            
            return render_template('forgot.html', email=email, step='verify')
        
        elif action == 'reset':
            # 重置密码
            email = request.form.get('email')
            code = request.form.get('code')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password != confirm_password:
                flash('两次输入的密码不一致！', 'error')
                return render_template('forgot.html', email=email, step='reset')
            
            # 验证验证码
            if email not in verification_codes:
                flash('请先获取验证码！', 'error')
                return render_template('forgot.html', email=email, step='verify')
            
            if time.time() - verification_codes[email]['time'] > 600:  # 10分钟有效期
                del verification_codes[email]
                flash('验证码已过期，请重新获取！', 'error')
                return render_template('forgot.html', email=email, step='verify')
            
            if verification_codes[email]['code'] != code:
                flash('验证码错误！', 'error')
                return render_template('forgot.html', email=email, step='reset')
            
            # 更新密码
            user = User.query.filter_by(email=email).first()
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            del verification_codes[email]
            flash('密码重置成功！请使用新密码登录', 'success')
            return redirect(url_for('login'))
    
    return render_template('forgot.html')

# 个人信息页面
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # 处理表单提交
        current_user.nickname = request.form.get('nickname', '')
        current_user.phone = request.form.get('phone', '')
        
        # 处理邮箱修改
        new_email = request.form.get('email', '')
        if new_email and new_email != current_user.email:
            # 检查邮箱是否已被占用
            existing = User.query.filter_by(email=new_email).first()
            if existing and existing.id != current_user.id:
                flash('该邮箱已被其他用户使用！', 'error')
                return redirect(url_for('profile'))
            current_user.email = new_email
        
        birthday_str = request.form.get('birthday')
        if birthday_str:
            try:
                current_user.birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
            except:
                pass
        
        # 处理头像上传
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"avatar_{current_user.id}_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}")
                file.save(os.path.join(app.config['AVATAR_FOLDER'], filename))
                
                # 删除旧头像
                if current_user.avatar:
                    old_path = os.path.join(app.config['AVATAR_FOLDER'], current_user.avatar)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                current_user.avatar = filename
        
        db.session.commit()
        flash('个人信息更新成功！', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=current_user)

# 头像文件访问
@app.route('/avatars/<filename>')
def avatars(filename):
    return send_from_directory(app.config['AVATAR_FOLDER'], filename)

# 添加记录
@app.route('/add', methods=['POST'])
@login_required
def add_period():
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
    flow = request.form.get('flow', 'medium')
    notes = request.form.get('notes', '')
    
    period = Period(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        flow=flow,
        notes=notes
    )
    db.session.add(period)
    db.session.commit()
    
    flash('记录添加成功！', 'success')
    return redirect(url_for('index'))

# 删除记录
@app.route('/delete/<int:period_id>')
@login_required
def delete_period(period_id):
    period = Period.query.get_or_404(period_id)
    if period.user_id == current_user.id:
        db.session.delete(period)
        db.session.commit()
        flash('记录已删除', 'success')
    return redirect(url_for('index'))

# API: 获取当前用户数据
@app.route('/api/data')
@login_required
def api_data():
    periods = Period.query.filter_by(user_id=current_user.id).all()
    data = []
    for p in periods:
        data.append({
            'id': p.id,
            'start_date': p.start_date.strftime('%Y-%m-%d'),
            'end_date': p.end_date.strftime('%Y-%m-%d'),
            'flow': p.flow,
            'notes': p.notes
        })
    return jsonify(data)

# 检查邮箱是否已注册 (AJAX)
@app.route('/api/check_email')
def check_email():
    email = request.args.get('email')
    user = User.query.filter_by(email=email).first()
    return jsonify({'exists': user is not None})

# ==================== AI 功能 ====================

def call_deepseek(prompt, system_prompt=None):
    """调用 DeepSeek API"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"抱歉，AI服务暂时不可用: {str(e)}"

# AI 预测经期
@app.route('/api/ai/predict')
@login_required
def ai_predict_period():
    """基于历史数据预测下次经期"""
    periods = Period.query.filter_by(user_id=current_user.id).order_by(Period.start_date.desc()).limit(10).all()
    
    if len(periods) < 2:
        return jsonify({
            'success': False,
            'message': '需要至少2条经期记录才能进行预测'
        })
    
    # 计算平均周期
    cycles = []
    for i in range(len(periods) - 1):
        cycle = (periods[i].start_date - periods[i+1].start_date).days
        cycles.append(cycle)
    
    avg_cycle = sum(cycles) / len(cycles)
    last_period = periods[0]
    predicted_date = last_period.start_date + timedelta(days=int(avg_cycle))
    
    # 准备历史数据给AI分析
    history_text = "\n".join([
        f"第{i+1}次: {p.start_date} 到 {p.end_date}, 经量: {p.flow}"
        for i, p in enumerate(periods[:6])
    ])
    
    system_prompt = """你是一个专业的经期健康助手。根据用户的历史经期记录，分析规律并给出预测和健康建议。
请用温暖、关心的语气回复，回复使用中文。"""
    
    prompt = f"""用户的历史经期记录：
{history_text}

平均经期周期: {avg_cycle:.1f} 天
最近一次经期开始日期: {last_period.start_date}
预测下次经期开始日期: {predicted_date}

请分析用户的经期规律，并给出：
1. 预测的下次经期日期
2. 经期健康建议（如饮食、运动、休息等）
3. 注意事项

请用简洁友好的方式回复。"""
    
    ai_response = call_deepseek(prompt, system_prompt)
    
    return jsonify({
        'success': True,
        'predicted_date': predicted_date.strftime('%Y-%m-%d'),
        'avg_cycle': round(avg_cycle, 1),
        'ai_analysis': ai_response
    })

# AI 健康建议
@app.route('/api/ai/advice', methods=['POST'])
@login_required
def ai_get_advice():
    """获取个性化健康建议"""
    data = request.get_json()
    user_input = data.get('question', '')
    
    # 获取用户最近的经期数据
    periods = Period.query.filter_by(user_id=current_user.id).order_by(Period.start_date.desc()).limit(3).all()
    
    history_text = "暂无记录"
    if periods:
        history_text = "\n".join([
            f"- {p.start_date} 到 {p.end_date}, 经量: {p.flow}"
            for p in periods
        ])
    
    system_prompt = """你是一个专业、温暖的经期健康顾问。请根据用户的问题和经期历史记录，给出专业而贴心的建议。
注意：如果用户询问的是医疗相关问题，请提醒用户咨询专业医生。"""
    
    prompt = f"""用户最近3次经期记录：
{history_text}

用户问题: {user_input}

请根据用户的经期历史和当前问题，给出适合的建议。如果用户没有提供具体问题，请给出通用的经期健康建议。"""
    
    ai_response = call_deepseek(prompt, system_prompt)
    
    return jsonify({
        'success': True,
        'advice': ai_response
    })

# AI 聊天助手
@app.route('/api/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    """AI 聊天助手"""
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({'success': False, 'message': '请输入内容'})
    
    # 获取用户历史记录作为上下文
    periods = Period.query.filter_by(user_id=current_user.id).order_by(Period.start_date.desc()).limit(5).all()
    
    history_text = "暂无记录"
    if periods:
        history_text = "\n".join([
            f"- {p.start_date} 到 {p.end_date}, 经量: {p.flow}"
            for p in periods
        ])
    
    system_prompt = """你是一个温柔、专业、亲切的经期健康助手"小经"。你了解经期健康知识，能够回答用户关于经期的问题。
请用轻松友好的语气聊天，适当使用emoji，回复控制在200字以内。"""
    
    prompt = f"""用户的经期历史记录：
{history_text}

用户说: {message}

请以"小经"的身份回复用户。"""
    
    ai_response = call_deepseek(prompt, system_prompt)
    
    return jsonify({
        'success': True,
        'reply': ai_response
    })

# AI 周报生成
@app.route('/api/ai/report')
@login_required
def ai_generate_report():
    """生成经期健康报告"""
    periods = Period.query.filter_by(user_id=current_user.id).order_by(Period.start_date.desc()).limit(10).all()
    
    if not periods:
        return jsonify({
            'success': False,
            'message': '暂无经期记录'
        })
    
    # 计算统计数据
    total_records = len(periods)
    cycle_days = []
    period_days = []
    
    for i in range(len(periods) - 1):
        cycle_days.append((periods[i].start_date - periods[i+1].start_date).days)
    
    for p in periods:
        period_days.append((p.end_date - p.start_date).days + 1)
    
    avg_cycle = sum(cycle_days) / len(cycle_days) if cycle_days else 28
    avg_period = sum(period_days) / len(period_days)
    
    # 统计经量分布
    flow_count = {'light': 0, 'medium': 0, 'heavy': 0}
    for p in periods:
        if p.flow in flow_count:
            flow_count[p.flow] += 1
    
    history_text = "\n".join([
        f"第{i+1}次: {p.start_date} 开始，持续 {((p.end_date - p.start_date).days + 1)} 天，经量: {p.flow}"
        for i, p in enumerate(periods[:6])
    ])
    
    system_prompt = """你是一个专业的经期健康分析师。根据用户的经期数据，生成一份详细的健康报告。
请用清晰的结构化方式呈现，使用emoji让报告更生动。"""
    
    prompt = f"""请根据以下用户的经期数据，生成一份健康报告：

历史记录：
{history_text}

统计数据：
- 记录次数: {total_records} 次
- 平均周期: {avg_cycle:.1f} 天
- 平均经期时长: {avg_period:.1f} 天
- 经量分布: 少量{flow_count['light']}次, 中等{flow_count['medium']}次, 大量{flow_count['heavy']}次

请生成包括以下内容的健康报告：
1. 周期分析 - 你的经期规律是否正常
2. 健康评分 (1-10分)
3. 存在的问题和建议
4. 下次经期预测
5. 温馨小贴士

回复使用中文，报告结构清晰。"""
    
    ai_response = call_deepseek(prompt, system_prompt)
    
    return jsonify({
        'success': True,
        'report': ai_response,
        'stats': {
            'avg_cycle': round(avg_cycle, 1),
            'avg_period': round(avg_period, 1),
            'total_records': total_records
        }
    })

# ==================== 学习 AI 功能 ====================

# AI 学习计划生成
@app.route('/api/ai/study/plan', methods=['POST'])
@login_required
def ai_study_plan():
    """生成学习计划"""
    data = request.get_json()
    subject = data.get('subject', '')
    goal = data.get('goal', '')
    days = data.get('days', 7)
    
    if not subject:
        return jsonify({'success': False, 'message': '请输入学习科目'})
    
    prompt = f"""请为用户生成一个{days}天的{subject}学习计划。

用户目标: {goal if goal else '暂无具体目标'}

请生成一个超级详细的学习计划，必须包含以下内容：

📅 **第1天到第{days}天** 每天都需要有：
1. 📖 学习内容：具体要学习的知识点或章节
2. ⏱️ 学习时长：建议学习多少分钟
3. 🎯 今日目标：今天要达成什么
4. 💡 学习方法：用什么方法学习

请严格按照以下表格格式输出：
| 天数 | 学习内容 | 学习时长 | 今日目标 | 学习方法 |
|------|----------|----------|----------|----------|
| 第1天 | 内容 | X分钟 | 目标 | 方法 |
| 第2天 | 内容 | X分钟 | 目标 | 方法 |
...（依次列出所有{days}天）

使用emoji让计划更生动，回复使用中文。"""
    
    system_prompt = """你是一个专业、耐心的学习顾问。你擅长制定学习计划，帮助用户高效学习。"""
    
    ai_response = call_deepseek(prompt, system_prompt)
    
    return jsonify({
        'success': True,
        'plan': ai_response
    })

# AI 学习效率分析
@app.route('/api/ai/study/analyze')
@login_required
def ai_study_analyze():
    """分析学习效率"""
    records = StudyRecord.query.filter_by(user_id=current_user.id).order_by(StudyRecord.date.desc()).limit(20).all()
    
    if not records:
        return jsonify({
            'success': False,
            'message': '暂无学习记录，无法分析'
        })
    
    # 统计数据
    total_duration = sum(r.duration for r in records)
    subject_stats = {}
    for r in records:
        if r.subject not in subject_stats:
            subject_stats[r.subject] = {'count': 0, 'duration': 0}
        subject_stats[r.subject]['count'] += 1
        subject_stats[r.subject]['duration'] += r.duration
    
    # 按星期几统计
    weekday_stats = {i: 0 for i in range(7)}
    for r in records:
        weekday_stats[r.date.weekday()] += r.duration
    
    best_day = max(weekday_stats, key=weekday_stats.get)
    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    
    history_text = "\n".join([
        f"- {r.date}: {r.subject}, {r.duration}分钟"
        for r in records[:15]
    ])
    
    prompt = f"""请分析用户的学习数据，找出学习规律和效率问题：

学习记录：
{history_text}

统计数据：
- 总学习时长: {total_duration} 分钟
- 学习科目分布: {subject_stats}
- 一周各天学习时长: {weekdays[best_day]}学习时长最长

请给出：
1. 学习效率评分 (1-10分)
2. 学习习惯分析
3. 存在的问题
4. 改进建议
5. 最佳学习时间建议

回复使用中文，结构清晰。"""
    
    system_prompt = """你是一个专业的学习效率分析师。你擅长分析学习数据，发现学习规律和问题。"""
    
    ai_response = call_deepseek(prompt, system_prompt)
    
    return jsonify({
        'success': True,
        'analysis': ai_response,
        'stats': {
            'total_duration': total_duration,
            'best_day': weekdays[best_day],
            'subject_count': len(subject_stats)
        }
    })

# AI 错题本辅导
@app.route('/api/ai/study/wrongQuestion', methods=['POST'])
@login_required
def ai_wrong_question():
    """AI 错题本辅导"""
    data = request.get_json()
    question = data.get('question', '')
    subject = data.get('subject', '')
    user_answer = data.get('user_answer', '')
    
    if not question:
        return jsonify({'success': False, 'message': '请输入错题内容'})
    
    prompt = f"""用户有一道错题需要讲解：

科目: {subject if subject else '未指定'}
错题: {question}
用户的答案: {user_answer if user_answer else '暂无'}

请帮助用户：
1. 分析这道题的知识点
2. 找出用户的错误原因
3. 给出正确的解题思路
4. 讲解相关知识点
5. 出一道类似的练习题

请用通俗易懂的方式讲解，回复使用中文。"""
    
    system_prompt = """你是一个专业、耐心的学科辅导老师。你擅长讲解题目，分析错误原因，帮助学生掌握知识点。"""
    
    ai_response = call_deepseek(prompt, system_prompt)
    
    return jsonify({
        'success': True,
        'explanation': ai_response,
        'subject': subject,
        'question': question,
        'user_answer': user_answer
    })

# 保存错题到错题集
@app.route('/api/ai/study/saveWrongQuestion', methods=['POST'])
@login_required
def ai_save_wrong_question():
    """保存错题到错题集"""
    data = request.get_json()
    subject = data.get('subject', '')
    question = data.get('question', '')
    user_answer = data.get('user_answer', '')
    ai_explanation = data.get('ai_explanation', '')
    
    if not question:
        return jsonify({'success': False, 'message': '请输入错题内容'})
    
    # 提取知识点和练习题
    knowledge_points = ""
    practice_question = ""
    
    # 简单解析AI回复，提取知识点和练习题
    if "知识点" in ai_explanation:
        try:
            parts = ai_explanation.split("知识点")
            if len(parts) > 1:
                knowledge_part = parts[1].split("\n")[0]
                knowledge_points = knowledge_part.strip()
        except:
            pass
    
    if "练习题" in ai_explanation or "类似题" in ai_explanation:
        try:
            for line in ai_explanation.split("\n"):
                if "练习题" in line or "类似题" in line:
                    practice_question = line.split("：")[-1] if "：" in line else line
                    break
        except:
            pass
    
    wrong_q = WrongQuestion(
        user_id=current_user.id,
        subject=subject or '未分类',
        question=question,
        user_answer=user_answer,
        ai_explanation=ai_explanation,
        knowledge_points=knowledge_points,
        practice_question=practice_question
    )
    db.session.add(wrong_q)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '错题已保存到错题集',
        'id': wrong_q.id
    })

# 重新生成错题解答
@app.route('/api/ai/study/regenerateWrongQuestion', methods=['POST'])
@login_required
def ai_regenerate_wrong_question():
    """重新生成错题解答"""
    data = request.get_json()
    question = data.get('question', '')
    subject = data.get('subject', '')
    user_answer = data.get('user_answer', '')
    
    if not question:
        return jsonify({'success': False, 'message': '请输入错题内容'})
    
    prompt = f"""用户有一道错题需要讲解，请用不同的方式解答：

科目: {subject if subject else '未指定'}
错题: {question}
用户的答案: {user_answer if user_answer else '暂无'}

请用不同的解题思路和方法来讲解：
1. 分析这道题涉及的知识点
2. 详细讲解正确的解题方法
3. 指出常见错误原因
4. 总结解题技巧
5.出一道不同类型的练习题

请用通俗易懂、生动有趣的方式讲解，回复使用中文。"""
    
    system_prompt = """你是一个专业、耐心的学科辅导老师。你擅长用不同的方法讲解题目，帮助学生真正理解。"""
    
    ai_response = call_deepseek(prompt, system_prompt)
    
    return jsonify({
        'success': True,
        'explanation': ai_response
    })

# 获取错题集列表
@app.route('/api/ai/study/wrongQuestions')
@login_required
def get_wrong_questions():
    """获取错题集列表"""
    subject = request.args.get('subject', '')
    
    query = WrongQuestion.query.filter_by(user_id=current_user.id)
    if subject:
        query = query.filter_by(subject=subject)
    
    questions = query.order_by(WrongQuestion.created_at.desc()).all()
    
    data = []
    for q in questions:
        data.append({
            'id': q.id,
            'subject': q.subject,
            'question': q.question,
            'user_answer': q.user_answer,
            'ai_explanation': q.ai_explanation,
            'knowledge_points': q.knowledge_points,
            'practice_question': q.practice_question,
            'created_at': q.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({'success': True, 'questions': data})

import re
from datetime import datetime as dt

# AI 接受学习计划
@app.route('/api/ai/study/acceptPlan', methods=['POST'])
@login_required
def ai_accept_study_plan():
    """接受AI生成的学习计划，批量添加学习记录"""
    data = request.get_json()
    plan_text = data.get('plan', '')
    subject = data.get('subject', '')
    
    if not plan_text:
        return jsonify({'success': False, 'message': '请先生成学习计划'})
    
    # 解析计划内容，提取每天的学习内容
    # 匹配类似 "第1天" 或 "Day 1" 或 "1." 的模式
    pattern = r'(?:第\s*(\d+)\s*天|Day\s*(\d+)|(\d+)\.)'
    matches = re.findall(pattern, plan_text)
    
    if not matches:
        return jsonify({'success': False, 'message': '无法解析学习计划格式'})
    
    added_count = 0
    today = dt.now().date()
    
    # 解析计划内容，提取每天的学习内容
    lines = plan_text.split('\n')
    daily_plans = []
    max_day = 0
    
    # 首先找出总天数
    for line in lines:
        day_match = re.search(r'第\s*(\d+)\s*天', line)
        if day_match:
            day_num = int(day_match.group(1))
            max_day = max(max_day, day_num)
    
    if max_day == 0:
        return jsonify({'success': False, 'message': '无法解析学习计划格式'})
    
    # 解析每天的内容
    for line in lines:
        day_match = re.search(r'第\s*(\d+)\s*天', line)
        if day_match:
            day_num = int(day_match.group(1))
            
            # 提取学习时长 - 查找表格中的分钟数
            duration = 60  # 默认60分钟
            minute_match = re.search(r'(\d+)\s*分钟', line)
            if minute_match:
                duration = int(minute_match.group(1))
            
            # 提取学习内容 - 查找 "| 内容 |" 格式
            content = ""
            parts = line.split('|')
            if len(parts) >= 3:
                # 第二列通常是学习内容
                content = parts[2].strip() if parts[2].strip() else f"第{day_num}天学习"
            else:
                # 尝试从文本中提取
                content = line.replace(f'第{day_num}天', '').strip()
                if not content:
                    content = f"第{day_num}天学习"
            
            # 提取学习目标
            goal = ""
            if len(parts) >= 5:
                goal = parts[4].strip()
            
            # 提取学习方法
            method = ""
            if len(parts) >= 6:
                method = parts[5].strip()
            
            # 组合学习内容
            plan_content = f"📖 {content}"
            if goal:
                plan_content += f"\n🎯 目标: {goal}"
            if method:
                plan_content += f"\n💡 方法: {method}"
            
            daily_plans.append({
                'day': day_num,
                'duration': duration,
                'content': plan_content
            })
    
    if not daily_plans:
        return jsonify({'success': False, 'message': '无法解析学习计划格式'})
    
    added_count = 0
    
    # 只添加不超过max_day天的记录
    for plan_info in daily_plans:
        if plan_info['day'] > max_day:
            continue
            
        # 计划日期从今天开始
        plan_date = today + timedelta(days=plan_info['day'] - 1)
        
        # 创建学习记录
        record = StudyRecord(
            user_id=current_user.id,
            date=plan_date,
            subject=subject or '学习',
            duration=plan_info['duration'],
            plan=plan_info['content'],
            notes='AI生成学习计划'
        )
        db.session.add(record)
        added_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'added_count': added_count,
        'message': f'成功添加 {added_count} 条学习记录'
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
