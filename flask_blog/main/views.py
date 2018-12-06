from flask import render_template, flash, url_for, redirect, request, abort, \
    make_response, current_app, jsonify
from . import main
from .forms import EditProfiledAdminForm, ArticleForm, CommentForm, UserForm
from flask_login import login_required, current_user
from ..decorators import admin_required
from ..models import User, Role, Permission, Article, Comment, Follow, Tag, \
    Category, UserFavorite
from flask_blog import db
from ..decorators import permission_required
from sqlalchemy import func
from functools import wraps
import flask_whooshalchemyplus

# 检查用户邮箱是否确认的装饰器
def confirmed(f):
    @wraps(f)
    def decorator_function(*args, **kwargs):
        if not current_user.confirmed:
            return redirect(url_for('auth.unconfirmed'))
        return f(*args, **kwargs)
    return decorator_function


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
    tags = Tag.query.all()
    return render_template('main/index.html', articles=articles, views_articles=views_articles,
                          com_articles=com_articles, pagination=pagination, tags=tags,
                           show_followed=show_followed, endpoint='main.index')


@main.route('/tag/<name>', methods=['GET', 'POST'])
def tag(name):  # 标签文章列表
    tag = Tag.query.filter_by(name=name).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = tag.articles.order_by(Article.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_ARTICLES_PER_PAGE'],
        error_out=False)
    articles = pagination.items
    views_articles = tag.articles.order_by(Article.views.desc()).limit(10).all()
    acc = tag.articles.subquery()
    com_articles = db.session.query(acc,func.count(Comment.id).label('num')).join(Comment)\
        .group_by(Comment.article_id).order_by(func.count(Comment.id).desc()).limit(10).all()
    tags = Tag.query.all()
    return render_template('main/tag.html', tag=tag, pagination=pagination,
                           views_articles=views_articles, com_articles=com_articles,
                           articles=articles, endpoint='main.tag', tags=tags)


@main.route('/category/<name>', methods=['GET', 'POST'])
def category(name):  # 分类文章列表
    category = Category.query.filter_by(name=name).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = category.articles.order_by(Article.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_ARTICLES_PER_PAGE'],
        error_out=False)
    articles = pagination.items
    views_articles = category.articles.order_by(Article.views.desc()).limit(10).all()
    acc = category.articles.subquery()
    com_articles = db.session.query(acc,func.count(Comment.id).label('num')).join(Comment)\
        .group_by(Comment.article_id).order_by(func.count(Comment.id).desc()).limit(10).all()
    categorys = Category.query.all()
    tags = Tag.query.all()
    return render_template('main/category.html', category=category, pagination=pagination,
                           views_articles=views_articles, com_articles=com_articles,tags=tags,
                           articles=articles, endpoint='main.category', categorys=categorys)


@main.route('/search', methods= [ 'POST'])
def search():
    if not request.form['search']:
        return redirect(url_for('.index'))
    return redirect(url_for('.search_results', query_con = request.form['search']))


@main.route('/search_results/<query_con>')
def search_results(query_con):
    results = Article.query.whoosh_search(query_con)
    page = request.args.get('page', 1, type=int)
    pagination = results.order_by(Article.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_ARTICLES_PER_PAGE'],
        error_out=False)
    articles = pagination.items
    views_articles = Article.query.order_by(Article.views.desc()).limit(10).all()
    com_articles = db.session.query(Article.id, Article.title, func.count(Comment.id).label('num')).join(Comment) \
        .group_by(Comment.article_id).order_by(func.count(Comment.id).desc()).limit(10).all()
    tags = Tag.query.all()
    return render_template('main/search_results.html', query_con =query_con, articles=articles,
                           pagination=pagination, endpoint='main.search_results',
                           views_articles=views_articles, com_articles=com_articles, tags=tags,)


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
@confirmed
@permission_required(Permission.WRITE_ARTICLES)
def publish():
    form = ArticleForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        article = Article(title=form.title.data, content=form.content.data,
                          category = Category.query.get(form.category.data),
                          author=current_user._get_current_object())
        for tag in form.tags.data:
            article.tags.append(tag)
        db.session.add(article)
        db.session.commit()
        flask_whooshalchemyplus.index_one_model(Article)
        flash('你的文章已经发布了')
        return redirect(url_for('.article', id=article.id))
    return render_template('main/edit_article.html', form=form)


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
        article.category = Category.query.get(form.category.data)
        for tag in article.tags.all():
            article.tags.remove(tag)
        for tag in form.tags.data:
            article.tags.append(tag)
        db.session.add(article)
        flash('文章已经更新！')
        return redirect(url_for('.article', id=article.id))
    form.title.data = article.title
    form.category.data = article.categorys_id
    form.content.data = article.content
    # 用QuerySelectMultipleField的话这里直接赋值给form.tags.data就可以了，用SelectMultipleField就不行了
    form.tags.data = article.tags.all()
    return render_template('main/edit_article.html', form=form)


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
    return render_template('main/edit_profile.html', form=form)


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
    return render_template('main/edit_profile.html', form=form)


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
    user_articles = db.session.query(Article).join(User).filter(User.username == username).all()
    tags = []
    for art in user_articles:
        for tag in art.tags.all():
            if tag not in tags:
                tags.append(tag)
    return render_template('main/user.html', user=user, articles=articles,
                           views_articles=views_articles, tags=tags,
                           com_articles=com_articles, endpoint='main.user',
                           pagination=pagination)


