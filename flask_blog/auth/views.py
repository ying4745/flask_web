from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user

from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, \
    EnterAccountForm, ResetPasswordForm
from .. import db
from ..email import send_email
from ..models import User


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:  # 用户已登录
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.' \
                and request.endpoint != 'static':
        # 用户还没确认，请求的端点不在‘auth.’，‘static’中
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')  # 未确认页面
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        # 如果是匿名用户 或者 用户确认了
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            # 调用Flask_Login中的login_user()函数，在用户会话中标记为登录
            # 参数是要登录的用户，以及可选的“记住我”布尔值
            return redirect(request.args.get('next') or url_for('main.index'))
            # Flask - Login会把原地址保存在查询字符串的next参数中，这个参数可从request.args字典中读取。
            # 如果查询字符串中没有next参数，则重定向到首页
        flash('无效的用户名和密码!')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('你已经退出!')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():  # 注册
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email,'确认你的账户','auth/email/confirm', user=user,token=token)
        flash('你已注册成功,一封确认邮件已通过电子邮件发送给你.')
        login_user(user)
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):  # 确认账户
    if current_user.confirmed:  # 检查用户是否确认过
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('您已确认您的账户，非常感谢！')
    else:
        flash('确认链接无效或已过期')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():  # 重新发送确认账户邮件
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, '确认你的账户', 'auth/email/confirm',
               user=current_user, token=token)
    flash('一封新的确认邮件已经通过电子邮件发送给你')
    return redirect(url_for('main.index'))


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


@auth.route('/enter-account', methods=['GET', 'POST'])
def enter_account():  # 重置密码 - 1 确认重置密码的账户 发送邮件确认
    if not current_user.is_anonymous:  # 如果用户已登录
        return redirect(url_for('main.index'))
    form = EnterAccountForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, '重置密码', 'auth/email/reset_password',
                       user=user, token=token)
            # 源代码中有 next=request.args.get('next') 感觉没用上
            flash('一封新的确认邮件已经通过电子邮件发送给你')
            return redirect(url_for('main.index'))
        flash('无效的用户')
    return render_template('auth/enter_account.html', form=form)


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):  # 重置密码 - 2 改密码
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('无效的用户')
        if user.reset_password(token,form.password.data):
            flash('你的密码已经重置成功')
            return redirect(url_for('.login'))
        else:
            flash('重置失败，账户错误或确认链接已失效')
    return render_template('auth/reset_password.html', form=form)


# @auth.route('/change-email', methods=['GET', 'POST'])
# @login_required
# def change_email_request():
#     form = ChangeEmailForm()
#     if  form.validate_on_submit():
#         if current_user.verify_password(form.password.data):
#             new_email = form.email.data
#             token = current_user.generate_email_change_token(new_email)
#             send_email(new_email, '确认你的邮箱地址', 'auth/email/change_email',
#                        user=current_user, token=token)
#             flash('一封确认邮箱地址的邮件已发送至你的邮箱')
#             return redirect(url_for('main.index'))
#         else:
#             flash('密码错误')
#     return render_template('auth/change_email.html', form=form)
#
#
# @auth.route('/change-email/<token>')
# @login_required
# def change_email(token):
#     if current_user.change_email(token):
#         flash('你的邮箱已经更新')
#     else:
#         flash('请求失败')
#     return redirect(url_for('main.index'))
