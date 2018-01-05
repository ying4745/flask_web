from flask import render_template, flash, url_for, redirect, request, abort, \
    make_response, current_app
from . import main
from .forms import EditProfiledAdminForm, ArticleForm, CommentForm
from flask_login import login_required, current_user
from ..decorators import admin_required
from ..models import User, Role, Permission, Article, Comment
from flask_blog import db
from ..decorators import permission_required


@main.route('/', methods=['GET', 'POST'])
def index():  # 主页
    form = ArticleForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        article = Article(title=form.title.data, content=form.content.data,
                          author=current_user._get_current_object())
        db.session.add(article)
        flash('你的文章已经发布了')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_articles
    else:
        query = Article.query
    pagination = query.order_by(Article.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_ARTICLES_PER_PAGE'],
        error_out=False)
    articles = pagination.items
    return render_template('index.html', form=form, articles=articles,
                           pagination=pagination, show_followed=show_followed)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):  # 管理员修改个人资料
    user = User.query.get_or_404(id)
    form = EditProfiledAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('个人资料已经更新')
        return redirect(url_for('auth.show_user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('main/edit_profile.html', form=form)


@main.route('/article/<int:id>', methods=['GET', 'POST'])
def article(id):  # 单独显示文章
    article = Article.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.content.data,
                          article=article,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('你的评论已经发表了')
        return redirect(url_for('.article', id=article.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        # 计算最后一页，-1是减去刚发的评论，如果总评论是39，每页20，如果不减40/20+1=3
        # 而实际上是第二页的最后一条
        page = (article.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = article.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('article.html', articles=[article], form=form,
                           comments=comments, pagination=pagination)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):  # 文章修改
    article = Article.query.get_or_404(id)
    if current_user != article.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = ArticleForm()
    if form.validate_on_submit():
        article.title = form.title.data
        article.content = form.content.data
        db.session.add(article)
        flash('文章已经更新！')
        return redirect(url_for('.article', id=article.id))
    form.title.data = article.title
    form.content.data = article.content
    return render_template('edit_article.html', form=form)


@main.route('/all')  # 显示所有文章
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/followed')  # 显示关注者的文章
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)
