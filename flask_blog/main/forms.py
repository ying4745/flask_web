from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms import StringField, SubmitField, TextAreaField, widgets, SelectField

from ..models import Role, User, Tag, Category
from .. import avatar


class UserForm(FlaskForm):
    avatar = FileField('头像上传', validators=[FileAllowed(avatar,'只能上传图片')])
    name = StringField('姓名', validators=[Length(0, 64)])
    location = StringField('地址', validators=[Length(0, 64)])
    about_me = TextAreaField('自我简介')
    submit = SubmitField('提交')


class EditProfiledAdminForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(message='邮箱不能为空'), Length(1, 64),
                                          Email(message='请输入有效的邮箱地址')])
    username = StringField('用户名', validators=[DataRequired(message='用户名不能为空'), Length(1, 64),
                                              Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                     '用户名只能由字母，数字，点，和下划线组成')])
    role = SelectField('角色', coerce=int)
    name = StringField('昵称', validators=[Length(0, 64)])
    location = StringField('地址', validators=[Length(0, 64)])
    about_me = TextAreaField('个人简介')
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

def get_tags():
    return Tag.query.all()

class ArticleForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(message='标题不能为空'), Length(1, 128)])
    category = SelectField('分类', coerce=int)
    tags = QuerySelectMultipleField('标签', query_factory=get_tags, get_label='name')
    content = TextAreaField('正文', validators=[DataRequired(message='正文不能为空')])
    submit = SubmitField('发布')

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        self.tags.choices = [(tag.id, tag.name)
                             for tag in Tag.query.order_by(Tag.name).all()]
        self.category.choices = [(Category.id, Category.name) for Category in \
                             Category.query.order_by(Category.name).all()]

class CommentForm(FlaskForm):
    content = TextAreaField('', validators=[DataRequired(message='评论不能为空')])
    submit = SubmitField('发布评论')


class CKTextAreaWidget(widgets.TextArea):
    """CKeditor form for Flask-Admin."""

    def __call__(self, field, **kwargs):

        # 为ckeditor 增加新的class
        kwargs.setdefault('class_', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(TextAreaField):
    """创建一个新字段"""

    # Add a new widget `CKTextAreaField` inherit from TextAreaField.
    widget = CKTextAreaWidget()