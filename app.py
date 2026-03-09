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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
