# app/routes.py
'''
from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from app import db
from app.models import User, Role
from app.forms import RegistrationForm, LoginForm
from app.decorators import require_role


# Create a Blueprint
main = Blueprint('main', __name__)

@main.route("/")
@main.route("/index")
def index():
    return render_template('base.html') # Let's render the base template now

@main.route("/register", methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create user and save to database
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        user_role = Role.query.filter_by(name='User').first()
        if user_role:
            user.roles.append(user_role)

        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('main.login'))
        
    return render_template('register.html', title='Register', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            # Redirect to the page user was trying to access, or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
            
    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html', title='Dashboard')

@main.route("/admin_page")
@login_required
@require_role('Admin')
def admin_page():
    return "<h1>This is the Admin-Only Page</h1><p>Only users with the 'Admin' role can see this!</p>"
'''
# app/routes.py

from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from app import db, login_manager
from app.models import User, Role
from app.forms import RegistrationForm, LoginForm
from app.decorators import require_role

# 浏览器每次请求时，Flask-Login 会自动拿 session 里的 user_id 通过这个函数查出用户完整对象
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Create a Blueprint
main = Blueprint('main', __name__)

@main.route("/")
@main.route("/index")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    return render_template('welcome.html')


@main.route("/register", methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create user and save to database
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        # 💡 提示：你的 seed.py 刷入了常规角色（如 Guest/Operator/Admin 等）
        # 这里默认注册分配 'Guest' 或者保留你原本的 'User'（若你数据库有此角色）
        user_role = Role.query.filter_by(name='Guest').first() or Role.query.filter_by(name='User').first()
        if user_role:
            user.roles.append(user_role)

        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('main.login'))
        
    return render_template('register.html', title='Register', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            # Redirect to the page user was trying to access, or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
            
    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route("/dashboard")
@login_required
def dashboard():
    # return render_template('dashboard.html', title='Dashboard')
    return render_template('file_manager.html', title='资源管理器')

@main.route("/admin_page")
@login_required
@require_role('Admin')
def admin_page():
    return "<h1>This is the Admin-Only Page</h1><p>Only users with the 'Admin' role can see this!</p>"