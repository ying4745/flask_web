import os

from flask_login import login_required, current_user
from flask import render_template, request, current_app, flash, redirect, url_for, jsonify

from . import main
from .. import avatar
from flask_blog import User, Article, Comment, db
from .forms import UserForm, EditProfiledAdminForm, CommentForm
from flask_blog.models import Role, Permission, Follow, UserFavorite
from flask_blog.utils.decorators import admin_required, permission_required
from flask_blog.utils.select_sql import get_article_pagination, get_hot_click_articles

# 个人修改资料
@main.route('/user/modify/<username>', methods=['GET', 'POST'])
@login_required
def edit_profile(username):
    form = UserForm()
    if form.validate_on_submit():
        # 如果上传了头像，则修改
        if form.avatar.data:
            filename = avatar.save(form.avatar.data)
            try:
                # 删除原来的头像
                os.remove(os.path.join(current_app.config['UPLOADED_AVATAR_DEST'],
                                       current_user.avatar_img))
            except Exception:
                pass
            current_user.avatar_img = filename

        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)

        flash('你的资料已更新')
        return redirect(url_for('.user', username=current_user.username))

    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    user_avatar = current_user.avatar_url

    return render_template('main/edit_profile.html', form=form, user_avatar=user_avatar)


# 管理员修改个人资料
@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
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


# 个人主页
@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)

    pagination, articles = get_article_pagination(user.articles, page)

    views_articles, com_articles = get_hot_click_articles(user.articles)

    tags = []
    for art in user.articles:
        for tag in art.tags.all():
            if tag not in tags:
                tags.append(tag)

    return render_template('main/user.html', user=user, articles=articles,
                           views_articles=views_articles, tags=tags,
                           com_articles=com_articles, endpoint='main.user',
                           pagination=pagination)


# 提交评论
@main.route('/article/comment', methods=['POST'])
def sub_comment():
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


# 评论子评论
@main.route('/article/add/comment', methods=['POST'])
def add_comment():
    article_id = request.form.get('article_id', None)
    parent_id = request.form.get('com_id', None)
    content = request.form.get('com_content', None)

    if not current_user.is_authenticated:
        return jsonify(errno='3',errmsg='用户未登陆')

    if not parent_id:
        return jsonify(errno='4',errmsg='评论出错')

    if not content:
        return jsonify(errno='5', errmsg='评论不能为空！')

    article = Article.query.get_or_404(article_id)

    comment = Comment(content=content,
                      article=article,
                      author=current_user._get_current_object(),
                      parent_id=parent_id)
    db.session.add(comment)

    return jsonify(errno='0', errmsg='ok')


# 加载评论
@main.route('/article/<int:article_id>/comments')
def comments(article_id):
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

    # return jsonify(errno='0', errmsg='ok', data=comments)
    return render_template('main/article_comment.html', comments=comments)


# 点赞
@main.route('/add/favorite', methods=['POST'])
def addfavorite():
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
        else:
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
            else:
                article = Article.query.get_or_404(int(fav_id))
                article.up_num += 1
                data = article.up_num
            return jsonify(errno='0', errmsg='点赞', data=data)
        else:
            return jsonify(errno='4', errmsg='数据错误')


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


@main.route('/moderate/<username>')  # 加载用户评论列表
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


# 加载管理评论页面 暂时还没用上
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
