from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    account = StringField('帐号', validators=[DataRequired(message='帐户不能为空'), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired(message='密码不能为空')])
    remember_me = BooleanField('保持登录')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    email = StringField('电子邮箱', validators=[DataRequired(message='邮箱不能为空'), Length(1, 64),
                                            Email(message='请输入有效的邮箱地址')])
    username = StringField('用户名', validators=[DataRequired(message='用户名不能为空'), Length(1, 64),
                                              Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                     '用户名只能由字母，数字，点，和下划线组成')])
    password = PasswordField('密码', validators=[DataRequired(message='密码不能为空'),
                                               EqualTo('password2', message='密码必须一样')])
    password2 = PasswordField('确认密码', validators=[DataRequired(message='密码不能为空')])
    submit = SubmitField('注册')

    def validate_email(self, field):  # 以validate_ 开头且后面跟着字段名的方法,自动调用验证
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已经被注册')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已经被使用')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('旧密码', validators=[DataRequired(message='密码不能为空')])
    password = PasswordField('新密码', validators=[DataRequired(message='密码不能为空'), EqualTo(
        'password2', message='密码必须一致')])
    password2 = PasswordField('确认新密码', validators=[DataRequired(message='密码不能为空')])
    submit = SubmitField('更改密码')


class EnterAccountForm(FlaskForm):
    email = StringField('电子邮箱', validators=[DataRequired(message='邮箱不能为空'), Length(1, 64),
                                             Email(message='请输入有效的邮箱地址')])
    submit = SubmitField('发送确认邮件')


class ResetPasswordForm(FlaskForm):
    email = StringField('电子邮箱', validators=[DataRequired(message='邮箱不能为空'), Length(1, 64),
                                             Email(message='请输入有效的邮箱地址')])
    password = PasswordField('新密码', validators=[DataRequired(message='密码不能为空'), EqualTo(
        'password2', message='密码必须一致')])
    password2 = PasswordField('确认新密码', validators=[DataRequired(message='密码不能为空')])
    submit = SubmitField('重置密码')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError ('无效的用户')


# class ChangeEmailForm(FlaskForm):
#     email = StringField('电子邮箱', validators=[DataRequired(message='邮箱不能为空'), Length(1, 64),
#                                              Email(message='请输入有效的邮箱地址')])
#     password = PasswordField('密码', validators=[DataRequired(message='密码不能为空')])
#     submit = SubmitField('更换邮箱')
#
#     def validate_email(self,field):
#         if User.query.filter_by(email=field.data).first():
#             raise ValidationError ('邮箱已注册')
