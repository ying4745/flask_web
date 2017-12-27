from flask import render_template, flash, url_for, redirect, session, abort
from . import main
from .forms import EditProfiledAdminForm, ArticleForm
from flask_login import login_required, current_user
from ..decorators import admin_required
from ..models import User, Role, Permission, Article
from flask_blog import db


@main.route('/', methods=['GET', 'POST'])
def index():
    form = ArticleForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        article = Article(title=form.title.data, content=form.content.data,
                          author=current_user._get_current_object())
        db.session.add(article)
        return redirect(url_for('.index'))
    articles = Article.query.order_by(Article.timestamp.desc()).all()
    return render_template('index.html', form=form, articles=articles)


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
        return redirect(url_for('auth.show_user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('main/edit_profile.html', form=form)
