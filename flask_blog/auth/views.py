from flask import render_template, redirect, request, url_for, flash, \
    current_app
from flask_login import login_user, logout_user, login_required, \
                        current_user
from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, \
    UserForm
from ..models import User, Article, Permission
from .. import db
from ..decorators import permission_required


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
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.articles.order_by(Article.timestamp.desc()).paginate(
                    page, per_page=current_app.config['FLASKY_ARTICLES_PER_PAGE'],
                    error_out=False)
    articles = pagination.items
    return render_template('auth/show_user.html',user=user, articles=articles,
                           pagination=pagination)


@auth.route('/follow/<username>')  # 关注
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('.show_user', username=username))
    if current_user.is_following(user):
        flash('你已经关注了这个人')
        return redirect(url_for('.show_user', username=username))
    current_user.follow(user)
    flash('你关注了%s' % username)
    return redirect(url_for('.show_user', username=username))


@auth.route('/unfollow/<username>')  # 取消关注
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('.show_user', username=username))
    if not current_user.is_following(user):
        flash('你没有关注这个人')
        return redirect(url_for('.show_user', username=username))
    current_user.unfollow(user)
    flash('你取消了对%s的关注' % username)
    return redirect(url_for('.show_user', username=username))


@auth.route('/followers/<username>')  # 被关注列表
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('.show_user', username=username))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(page,
                per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
                error_out=False)
    follows = [{'user':item.follower, 'timestamp':item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title='的粉丝',
                           endpoint='.followers', pagination=pagination,
                           follows=follows)\


@auth.route('/followed-by/<username>')  # 关注列表
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('.show_user', username=username))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(page,
                per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
                error_out=False)
    follows = [{'user':item.followed, 'timestamp':item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title='的关注',
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


