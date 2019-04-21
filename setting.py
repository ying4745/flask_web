import os

FLASKY_MAIL_SUBJECT_PREFIX = '[左岸博客]'  # 邮件主题前缀
FLASKY_MAIL_SENDER = '左岸博客 <yanwei4682@qq.com>'  # 发件人邮箱

# 文章分页
FLASKY_ARTICLES_PER_PAGE = 5

# 关注列表分页
FLASKY_FOLLOWERS_PER_PAGE = 5

# 评论分页
FLASKY_COMMENTS_PER_PAGE = 5

# 头像上传配置
UPLOADED_AVATAR_DEST = os.path.join(os.path.dirname(__file__), 'flask_blog/static/avatar_img')