@main.route('/article/<int:id>', methods=['GET', 'POST'])
def article(id):  # 单独显示文章
    article = Article.query.get_or_404(id)
    article.increase_views()
    form = CommentForm()

    is_a_fav = False
    try:
        user_id = current_user._get_current_object().id
    except:
        pass
    if user_id:
        is_fav = UserFavorite.query.filter_by(user_id=user_id,
                                              fav_id=article.id,
                                              fav_type='article').first()
        if is_fav:
            is_a_fav = True

    # page = request.args.get('page', 1, type=int)
    # if page == -1:
    #     # 计算最后一页，-1是减去刚发的评论，如果总评论是39，每页20，如果不减40/20+1=3
    #     # 而实际上是第二页的最后一条
    #     page = (article.comments.count() - 1) // \
    #         current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    # pagination = article.comments.order_by(Comment.timestamp.asc()).paginate(
    #     page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
    #     error_out=False)

    # 多级评论  数据处理

    u_id = article.author_id
    views_articles = db.session.query(Article).join(User).filter(User.id==u_id)\
        .order_by(Article.views.desc()).limit(10).all()
    acc = db.session.query(Article).join(User).filter(User.id == u_id).subquery()
    com_articles = db.session.query(acc, func.count(Comment.id).label('num')).join(Comment) \
        .group_by(Comment.article_id).order_by(func.count(Comment.id).desc()).limit(10).all()
    user_articles = db.session.query(Article).join(User).filter(User.id==u_id).all()
    tags = []
    for art in user_articles:
        for tag in art.tags.all():
            if tag not in tags:
                tags.append(tag)
    return render_template('main/article.html', articles=[article], form=form,
                           views_articles=views_articles, tags=tags,
                           com_articles=com_articles, is_a_fav=is_a_fav)


@main.route('/article/comment', methods=['POST'])
def sub_comment():  # 提交评论
    article_id = request.form.get('article_id', None)
    if not current_user.is_authenticated:
        return jsonify(errno='3',errmsg='请先登陆')
    article = Article.query.get_or_404(article_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.content.data,
                          article=article,
                          author=current_user._get_current_object())
        db.session.add(comment)
        return jsonify(errno='0', errmsg='ok')
    return jsonify(errno='4', errmsg='评论失败')


@main.route('/article/add/comment', methods=['POST'])
def add_comment():  # 评论子评论
    article_id = request.form.get('article_id', None)
    parent_id = request.form.get('com_id', None)
    if not current_user.is_authenticated:
        return jsonify(errno='3',errmsg='用户未登陆')
    if not parent_id:
        return jsonify(errno='4',errmsg='评论出错')
    content = request.form.get('com_content', None)
    if not content:
        return jsonify(errno='5', errmsg='评论不能为空！')
    article = Article.query.get_or_404(article_id)

    comment = Comment(content=content,
                      article=article,
                      author=current_user._get_current_object(),
                      parent_id=parent_id)
    db.session.add(comment)
    return jsonify(errno='0', errmsg='ok')


