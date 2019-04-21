from sqlalchemy import func
from flask import current_app

from flask_blog import Tag, Article, Comment, db


# 获取所有标签
def get_all_tags():
    return Tag.query.all()


# 文章分页
def get_article_pagination(query, page):
    pagination = query.order_by(Article.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_ARTICLES_PER_PAGE'],
        error_out=False)
    return pagination, pagination.items


# 查询热评和点击榜
def get_hot_click_articles(query_obj):
    views_articles = query_obj.order_by(Article.views.desc()).limit(10).all()
    # 子查询
    acc = query_obj.subquery()
    # 文章的评论按文章分组，统计文章评论数，排序
    com_articles = db.session.query(acc, func.count(Comment.id).label('num')).join(Comment) \
        .group_by(Comment.article_id).order_by(func.count(Comment.id).desc()).limit(10).all()
    return views_articles, com_articles
