from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, \
    SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError
from ..models import Role, User
from flask_pagedown.fields import PageDownField


class UserForm(FlaskForm):
    name = StringField('姓名', validators=[Length(0, 64)])
    location = StringField('地址', validators=[Length(0, 64)])
    about_me = TextAreaField('自我简介')
    submit = SubmitField('提交')


class EditProfiledAdminForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64),
                                              Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                     '用户名只能由字母，数字，点，和下划线组成')])
    role = SelectField('角色', coerce=int)
    name = StringField('名字', validators=[Length(0, 64)])
    location = StringField('地址', validators=[Length(0, 64)])
    about_me = TextAreaField('个人风采')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfiledAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in \
                             Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已经被注册')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已经被使用')


class ArticleForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(1, 128)])
    content = PageDownField('正文', validators=[DataRequired()])
    submit = SubmitField('发布')


class CommentForm(FlaskForm):
    content = PageDownField('', validators=[DataRequired()])
    submit = SubmitField('发布')