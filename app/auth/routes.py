from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm
from app.auth import bp

@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'specialist':
            return redirect(url_for('specialist.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('auth.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.index'))

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role != 'admin':
        flash('Only admins can register new users')
        return redirect(url_for('auth.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            full_name=form.full_name.data,
            role=form.role.data,
            specialty=form.specialty.data if form.role.data == 'specialist' else None
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('New user registered successfully!')
        return redirect(url_for('admin.dashboard'))
    return render_template('auth/register.html', title='Register', form=form)