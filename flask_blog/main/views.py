import flask_whooshalchemyplus
from flask_login import login_required, current_user
from flask import render_template, flash, url_for, redirect, request, abort, \
    make_response

from . import main
from flask_blog import db
from .forms import ArticleForm, CommentForm
from flask_blog.utils.decorators import permission_required, confirmed
from ..models import User, Permission, Article, Tag, Category, UserFavorite
from flask_blog.utils.select_sql import get_article_pagination, get_hot_click_articles, \
    get_all_tags


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

    pagination, articles = get_article_pagination(query, page)

    views_articles, com_articles = get_hot_click_articles(query)

    tags = get_all_tags()

    return render_template('main/index.html', articles=articles, views_articles=views_articles,
                           com_articles=com_articles, pagination=pagination, tags=tags,
                           show_followed=show_followed, endpoint='main.index')


@main.route('/tag/<name>', methods=['GET', 'POST'])
def tag(name):  # 标签文章列表
    tag = Tag.query.filter_by(name=name).first_or_404()
    page = request.args.get('page', 1, type=int)

    pagination, articles = get_article_pagination(tag.articles, page)

    views_articles, com_articles = get_hot_click_articles(tag.articles)

    tags = get_all_tags()

    return render_template('main/tag.html', tag=tag, pagination=pagination,
                           views_articles=views_articles, com_articles=com_articles,
                           articles=articles, endpoint='main.tag', tags=tags)


@main.route('/category/<name>', methods=['GET', 'POST'])
def category(name):  # 分类文章列表
    category = Category.query.filter_by(name=name).first_or_404()
    page = request.args.get('page', 1, type=int)

    pagination, articles = get_article_pagination(category.articles, page)

    views_articles, com_articles = get_hot_click_articles(category.articles)

    tags = get_all_tags()

    return render_template('main/category.html', category=category, pagination=pagination,
                           views_articles=views_articles, com_articles=com_articles, tags=tags,
                           articles=articles, endpoint='main.category')


@main.route('/search', methods=['POST'])
def search():
    if not request.form['search']:
        return redirect(url_for('.index'))
    return redirect(url_for('.search_results', query_con=request.form['search']))


@main.route('/search_results/<query_con>')
def search_results(query_con):
    results = Article.query.whoosh_search(query_con)
    page = request.args.get('page', 1, type=int)

    pagination, articles = get_article_pagination(results, page)

    views_articles, com_articles = get_hot_click_articles(Article.query)

    tags = get_all_tags()

    return render_template('main/search_results.html', query_con=query_con, articles=articles,
                           pagination=pagination, endpoint='main.search_results',
                           views_articles=views_articles, com_articles=com_articles, tags=tags, )


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


@main.route('/publish', methods=['GET', 'POST'])  # 发布文章
@login_required
@confirmed  # 过滤没确认的账户
@permission_required(Permission.WRITE_ARTICLES)
def publish():
    form = ArticleForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        article = Article(title=form.title.data,
                          content=form.content.data,
                          category=Category.query.get(form.category.data),
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


@main.route('/article/<int:id>', methods=['GET', 'POST'])
def article(id):  # 单独显示文章
    article = Article.query.get_or_404(id)
    article.increase_views()
    form = CommentForm()

    is_a_fav = False
    try:
        user_id = current_user._get_current_object().id
    except:
        user_id = None
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

    # TODO 多级评论 数据处理

    u_id = article.author_id
    # 查询该用户的所有文章
    query = db.session.query(Article).join(User).filter(User.id == u_id)

    views_articles, com_articles = get_hot_click_articles(query)

    # 该用户所有文章的标签
    user_articles = query.all()
    tags = []
    for art in user_articles:
        for tag in art.tags.all():
            if tag not in tags:
                tags.append(tag)

    return render_template('main/article.html', article=article, form=form,
                           views_articles=views_articles, tags=tags,
                           com_articles=com_articles, is_a_fav=is_a_fav)


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