@main.route('/article/<int:article_id>/comments')
def comments(article_id):  # 加载评论
    article = Article.query.get_or_404(article_id)
    comment_lists = article.comments.order_by(Comment.id.asc()).all()
    if not comment_lists:
        return jsonify(errno='5', errmsg='无数据')
    com_lists = []
    for a in comment_lists:
        com_lists.append(a.to_dict())

    # 获取登陆用户的ID，如果没有就为None
    if current_user.is_authenticated:
        user_id = current_user._get_current_object().id
    else:
        user_id = None

    # 为评论增加属性，表示该用户对该评论的点赞行为
    for com in com_lists:
        if user_id:
            is_fav = UserFavorite.query.filter_by(user_id=user_id,
                                                  fav_id=com['id'],
                                                  fav_type='comment').first()
            if is_fav:
                com['isFav'] = 'icon-dianzan'
            else:
                com['isFav'] = 'icon-dianzan1'
        else:
            com['isFav'] = 'icon-dianzan1'


    comments = []
    from collections import OrderedDict  # 有序字典 按字典的插入顺序排列
    comment_dict = OrderedDict()
    for comment in com_lists:
        comment_dict[comment['id']] = comment

    for item in com_lists:
        parent_comment = comment_dict.get(item['parent_id'])
        if parent_comment:
            parent_comment['children'].append(item)  # 列表中添加子级评论
        else:
            comments.append(item)

    return jsonify(errno='0', errmsg='ok', data=comments)


@main.route('/add/favorite', methods=['POST'])
def addfavorite():  # 点赞
    fav_id = request.form.get('fav_id')
    fav_type = request.form.get('fav_type')
    if not current_user.is_authenticated:
        return jsonify(errno='3',errmsg='用户未登陆')
    user_id = current_user._get_current_object().id
    is_fav = UserFavorite.query.filter_by(user_id=user_id,
                                          fav_id=int(fav_id),
                                          fav_type=fav_type).first()
    if is_fav:
        #  用户记录存在，表示取消点赞
        db.session.delete(is_fav)
        if fav_type == 'comment':
            comment = Comment.query.get_or_404(int(fav_id))
            comment.up_num -= 1
            if comment.up_num < 0:
                comment.up_num = 0
            data = comment.up_num
        elif fav_type == 'article':
            article = Article.query.get_or_404(int(fav_id))
            article.up_num -= 1
            if article.up_num < 0:
                article.up_num = 0
            data = article.up_num
        return jsonify(errno='0', errmsg='取消点赞', data=data)
    else:
        if int(fav_id) > 0:
            userfavorite = UserFavorite(user_id=user_id,
                                        fav_id=int(fav_id),
                                        fav_type=fav_type)
            db.session.add(userfavorite)
            if fav_type == 'comment':
                comment = Comment.query.get_or_404(int(fav_id))
                comment.up_num += 1
                data = comment.up_num
            elif fav_type == 'article':
                article = Article.query.get_or_404(int(fav_id))
                article.up_num += 1
                data = article.up_num
            return jsonify(errno='0', errmsg='点赞', data=data)
        else:
            return jsonify(errno='4', errmsg='数据错误')


# @main.route('/edit_about', methods=['GET', 'POST'])   # 编辑自我介绍
# @login_required
# @confirmed
# @permission_required(Permission.WRITE_ARTICLES)
# def edit_about():
#     article = Article.query.get_or_404(106)
#     form = ArticleForm()
#     if current_user.can(Permission.WRITE_ARTICLES) and \
#             form.validate_on_submit():
#         article.title = form.title.data
#         article.content = form.content.data
#         for tag in article.tags.all():
#             article.tags.remove(tag)
#         for tag in form.tags.data:
#             article.tags.append(tag)
#         db.session.add(article)
#         flash('文章已经更新！')
#         return redirect(url_for('.about'))
#     form.title.data = article.title
#     form.content.data = article.content
#     return render_template('main/edit_article.html', form=form)


# @main.route('/about', methods=['GET', 'POST'])
# def about():  # 关于我
#     article = Article.query.get_or_404(106)
#     form = CommentForm()
#     if form.validate_on_submit():
#         comment = Comment(content=form.content.data,
#                           article=article,
#                           author=current_user._get_current_object())
#         db.session.add(comment)
#         flash('你的评论已经发表了')
#         return redirect(url_for('.about', page=-1))
#     page = request.args.get('page', 1, type=int)
#     if page == -1:
#         page = (article.comments.count() - 1) // \
#             current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
#     pagination = article.comments.order_by(Comment.timestamp.asc()).paginate(
#         page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
#         error_out=False)
#     comments = pagination.items
#     return render_template('main/about_me.html', comments=comments, form=form,
#                            pagination=pagination, article=article)


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
    return render_template('main/followers.html', user=user,
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
    return render_template('main/followers.html', user=user,
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
    return render_template('main/private_comment.html', comments=comments, user=user,
                           pagination=pagination, page=page, endpoint='main.comment')


@main.route('/moderate')  # 加载管理评论页面 暂时还没用上
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
