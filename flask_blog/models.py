from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app, request
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import login_manager
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from markdown import markdown
import bleach
import hashlib

db = SQLAlchemy()


class Permission:  # 权限
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')  # lazy='dynamic'禁止自动执行查询

    @staticmethod  # 静态方法，允许程序在不创建实例的情况下就可以使用
    def insert_roles():  # 函数没self参数
        roles = {
            '用户': (Permission.FOLLOW |
                   Permission.COMMENT |
                   Permission.WRITE_ARTICLES, True),
            '协管员': (Permission.FOLLOW |
                    Permission.COMMENT |
                    Permission.WRITE_ARTICLES |
                    Permission.MODERATE_COMMENTS, False),
            '管理员': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    avatar_hash = db.Column(db.String(32))
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    confirmed = db.Column(db.Boolean, default=False)  # 账户状态确认
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    articles = db.relationship('Article', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    @staticmethod  # 生成虚拟用户
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()  # seed()方法改变随机数生成器的种子
        # Seed就是random开始计算的第一个值。所以只要seed一样，那么“随机”结果和顺序也都完全一致
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence())
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                # 在生成虚拟用户时候，可能会发生email重复的情况，所以这个情况就需要回滚

    @staticmethod  # 更新数据库中用户自己关注自己
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        self.followed.append(Follow(followed=self))

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    @property  # 把方法变成属性调用
    def password(self):  # 读取会报错
        raise AttributeError('密码不可读取')

    @password.setter  # 写入密码的散列值
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):  # 检查用户输入的密码，对就返回True
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        # 生成一个令牌，有效期默认为一小时
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)  # 检验令牌
        except:
            return False
        if data.get('confirm') != self.id:  # 检查令牌中ID与当前登录用户是否匹配
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):  # 重置密码时生成令牌
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):  # 验证通过就重设密码
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    # def generate_email_change_token(self, new_email, expiration=3600):  # 更换邮箱时生成令牌
    #     s = Serializer(current_app.config['SECRET_KEY'], expiration)
    #     return s.dumps({'change_email': self.id, 'new_email': new_email})
    #
    # def change_email(self, token):
    #     s = Serializer(current_app.config['SECRET_KEY'])
    #     try:
    #         data = s.loads(token)  # 检验令牌
    #     except:
    #         return False
    #     if data.get('change_email') != self.id:   # 检查用户身份
    #         return False
    #     new_email = data.get('new_email')
    #     if new_email is None:
    #         return False
    #     if self.query.filter_by(email=new_email).first() is not None:  # 邮箱与原来相同
    #         return False
    #     self.email = new_email
    #     self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
    #     # 通过hashlib的md5函数，将email生成摘要信息
    #     db.session.add(self)
    #     return True

    def can(self, permissions):  # 检查角色是否具有请求所需的权限
        return self.role is not None and (self.role.permissions &
                                          permissions) == permissions

    def is_administrator(self):  # 检查管理员权限经常用，所以单独定制方法
        return self.can(Permission.ADMINISTER)

    def gravatar(self, size=100, default='identicon', rating='g'):  # 生成 Gravatar头像 URL
        if request.is_secure:  # 判断request是否为https
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return "{url}/{hash}?s={size}&d={default}&r={rating}" \
            .format(url=url, hash=hash, size=size, default=default, rating=rating)

    def follow(self, user):  # 关注
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):  # 取消关注
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):  # 检查是否关注了他
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):  # 检查是否关注了自己
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_articles(self):  # 查询关注者的文章
        return Article.query.join(Follow, Follow.followed_id == Article.author_id) \
            .filter(Follow.follower_id == self.id)

    def __repr__(self):
        return '<User %r>' % self.username


@login_manager.user_loader  # 回调函数，使用指定的标识符加载用户
def load_user(user_id):  # 能找到该用户，返回用户对象，否则返回None
    return User.query.get(int(user_id))


class AnonymousUser(AnonymousUserMixin):  # 出于一致性考虑，未登录时实现两种方法
    def can(self, permissions):  # 这样程序可以不检查是否登录，就可以检查权限
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


# 设置未登录状态的current_user为AnonymousUser类


class Category(db.Model):
    __tablename__ = 'categorys'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, index=True, nullable=False)
    articles = db.relationship('Article', backref='category', lazy='dynamic')

    def __repr__(self):
        return '<Category %r>' % self.name


article_tag_table = db.Table('article_tag_table',
                             db.Column('article_id', db.Integer, db.ForeignKey('articles.id')),
                             db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')))


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, index=True,
                     nullable=False)

    @staticmethod
    def generate_fake(count=30):
        from random import seed

        import forgery_py
        from sqlalchemy.exc import IntegrityError

        seed()
        for i in range(count):
            t = Tag(name=forgery_py.lorem_ipsum.word())
            db.session.add(t)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return '<Tag %r>' % self.name


class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), unique=True)
    content = db.Column(db.Text)
    content_html = db.Column(db.Text)
    summary = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    views = db.Column(db.Integer, default=int(0))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    categorys_id = db.Column(db.Integer, db.ForeignKey('categorys.id'))
    comments = db.relationship('Comment', backref='article', lazy='dynamic')
    tags = db.relationship('Tag',
                           secondary=article_tag_table,
                           backref=db.backref('articles', lazy='dynamic'),
                           lazy='dynamic')

    @staticmethod  # 生成虚拟数据
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        tag_count = Tag.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            a = Article(title=forgery_py.lorem_ipsum.title(randint(1, 10)),
                        content=forgery_py.lorem_ipsum.paragraphs(randint(10, 20)),
                        timestamp=forgery_py.date.datetime(True),
                        author=u)
            allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                            'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                            'h1', 'h2', 'h3', 'p']
            lines = a.content.split('\n')
            temp = '\n'.join(lines[:8])
            a.summary = bleach.linkify(bleach.clean(
                markdown(temp, output_format='html'),
                tags=allowed_tags, strip=True))
            tag_num = randint(1, 5)
            for j in range(tag_num):
                t = Tag.query.offset(randint(0, tag_count - 1)).first()
                a.tags.append(t)
            db.session.add(a)
            db.session.commit()

    def increase_views(self):
        self.views += 1

    @staticmethod  # 此装饰器表示此方法以类名调用
    def on_changed_content(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'table', 'tr', 'td', 'tbody',
                        'h1', 'h2', 'h3', 'p', 'img']
        attrs = {
            '*': ['class', 'style'],
            'a': ['href', 'rel'],
            'img': ['alt', 'src'],
        }
        styles = ['height', 'width']
        target.content_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, attributes=attrs, styles=styles, strip=True))
        lines = value.split('\n')
        temp = '\n'.join(lines[:5])
        target.summary = bleach.linkify(bleach.clean(
            markdown(temp, output_format='html'),
            tags=allowed_tags, attributes=attrs, styles=styles, strip=True))

    def __repr__(self):
        return '<Article %r>' % self.title


# on_changed_body 函数注册在 content 字段上，是 SQLAlchemy“set”事件的监听程序，这意
# 味着只要这个类实例的 content 字段设了新值，函数就会自动被调用
db.event.listen(Article.content, 'set', Article.on_changed_content)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    content_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)  # 布尔值 查禁不当的评论
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))

    @staticmethod
    def on_changed_content(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'p', 'li', 'ol', 'ul', 'strong']
        target.content_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'), tags=allowed_tags, strip=True))


db.event.listen(Comment.content, 'set', Comment.on_changed_content)
