"""empty message

Revision ID: e8434ed68342
Revises: 16edaa6b893f
Create Date: 2017-12-25 17:12:42.632477

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'e8434ed68342'
down_revision = '16edaa6b893f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('articles', sa.Column('author_id', sa.Integer(), nullable=True))
    op.add_column('articles', sa.Column('timestamp', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_articles_timestamp'), 'articles', ['timestamp'], unique=False)
    op.drop_constraint('articles_ibfk_1', 'articles', type_='foreignkey')
    op.create_foreign_key(None, 'articles', 'users', ['author_id'], ['id'])
    op.drop_column('articles', 'user_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('articles', sa.Column('user_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'articles', type_='foreignkey')
    op.create_foreign_key('articles_ibfk_1', 'articles', 'users', ['user_id'], ['id'])
    op.drop_index(op.f('ix_articles_timestamp'), table_name='articles')
    op.drop_column('articles', 'timestamp')
    op.drop_column('articles', 'author_id')
    # ### end Alembic commands ###
