from flask import render_template, flash, url_for, redirect, request, abort, \
    make_response, current_app
from . import main
from .forms import EditProfiledAdminForm, ArticleForm, CommentForm, UserForm
from flask_login import login_required, current_user
from ..decorators import admin_required
from ..models import User, Role, Permission, Article, Comment, Follow
from flask_blog import db
from ..decorators import permission_required
from sqlalchemy import func


@main.route('/')
def index():  # 主页
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
    views_articles = Article.query.order_by(Article.views.desc()).limit(10).all()
    com_articles = db.session.query(Article.id,Article.title,func.count(Comment.id).label('num')).join(Comment)\
        .group_by(Comment.article_id).order_by(func.count(Comment.id).desc()).limit(10).all()
    return render_template('index.html', articles=articles, views_articles=views_articles,
                          com_articles=com_articles, pagination=pagination, show_followed=show_followed)


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


@main.route('/publish', methods=['GET', 'POST'])   # 发布文章
@login_required
@permission_required(Permission.WRITE_ARTICLES)
def publish():
    form = ArticleForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        article = Article(title=form.title.data, content=form.content.data,
                          author=current_user._get_current_object())
        db.session.add(article)
        db.session.commit()
        flash('你的文章已经发布了')
        return redirect(url_for('.article', id=article.id))
    return render_template('edit_article.html', form=form)

@main.route('/user/modify/<username>', methods=['GET', 'POST'])
@login_required
def edit_profile(username):
    form = UserForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('你的资料已更新')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


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
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.articles.order_by(Article.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_ARTICLES_PER_PAGE'],
        error_out=False)
    articles = pagination.items
    views_articles = user.articles.order_by(Article.views.desc()).limit(10).all()
    acc = db.session.query(Article).join(User).filter(User.username==username).subquery()
    com_articles = db.session.query(acc,func.count(Comment.id).label('num')).join(Comment)\
        .group_by(Comment.article_id).order_by(func.count(Comment.id).desc()).limit(10).all()
    return render_template('user.html', user=user, articles=articles, views_articles=views_articles,
                           com_articles=com_articles, endpoint='main.user',pagination=pagination)


@main.route('/article/<int:id>', methods=['GET', 'POST'])
def article(id):  # 单独显示文章
    article = Article.query.get_or_404(id)
    article.increase_views()
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
    u_id = article.author_id
    views_articles = db.session.query(Article).join(User).filter(User.id==u_id)\
        .order_by(Article.views.desc()).limit(10).all()
    acc = db.session.query(Article).join(User).filter(User.id == u_id).subquery()
    com_articles = db.session.query(acc, func.count(Comment.id).label('num')).join(Comment) \
        .group_by(Comment.article_id).order_by(func.count(Comment.id).desc()).limit(10).all()
    return render_template('article.html', articles=[article], form=form, views_articles=views_articles,
                           com_articles=com_articles, comments=comments, pagination=pagination)


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


@main.route('/follow/<username>')  # 关注
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('.user', username=username))
    if current_user.is_following(user):
        flash('你已经关注了这个人')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('你关注了%s' % username)
    return "取消关注"


@main.route('/unfollow/<username>')  # 取消关注
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('.user', username=username))
    if not current_user.is_following(user):
        flash('你没有关注这个人')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('你取消了对%s的关注' % username)
    return "关注"


@main.route('/followers/<username>')  # 被关注列表
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('.user', username=username))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.order_by(Follow.timestamp.desc()).paginate(page,
                                         per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
                                         error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user,
                           endpoint='main.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')  # 关注列表
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('.user', username=username))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.order_by(Follow.timestamp.desc()).paginate(page,
                                        per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
                                        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user,
                           endpoint='main.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/moderate/<username>')  # 加载评论列表
def comment(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('.user', username=username))
    page = request.args.get('page', 1, type=int)
    pagination = user.comments.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('private_comment.html', comments=comments, user=user,
                           pagination=pagination, page=page, endpoint='main.comment')


@main.route('/moderate')  # 加载管理评论页面
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


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return "解禁"


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return "屏蔽"
