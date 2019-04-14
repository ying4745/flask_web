from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.fileadmin import FileAdmin
from ..main.forms import CKTextAreaField
from wtforms import PasswordField
from wtforms.validators import DataRequired, Length, Email, Regexp
from flask import url_for, redirect
from flask_login import current_user


class CustomView(BaseView):

    @expose('/')
    def index(self):
        return redirect(url_for('main.index'))


class UserView(ModelView):

    def is_accessible(self):
        return current_user.is_administrator()

    column_labels = {
        'email': '电子邮箱',
        'username': '用户名',
        'password': '密码',
        'name': '昵称',
        'location': '地址',
        'about_me': '简介',
        'confirmed': '确认状态',
        'member_since': '注册时间',
        'last_seen': '最后一次登录',
        'role': '角色'
    }
    # 使用搜索框
    column_searchable_list = ('username', 'name')
    # 隐藏字段不显示
    column_exclude_list = ['avatar_hash', 'password_hash']
    #  表单显示字段列集合
    form_columns = ('email', 'username', 'password', 'name',
                    'location', 'about_me', 'confirmed', 'role',)
    # 添加密码字段
    form_extra_fields = {
        'password': PasswordField('密码', validators=[DataRequired(message='密码不能为空')])
    }
    #  表单字段参数字典
    form_args = dict(
        email=dict(validators=[DataRequired(message='邮箱不能为空'), Length(1, 64),
                               Email(message='请输入有效的邮箱地址')]),
        username=dict(validators=[DataRequired(message='用户名不能为空'), Length(1, 64),
                                  Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                         '用户名只能由字母，数字，点，和下划线组成')]),
        role=dict(validators=[DataRequired()])
    )
    list_template = 'admin/list_blog.html'


class ArticleView(ModelView):

    def is_accessible(self):
        return current_user.is_administrator()

    # 使用CKTextAreaField替换 字段名为content的值
    form_overrides = dict(content=CKTextAreaField)
    # 使用搜索框
    column_searchable_list = ('content', 'title')
    # 增加过滤器
    column_filters = ('timestamp',)

    create_template = 'admin/article_edit.html'
    edit_template = 'admin/article_edit.html'
    list_template = 'admin/list_blog.html'

    column_labels = {
        'id': '编号',
        'title': '文章标题',
        'timestamp': '发布时间',
        'author': '作者',
        'category': '分类',
        'views': '浏览量'
    }
    column_list = ('id', 'title', 'timestamp', 'views', 'author', 'category')
    #  从创建和编辑表单中删除字段
    form_excluded_columns = ['comments', 'summary', 'content_html']
    #  表单控件渲染参数字典。使用它可以自定义如何在不使用自定义模板的情况下渲染小部件
    form_widget_args = {
        'tags': {
            'style': 'width: 100%'
        },
        'title': {
            'style': 'width: 100%; box-sizing: border-box; height: 30px'
        },
    }


class CommentView(ModelView):

    def is_accessible(self):
        return current_user.is_administrator()

    can_create = False
    edit_modal = True
    column_labels = {
        'content': '评论内容',
        'timestamp': '评论时间',
        'disabled': '是否屏蔽',
        'author': '评论者',
        'up_num': '点赞数',
        'article': '评论文章'
    }
    # 隐藏字段不显示
    column_exclude_list = ['content_html']
    list_template = 'admin/list_blog.html'
    form_excluded_columns = ['content_html']


class TagView(ModelView):
    def is_accessible(self):
        return current_user.is_administrator()

    create_modal = True
    edit_modal = True
    form_excluded_columns = ['articles']


class CategoryView(ModelView):
    def is_accessible(self):
        return current_user.is_administrator()

    create_modal = True
    edit_modal = True
    form_excluded_columns = ['articles']


class StaticFileAdmin(FileAdmin):
    can_delete_dirs = True