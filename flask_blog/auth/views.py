from flask import render_template, redirect, request, url_for, flash, \
    abort
from flask_login import login_user, logout_user, login_required, \
                        current_user
from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, \
    UserForm
from ..models import User, Article
from .. import db


# @auth.before_app_request
# def before_request():
#     if current_user.is_authenticated():
#         current_user.ping()


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('无效的用户名和密码')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('你已经退出')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        flash('你现在可以登录了')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/change-password', methods=['GET', 'POST'])
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('你的密码已经更改')
            return redirect(url_for('main.index'))
        else:
            flash('密码错误')
    return render_template('auth/change_password.html', form=form)


@auth.route('/user/modify/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    form = UserForm()
    if form.validate_on_submit():
        # user = User.query.filter_by(username=username).first()
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('你的资料已更新')
        return redirect(url_for('auth.show_user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('auth/user.html', form=form)


@auth.route('/user/<username>')
@login_required
def show_user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    articles = user.articles.order_by(Article.timestamp.desc()).all()
    return render_template('auth/show_user.html',user=user, articles=articles)